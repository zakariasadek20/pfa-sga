"""Routes des rapports d'assiduité."""

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import alerts, exports, models, reporting, schemas
from ..database import get_db

router = APIRouter(tags=["rapports"])


@router.get("/modules/{module_id}/report", response_model=list[schemas.ReportRow])
def module_report(module_id: int, db: Session = Depends(get_db)):
    """Taux de présence de chaque étudiant de la classe, sur les séances du module."""
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(404, "Module introuvable")
    return [
        schemas.ReportRow(
            etudiant_id=r["etudiant_id"],
            nom=r["nom"],
            total_seances=r["total"],
            presences=r["presences"],
            taux=r["taux"],
        )
        for r in reporting.module_report_rows(db, module)
    ]


@router.get("/modules/{module_id}/report.xlsx")
def export_report_xlsx(module_id: int, db: Session = Depends(get_db)):
    """Export Excel du rapport d'assiduité d'un module."""
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(404, "Module introuvable")
    data = exports.report_xlsx(module.libelle, reporting.module_report_rows(db, module))
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="rapport_module_{module_id}.xlsx"'},
    )


@router.get("/modules/{module_id}/report.pdf")
def export_report_pdf(module_id: int, db: Session = Depends(get_db)):
    """Export PDF du rapport d'assiduité d'un module."""
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(404, "Module introuvable")
    data = exports.report_pdf(module.libelle, reporting.module_report_rows(db, module))
    return StreamingResponse(
        BytesIO(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="rapport_module_{module_id}.pdf"'},
    )


@router.get("/modules/{module_id}/alerts")
def module_alerts(
    module_id: int,
    threshold: float = 50.0,
    send: bool = False,
    db: Session = Depends(get_db),
):
    """Prévisualise (send=false) ou envoie (send=true) les alertes d'absentéisme."""
    module = db.get(models.Module, module_id)
    if not module:
        raise HTTPException(404, "Module introuvable")
    items = alerts.build_absence_alerts(db, module, threshold)
    result = {"module": module.libelle, "seuil": threshold, "alertes": items}
    if send:
        result["envoi"] = alerts.send_alerts(items)
    return result


@router.get("/students/{student_id}/attendance-rate")
def student_rate(student_id: int, db: Session = Depends(get_db)):
    """Taux de présence global d'un étudiant."""
    if not db.get(models.Etudiant, student_id):
        raise HTTPException(404, "Étudiant introuvable")
    total = (
        db.query(models.Presence)
        .filter(models.Presence.etudiant_id == student_id)
        .count()
    )
    present = (
        db.query(models.Presence)
        .filter(
            models.Presence.etudiant_id == student_id,
            models.Presence.statut != "absent",
        )
        .count()
    )
    taux = round(present / total * 100, 1) if total else 0.0
    return {
        "etudiant_id": student_id,
        "seances_enregistrees": total,
        "presences": present,
        "taux": taux,
    }
