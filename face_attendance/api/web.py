"""Dashboard enseignant (interface web, rendu serveur avec Jinja2)."""

import base64
from datetime import datetime
from pathlib import Path

import cv2

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import config
from . import face_service, models, reporting
from .database import get_db
from ..face.antispoofing import get_detector
from ..face.engine import identify

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
router = APIRouter(tags=["dashboard"], include_in_schema=False)


def _nom(etu) -> str:
    return f"{etu.prenom or ''} {etu.nom}".strip()


def _recognize_and_annotate(data: bytes, enroll_map: dict, db: Session):
    """Reconnaît les visages, dessine les cadres et renvoie (résultats, image b64)."""
    img = face_service.decode_image(data)
    faces_out = []
    if img is None:
        return faces_out, None
    detector = get_detector()  # None si le modèle anti-spoofing est absent
    for f in face_service.get_engine().analyze(img):
        sid, score = identify(f.embedding, enroll_map, config.MATCH_THRESHOLD)
        nom = None
        if sid is not None:
            etu = db.get(models.Etudiant, sid)
            nom = _nom(etu) if etu else None

        is_real, liveness = (None, None)
        if detector is not None:
            is_real, liveness = detector.predict(img, f.bbox)

        x1, y1, x2, y2 = f.bbox
        if is_real is False:
            color = (0, 140, 255)  # orange : visage suspect (photo ?)
        elif sid is not None:
            color = (0, 170, 0)    # vert : reconnu
        else:
            color = (40, 40, 220)  # rouge : inconnu
        label = (nom or "Inconnu") + (" - SUSPECT" if is_real is False else "")
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            img, label, (x1, max(14, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
        )
        faces_out.append(
            {"etudiant_id": sid, "nom": nom, "score": round(float(score), 3),
             "is_real": is_real, "liveness": liveness}
        )
    ok, buf = cv2.imencode(".jpg", img)
    b64 = base64.b64encode(buf.tobytes()).decode() if ok else None
    return faces_out, b64


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    ctx = {
        "request": request,
        "n_etu": db.query(models.Etudiant).count(),
        "n_sea": db.query(models.Seance).count(),
        "n_pre": db.query(models.Presence).count(),
        "seances": db.query(models.Seance).order_by(models.Seance.id.desc()).limit(8).all(),
    }
    return templates.TemplateResponse("index.html", ctx)


@router.get("/ui/students", response_class=HTMLResponse)
def students_page(request: Request, db: Session = Depends(get_db)):
    etus = db.query(models.Etudiant).all()
    counts = {e.id: len(e.empreintes) for e in etus}
    ctx = {
        "request": request,
        "etudiants": etus,
        "counts": counts,
        "classes": db.query(models.Classe).all(),
    }
    return templates.TemplateResponse("students.html", ctx)


@router.post("/ui/students")
def create_student_ui(
    nom: str = Form(...),
    prenom: str = Form(""),
    code: str = Form(""),
    classe_id: str = Form(""),
    db: Session = Depends(get_db),
):
    etu = models.Etudiant(
        nom=nom, prenom=prenom or None, code=code or None,
        classe_id=int(classe_id) if classe_id else None,
    )
    db.add(etu)
    db.commit()
    return RedirectResponse("/ui/students", status_code=303)


@router.get("/ui/students/{sid}/enroll", response_class=HTMLResponse)
def enroll_page(sid: int, request: Request, db: Session = Depends(get_db)):
    etu = db.get(models.Etudiant, sid)
    return templates.TemplateResponse(
        "enroll.html", {"request": request, "etu": etu}
    )


@router.post("/ui/students/{sid}/enroll")
def enroll_ui(
    sid: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    for f in files:
        emb = face_service.main_face_embedding(f.file.read())
        if emb is None:
            continue
        db.add(
            models.EmpreinteReference(
                etudiant_id=sid, vecteur=emb.astype("float32").tobytes(),
                dim=int(emb.shape[0]),
            )
        )
    db.commit()
    return RedirectResponse("/ui/students", status_code=303)


@router.get("/ui/attendance", response_class=HTMLResponse)
def attendance_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "attendance.html",
        {"request": request, "seances": db.query(models.Seance).all()},
    )


@router.post("/ui/attendance/recognize", response_class=HTMLResponse)
def attendance_recognize(
    request: Request,
    seance_id: int = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    enroll_map = face_service.build_enroll_map(db)
    faces, image_b64 = _recognize_and_annotate(photo.file.read(), enroll_map, db)
    seance = db.get(models.Seance, seance_id)
    return templates.TemplateResponse(
        "attendance_result.html",
        {"request": request, "seance": seance, "faces": faces, "image_b64": image_b64},
    )


@router.post("/ui/attendance/confirm")
def attendance_confirm(
    seance_id: int = Form(...),
    present_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
):
    db.query(models.Presence).filter(
        models.Presence.seance_id == seance_id
    ).delete()
    for sid in present_ids:
        db.add(
            models.Presence(
                seance_id=seance_id, etudiant_id=sid, statut="present",
                horodatage=datetime.now(), methode="auto",
            )
        )
    db.commit()
    return RedirectResponse("/", status_code=303)


@router.get("/ui/reports", response_class=HTMLResponse)
def reports_page(
    request: Request,
    module_id: int | None = None,
    db: Session = Depends(get_db),
):
    modules = db.query(models.Module).all()
    rows, selected = [], None
    if module_id:
        selected = db.get(models.Module, module_id)
        if selected:
            rows = reporting.module_report_rows(db, selected)
    return templates.TemplateResponse(
        "reports.html",
        {"request": request, "modules": modules, "rows": rows, "selected": selected},
    )


@router.get("/ui/portail", response_class=HTMLResponse)
def portal_page(
    request: Request,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    selected = db.get(models.Etudiant, student_id) if student_id else None
    hist = reporting.student_history(db, selected) if selected else None
    return templates.TemplateResponse(
        "portal.html",
        {
            "request": request,
            "etudiants": db.query(models.Etudiant).all(),
            "selected": selected,
            "hist": hist,
        },
    )
