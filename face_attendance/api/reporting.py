"""Calcul des rapports d'assiduité (logique partagée API / dashboard / exports)."""

from . import models


def module_report_rows(db, module) -> list:
    """Renvoie, pour chaque étudiant de la classe du module, son taux de présence.

    Chaque ligne : ``{etudiant_id, nom, total, presences, taux}``.
    """
    seance_ids = [
        s.id
        for s in db.query(models.Seance)
        .filter(models.Seance.module_id == module.id)
        .all()
    ]
    total = len(seance_ids)

    q = db.query(models.Etudiant)
    if module.classe_id:
        q = q.filter(models.Etudiant.classe_id == module.classe_id)

    rows = []
    for e in q.all():
        presences = 0
        if seance_ids:
            presences = (
                db.query(models.Presence)
                .filter(
                    models.Presence.etudiant_id == e.id,
                    models.Presence.seance_id.in_(seance_ids),
                    models.Presence.statut != "absent",
                )
                .count()
            )
        rows.append(
            {
                "etudiant_id": e.id,
                "nom": f"{e.prenom or ''} {e.nom}".strip(),
                "total": total,
                "presences": presences,
                "taux": round(presences / total * 100, 1) if total else 0.0,
            }
        )
    return rows


def student_history(db, student) -> dict:
    """Historique d'assiduité d'un étudiant sur les séances de sa classe.

    Renvoie ``{total, presences, taux, rows:[{seance, module, present}]}``.
    """
    if student.classe_id:
        module_ids = [
            m.id for m in db.query(models.Module)
            .filter(models.Module.classe_id == student.classe_id).all()
        ]
    else:
        module_ids = [m.id for m in db.query(models.Module).all()]

    seances = []
    if module_ids:
        seances = (
            db.query(models.Seance)
            .filter(models.Seance.module_id.in_(module_ids))
            .all()
        )
    present_ids = {
        p.seance_id
        for p in db.query(models.Presence).filter(
            models.Presence.etudiant_id == student.id,
            models.Presence.statut != "absent",
        ).all()
    }

    rows = [{"seance": s, "present": s.id in present_ids} for s in seances]
    total = len(rows)
    presences = sum(1 for r in rows if r["present"])
    return {
        "total": total,
        "presences": presences,
        "taux": round(presences / total * 100, 1) if total else 0.0,
        "rows": rows,
    }
