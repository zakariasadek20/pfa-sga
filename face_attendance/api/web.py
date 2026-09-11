"""Dashboard web (rendu serveur, Jinja2) avec connexion et rôles.

Rôles : admin (gestion des étudiants), enseignant (prise de présence, rapports),
etudiant (portail personnel). Chaque page est protégée selon le rôle.
"""

import base64
from datetime import datetime
from pathlib import Path

import cv2

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import config
from . import auth, face_service, models, reporting
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


# ─────────────────────────── Authentification ───────────────────────────
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if auth.current_user(request, db):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    db: Session = Depends(get_db),
):
    u = (
        db.query(models.Utilisateur)
        .filter(models.Utilisateur.email == email.lower().strip())
        .first()
    )
    if u and auth.verify_password(mot_de_passe, u.mot_de_passe_hash):
        request.session["uid"] = u.id
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "E-mail ou mot de passe incorrect."},
        status_code=401,
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ─────────────────────────── Accueil (selon le rôle) ───────────────────────────
@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = auth.require(request, db)
    if user.role == "etudiant":
        return RedirectResponse("/ui/portail", status_code=303)
    ctx = {
        "request": request,
        "user": user,
        "n_etu": db.query(models.Etudiant).count(),
        "n_sea": db.query(models.Seance).count(),
        "n_pre": db.query(models.Presence).count(),
        "seances": db.query(models.Seance).order_by(models.Seance.id.desc()).limit(8).all(),
    }
    return templates.TemplateResponse("index.html", ctx)


# ─────────────────────────── Étudiants (admin) ───────────────────────────
@router.get("/ui/students", response_class=HTMLResponse)
def students_page(request: Request, db: Session = Depends(get_db)):
    user = auth.require(request, db, roles=["admin"])
    etus = db.query(models.Etudiant).all()
    counts = {e.id: len(e.empreintes) for e in etus}
    ctx = {
        "request": request, "user": user, "etudiants": etus, "counts": counts,
        "classes": db.query(models.Classe).all(),
    }
    return templates.TemplateResponse("students.html", ctx)


@router.post("/ui/students")
def create_student_ui(
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(""),
    code: str = Form(""),
    classe_id: str = Form(""),
    db: Session = Depends(get_db),
):
    auth.require(request, db, roles=["admin"])
    etu = models.Etudiant(
        nom=nom, prenom=prenom or None, code=code or None,
        classe_id=int(classe_id) if classe_id else None,
    )
    db.add(etu)
    db.commit()
    auth.create_student_login(db, etu)   # crée son compte de connexion (rôle etudiant)
    return RedirectResponse("/ui/students", status_code=303)


@router.get("/ui/students/{sid}/enroll", response_class=HTMLResponse)
def enroll_page(sid: int, request: Request, db: Session = Depends(get_db)):
    user = auth.require(request, db, roles=["admin"])
    etu = db.get(models.Etudiant, sid)
    return templates.TemplateResponse(
        "enroll.html", {"request": request, "user": user, "etu": etu}
    )


@router.post("/ui/students/{sid}/enroll")
def enroll_ui(
    sid: int,
    request: Request,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    auth.require(request, db, roles=["admin"])
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


# ─────────────────────────── Prise de présence (enseignant) ───────────────────────────
@router.get("/ui/attendance", response_class=HTMLResponse)
def attendance_page(request: Request, db: Session = Depends(get_db)):
    user = auth.require(request, db, roles=["admin", "enseignant"])
    return templates.TemplateResponse(
        "attendance.html",
        {"request": request, "user": user, "seances": db.query(models.Seance).all()},
    )


@router.post("/ui/attendance/recognize", response_class=HTMLResponse)
def attendance_recognize(
    request: Request,
    seance_id: int = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = auth.require(request, db, roles=["admin", "enseignant"])
    enroll_map = face_service.build_enroll_map(db)
    faces, image_b64 = _recognize_and_annotate(photo.file.read(), enroll_map, db)
    seance = db.get(models.Seance, seance_id)
    return templates.TemplateResponse(
        "attendance_result.html",
        {"request": request, "user": user, "seance": seance, "faces": faces,
         "image_b64": image_b64},
    )


@router.post("/ui/attendance/confirm")
def attendance_confirm(
    request: Request,
    seance_id: int = Form(...),
    present_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
):
    auth.require(request, db, roles=["admin", "enseignant"])
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


# ─────────────────────────── Rapports (enseignant) ───────────────────────────
@router.get("/ui/reports", response_class=HTMLResponse)
def reports_page(
    request: Request,
    module_id: int | None = None,
    db: Session = Depends(get_db),
):
    user = auth.require(request, db, roles=["admin", "enseignant"])
    modules = db.query(models.Module).all()
    rows, selected = [], None
    if module_id:
        selected = db.get(models.Module, module_id)
        if selected:
            rows = reporting.module_report_rows(db, selected)
    return templates.TemplateResponse(
        "reports.html",
        {"request": request, "user": user, "modules": modules, "rows": rows,
         "selected": selected},
    )


# ─────────────────────────── Portail (étudiant : soi-même) ───────────────────────────
@router.get("/ui/portail", response_class=HTMLResponse)
def portal_page(
    request: Request,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    user = auth.require(request, db)   # tous les rôles connectés
    if user.role == "etudiant":
        student_id = user.etudiant_id   # un étudiant ne voit que sa propre assiduité
    selected = db.get(models.Etudiant, student_id) if student_id else None
    hist = reporting.student_history(db, selected) if selected else None
    if user.role == "etudiant":
        etuds = [selected] if selected else []
    else:
        etuds = db.query(models.Etudiant).all()
    return templates.TemplateResponse(
        "portal.html",
        {"request": request, "user": user, "etudiants": etuds,
         "selected": selected, "hist": hist},
    )
