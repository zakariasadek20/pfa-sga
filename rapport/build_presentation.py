#!/usr/bin/env python3
"""Construit la présentation de soutenance : rapport/presentation-pfa.pptx.

PowerPoint natif (éditable), format 16:9, charte du rapport (bleu marine /
bleu), logo ISGA, figures et captures réelles du projet. Chaque diapositive a
une transition en fondu ; le contenu apparaît en fondu au clic.

    .venv/bin/python rapport/build_presentation.py
Dépendance : python-pptx (voir rapport/requirements-build.txt).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
DIAG = HERE / "diagrammes"
LOGO = HERE / "assets" / "isga-logo.png"
OUT = HERE / "presentation-pfa.pptx"

NAVY = RGBColor(0x17, 0x36, 0x5D)
BLUE = RGBColor(0x36, 0x5F, 0x91)
ACCENT = RGBColor(0x4F, 0x81, 0xBD)
GREY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xEE, 0xF3, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x20, 0x24, 0x2B)

EMU_IN = 914400
SW, SH = 13.333, 7.5

prs = Presentation()
prs.slide_width = Inches(SW)
prs.slide_height = Inches(SH)
BLANK = prs.slide_layouts[6]


# ─────────────────────────── helpers ───────────────────────────
def _solid(shape, color):
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def rect(slide, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
                                Inches(w), Inches(h))
    _solid(sp, color)
    sp.shadow.inherit = False
    return sp


def textbox(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    return tb


def _run(p, text, size, color, bold=False, italic=False, font="Calibri"):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    return r


def bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def new_slide():
    return prs.slides.add_slide(BLANK)


def footer(slide, n):
    ln = rect(slide, 0.9, 6.95, 11.53, 0.012, RGBColor(0xD0, 0xD8, 0xE4))
    tb = textbox(slide, 0.9, 7.0, 8, 0.35)
    p = tb.text_frame.paragraphs[0]
    _run(p, "AI Class Attendance for Students · ISGA — PFA 2025/2026", 9, GREY)
    tn = textbox(slide, 11.4, 7.0, 1.03, 0.35)
    pn = tn.text_frame.paragraphs[0]
    pn.alignment = PP_ALIGN.RIGHT
    _run(pn, str(n), 9, GREY)


def title(slide, text):
    tb = textbox(slide, 0.9, 0.5, 11.5, 0.95)
    p = tb.text_frame.paragraphs[0]
    _run(p, text, 30, NAVY, bold=True)
    rect(slide, 0.92, 1.45, 2.1, 0.06, ACCENT)
    return tb


def bullets(slide, items, top=1.95, left=1.0, width=11.3, height=4.6, size=19, gap=14):
    tb = textbox(slide, left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.12
        if isinstance(it, tuple):        # (texte, niveau)
            text, lvl = it
        else:
            text, lvl = it, 0
        _bullet(p, ACCENT if lvl == 0 else RGBColor(0x9A, 0xB4, 0xD4), lvl)
        _run(p, text, size if lvl == 0 else size - 3,
             DARK if lvl == 0 else GREY, bold=False)
        p.level = lvl
    return tb


def _bullet(paragraph, color, lvl):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("indent", str(-Emu(Inches(0.3)).emu if False else -274320))
    pPr.set("marL", str(274320 + lvl * 274320))
    buClr = pPr.makeelement(qn("a:buClr"), {})
    clr = buClr.makeelement(qn("a:srgbClr"), {"val": "%02X%02X%02X" % (color[0], color[1], color[2])})
    buClr.append(clr)
    buFont = pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"})
    buChar = pPr.makeelement(qn("a:buChar"), {"char": "▪" if lvl == 0 else "–"})
    for el in (buClr, buFont, buChar):
        pPr.append(el)


def image_fit(slide, path, x, y, w, h, center=True):
    iw, ih = Image.open(path).size
    ar = iw / ih
    bw, bh = w, h
    if bw / bh > ar:
        nw, nh = bh * ar, bh
    else:
        nw, nh = bw, bw / ar
    nx = x + (w - nw) / 2 if center else x
    ny = y + (h - nh) / 2 if center else y
    return slide.shapes.add_picture(str(path), Inches(nx), Inches(ny),
                                    Inches(nw), Inches(nh))


def caption(slide, text, y=6.5):
    tb = textbox(slide, 0.9, y, 11.5, 0.4)
    p = tb.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, text, 11, BLUE, italic=True)


# ── animations : transition fondu + entrée en fondu au clic ──
def add_transition(slide):
    xml = ('<p:transition xmlns:p="http://schemas.openxmlformats.org/'
           'presentationml/2006/main" spd="med"><p:fade/></p:transition>')
    slide._element.append(_parse(xml))


# Les entrées animées au clic masquent le contenu tant qu'on n'a pas cliqué, ce
# qui casse l'aperçu dans certains lecteurs (Keynote/PowerPoint Mac). On garde
# uniquement les transitions en fondu, fiables partout. Mettre à True pour les
# réactiver.
ANIMATE_ENTRANCE = False


def add_fade_click(slide, spids):
    """Entrée en fondu au clic pour la liste d'id de formes `spids`."""
    if not ANIMATE_ENTRANCE:
        return
    cid = [2]

    def nid():
        cid[0] += 1
        return cid[0]

    blocks = ""
    for spid in spids:
        a, b, c, d, e = nid(), nid(), nid(), nid(), nid()
        blocks += (
            f'<p:par><p:cTn id="{a}" fill="hold"><p:stCondLst>'
            f'<p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{b}" fill="hold"><p:stCondLst>'
            f'<p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{c}" presetID="10" presetClass="entr" '
            f'presetSubtype="0" fill="hold" grpId="0" nodeType="clickEffect">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:set><p:cBhvr><p:cTn id="{d}" dur="1" fill="hold"><p:stCondLst>'
            f'<p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl>'
            f'<p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst>'
            f'<p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr>'
            f'<p:cTn id="{e}" dur="500"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            f'</p:cBhvr></p:animEffect>'
            f'</p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn></p:par>'
        )
    xml = (
        '<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        '<p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" '
        'nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" '
        f'nodeType="mainSeq"><p:childTnLst>{blocks}</p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/>'
        '</p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/>'
        '</p:tgtEl></p:cond></p:nextCondLst></p:seq>'
        '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'
    )
    slide._element.append(_parse(xml))


def _parse(xml):
    from pptx.oxml import parse_xml
    return parse_xml(xml)


# ─────────────────────────── diapositives ───────────────────────────
def slide_title():
    s = new_slide()
    bg(s, NAVY)
    rect(s, 0, 0, SW, 0.28, ACCENT)
    rect(s, 0, SH - 0.28, SW, 0.28, ACCENT)
    s.shapes.add_picture(str(LOGO), Inches(5.55), Inches(0.85), height=Inches(1.15))
    tb = textbox(s, 1.0, 2.5, 11.33, 1.9)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, "Système intelligent de gestion des présences", 34, WHITE, bold=True)
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    _run(p2, "par reconnaissance faciale", 34, WHITE, bold=True)
    p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER; p3.space_before = Pt(14)
    _run(p3, "« AI Class Attendance for Students »", 18, RGBColor(0xBE, 0xD0, 0xE8),
         italic=True)
    box = textbox(s, 1.0, 5.15, 11.33, 1.7)
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, "Projet de Fin d'Année — Cycle d'ingénieur (2ᵉ année) — 2025 / 2026",
         15, RGBColor(0xD7, 0xE0, 0xEF))
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER; p.space_before = Pt(12)
    _run(p, "Réalisé par : ", 15, WHITE, bold=True)
    _run(p, "BENDADI Mohamed · SADEK Zakaria · BELHASSAN Amine", 15, WHITE)
    p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER; p.space_before = Pt(4)
    _run(p, "Encadré par : ", 15, WHITE, bold=True)
    _run(p, "M. Adama SAMAKE", 15, WHITE)
    add_transition(s)


def slide_plan():
    s = new_slide(); bg(s, WHITE)
    title(s, "Plan de la présentation")
    items = [
        "1.  Contexte & problématique", "2.  Objectifs du projet",
        "3.  État de l'art", "4.  Conception du système",
        "5.  Implémentation", "6.  Démonstration",
        "7.  Résultats & évaluation", "8.  Éthique & conformité (loi 09-08)",
        "9.  Conclusion & perspectives",
    ]
    tb = textbox(s, 1.2, 1.95, 11.0, 4.7)
    tf = tb.text_frame
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(10)
        _run(p, it, 19, DARK)
    footer(s, 2); add_transition(s)
    add_fade_click(s, [tb.shape_id])


def content(n, ttl, items, size=19):
    s = new_slide(); bg(s, WHITE)
    title(s, ttl)
    tb = bullets(s, items, size=size)
    footer(s, n); add_transition(s)
    add_fade_click(s, [tb.shape_id])
    return s


def image_slide(n, ttl, img, cap, box=(0.9, 1.85, 11.5, 4.5)):
    s = new_slide(); bg(s, WHITE)
    title(s, ttl)
    pic = image_fit(s, DIAG / img, *box)
    caption(s, cap)
    footer(s, n); add_transition(s)
    add_fade_click(s, [pic.shape_id])
    return s


# 1 — titre
slide_title()
# 2 — plan
slide_plan()
# 3 — contexte
content(3, "1. Contexte & problématique", [
    "L'appel manuel mobilise 5 à 10 minutes par séance — autant de temps pédagogique perdu.",
    "La fraude par procuration (proxy attendance) : un étudiant répond ou signe pour un absent.",
    "Les feuilles papier se perdent, se raturent, et ne produisent aucune statistique.",
    ("Comment automatiser l'appel de façon fiable, rapide et éthique ?", 0),
])
# 4 — objectifs
content(4, "2. Objectifs du projet", [
    "Identifier automatiquement les étudiants présents à partir d'une photo de la classe.",
    "Enregistrer les présences et offrir à l'enseignant un tableau de bord de suivi.",
    "Atteindre une précision élevée sur du matériel standard (ordinateur portable, CPU).",
    "Détecter la fraude par photo (détection du vivant / anti-spoofing).",
    "Respecter la réglementation sur les données biométriques (loi 09-08 / CNDP).",
])
# 5 — état de l'art
content(5, "3. État de l'art", [
    "Chaîne de traitement : Détection → Alignement → Empreinte → Appariement.",
    ("Détection : RetinaFace — robuste (petits visages, angles).", 1),
    ("Reconnaissance : ArcFace, empreinte 512-d — ~99,4 à 99,8 % sur LFW.", 1),
    ("Les meilleurs modèles dépassent la performance humaine (~97,5 %).", 1),
    "Notre choix : intégrer les meilleures briques pré-entraînées plutôt que réentraîner.",
])
# 6 — architecture
image_slide(6, "4. Conception — architecture", "architecture-technique.png",
            "Figure — Architecture technique en trois couches (interface, serveur + IA, persistance).")
# 7 — cas d'utilisation
image_slide(7, "4. Conception — cas d'utilisation", "cas-utilisation.png",
            "Figure — Acteurs et cas d'utilisation ; l'enseignant valide toujours avant enregistrement.")
# 8 — implémentation
content(8, "5. Implémentation", [
    "Python 3.12, exécution sur CPU (Apple Silicon, sans carte graphique).",
    "Cœur IA : InsightFace (RetinaFace + ArcFace) via ONNX Runtime, OpenCV.",
    "Backend : FastAPI + SQLAlchemy + SQLite ; tableau de bord en gabarits Jinja2.",
    "Exports Excel / PDF ; module anti-spoofing MiniFASNet-V2.",
    "Principe clé : la reconnaissance propose, l'enseignant valide, puis on enregistre.",
])
# 9 — démonstration
image_slide(9, "6. Démonstration — prise de présence", "cap_reconnaissance.png",
            "Sur une photo de la classe, chaque étudiant est détecté, reconnu et nommé, avant validation.")
# 10 — résultats LFW
image_slide(10, "7. Résultats — évaluation contrôlée (LFW)", "fig_similarites.png",
            "15 identités, 56 photos de test → précision top-1 de 100 % ; distributions nettement séparées.")
# 11 — seuil
image_slide(11, "7. Résultats — calibration du seuil", "fig_far_frr.png",
            "FAR et FRR nuls entre 0,20 et 0,50 ; seuil retenu : 0,35.")
# 12 — multi-visages
image_slide(12, "7. Résultats — scène multi-visages", "fig_classe_annotee.png",
            "10/10 étudiants reconnus, 2/2 intrus rejetés, ~2 s ; 2 détections parasites (arrière-plan).")
# 13 — éthique
content(13, "8. Éthique & conformité — loi 09-08", [
    "Le visage est une donnée biométrique sensible (loi 09-08, contrôle CNDP).",
    "Consentement explicite et écrit de chaque personne enrôlée.",
    "Minimisation : on conserve les empreintes plutôt que les images.",
    "Finalité déterminée, accès restreint, sécurité, suppression en fin de projet.",
    "Droits garantis : accès, rectification, suppression, retrait du consentement.",
])
# 14 — conclusion
content(14, "9. Conclusion & perspectives", [
    "Une application complète : enrôlement → reconnaissance → validation → rapports.",
    "Cœur du système validé : 100 % en conditions contrôlées, robuste en multi-visages.",
    ("Perspectives :", 0),
    ("validation sur une vraie photo de classe (avec consentement) ;", 1),
    ("anti-spoofing éprouvé face à de vraies attaques ; reconnaissance en temps réel ;", 1),
    ("application mobile et intégration au système d'information.", 1),
])


# 15 — merci
def slide_merci():
    s = new_slide(); bg(s, NAVY)
    rect(s, 0, 0, SW, 0.28, ACCENT)
    rect(s, 0, SH - 0.28, SW, 0.28, ACCENT)
    s.shapes.add_picture(str(LOGO), Inches(5.7), Inches(1.2), height=Inches(1.0))
    tb = textbox(s, 1.0, 2.9, 11.33, 1.6)
    p = tb.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, "Merci de votre attention", 40, WHITE, bold=True)
    p2 = tb.text_frame.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(10)
    _run(p2, "Questions & discussion", 20, RGBColor(0xBE, 0xD0, 0xE8), italic=True)
    box = textbox(s, 1.0, 5.4, 11.33, 1.0)
    p = box.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, "BENDADI Mohamed · SADEK Zakaria · BELHASSAN Amine", 14,
         RGBColor(0xD7, 0xE0, 0xEF))
    p = box.text_frame.add_paragraph(); p.alignment = PP_ALIGN.CENTER
    _run(p, "Encadré par M. Adama SAMAKE — ISGA, 2025/2026", 13,
         RGBColor(0xBE, 0xD0, 0xE8))
    add_transition(s)


slide_merci()

prs.save(str(OUT))
print(f"OK -> {OUT}  ({len(prs.slides)} diapositives)")
