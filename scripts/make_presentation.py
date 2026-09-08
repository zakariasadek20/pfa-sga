"""Génère le support de soutenance : un diaporama HTML autonome (images intégrées).

    python scripts/make_presentation.py  ->  rapport/presentation.html
"""

import base64
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insightface.data import get_image as ins_get_image  # noqa: E402

from face_attendance.face.engine import FaceEngine, identify  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DIAG = ROOT / "rapport" / "diagrammes"
OUT = ROOT / "rapport" / "presentation.html"


def b64_file(path) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def demo_recognition_b64() -> str:
    """Image de démo : enrôle puis reconnaît les visages de l'image test t1."""
    eng = FaceEngine()
    img = ins_get_image("t1")
    faces = eng.analyze(img)
    db = {f"Etudiant {i + 1}": f.embedding[None, :] for i, f in enumerate(faces)}
    for f in faces:
        name, sim = identify(f.embedding, db, 0.35)
        x1, y1, x2, y2 = f.bbox
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 170, 0), 3)
        cv2.putText(img, f"{name} ({sim:.2f})", (x1, max(22, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 170, 0), 2)
    ok, buf = cv2.imencode(".jpg", img)
    return base64.b64encode(buf.tobytes()).decode()


def img_tag(b64, alt=""):
    return f'<img src="data:image/png;base64,{b64}" alt="{alt}">'


def jpg_tag(b64, alt=""):
    return f'<img src="data:image/jpeg;base64,{b64}" alt="{alt}">'


def build():
    im = {n: b64_file(DIAG / f"{n}.png") for n in [
        "architecture-technique", "diagramme-sequence",
        "fig_similarites", "fig_far_frr",
    ]}
    demo = demo_recognition_b64()

    slides = []

    slides.append("""
    <section class="slide title">
      <div class="kicker">ISGA — Cycle d'ingénieur (2ᵉ année) · PFA 2025–2026</div>
      <h1>Système intelligent de gestion des présences<br>par reconnaissance faciale</h1>
      <div class="subtitle">« AI Class Attendance for Students »</div>
      <div class="team">BENDADI Mohamed &nbsp;·&nbsp; SADEK Zakaria &nbsp;·&nbsp; BELHASSAN Amine</div>
      <div class="enc">Encadrant : M. Adama SAMAKE</div>
    </section>""")

    slides.append("""
    <section class="slide">
      <h2>Contexte &amp; problématique</h2>
      <ul>
        <li>L'appel manuel mobilise <b>5 à 10 minutes</b> par séance.</li>
        <li>La <b>fraude par procuration</b> : un étudiant répond pour un absent.</li>
        <li>Les feuilles papier se perdent : <b>aucune statistique</b> d'assiduité.</li>
      </ul>
      <p class="lead">→ Automatiser l'appel par la <b>reconnaissance faciale</b>, de façon fiable et éthique.</p>
    </section>""")

    slides.append("""
    <section class="slide">
      <h2>Objectifs</h2>
      <ul>
        <li>Reconnaître automatiquement les présents à partir d'une <b>photo</b> ou de la <b>webcam</b>.</li>
        <li>Précision élevée (<b>≥ 90–95 %</b>) sur du <b>matériel courant</b> (CPU).</li>
        <li>Respecter la <b>protection des données biométriques</b> (loi 09-08 / CNDP).</li>
        <li>Bonus : <b>anti-fraude</b> (détection du vivant).</li>
      </ul>
    </section>""")

    slides.append("""
    <section class="slide">
      <h2>État de l'art</h2>
      <ul>
        <li>Chaîne type : <b>Détection → Empreinte → Appariement</b>.</li>
        <li><b>RetinaFace</b> (détection) · <b>ArcFace</b> (empreinte 512-d).</li>
        <li>Benchmark LFW : ArcFace <b>≈ 99,8 %</b> (au-delà de l'humain, 97,5 %).</li>
        <li><b>Anti-spoofing</b> (MiniFASNet) contre les attaques par photo/écran.</li>
      </ul>
      <p class="note">Nous <b>intégrons</b> ces briques éprouvées plutôt que d'entraîner un modèle.</p>
    </section>""")

    slides.append(f"""
    <section class="slide">
      <h2>Architecture du système</h2>
      <div class="fig">{img_tag(im['architecture-technique'], 'Architecture')}</div>
    </section>""")

    slides.append(f"""
    <section class="slide">
      <h2>Fonctionnement — prise de présence</h2>
      <div class="fig">{img_tag(im['diagramme-sequence'], 'Séquence')}</div>
    </section>""")

    slides.append("""
    <section class="slide">
      <h2>Implémentation</h2>
      <ul>
        <li><b>Python</b> · InsightFace (RetinaFace + ArcFace) · <b>FastAPI</b> · SQLite.</li>
        <li><b>Dashboard</b> web : enrôlement, prise de présence, validation, rapports.</li>
        <li>Exports <b>Excel / PDF</b> · <b>Portail étudiant</b> · <b>Alertes</b> d'absence.</li>
        <li><b>Anti-spoofing</b> (ONNX) · <b>Temps réel</b> webcam.</li>
      </ul>
    </section>""")

    slides.append(f"""
    <section class="slide">
      <h2>Démonstration — reconnaissance</h2>
      <div class="fig">{jpg_tag(demo, 'Reconnaissance')}</div>
      <p class="note">Détection de tous les visages puis appariement à la base des étudiants.</p>
    </section>""")

    slides.append(f"""
    <section class="slide">
      <h2>Résultats — séparation des identités</h2>
      <div class="fig">{img_tag(im['fig_similarites'], 'Distributions')}</div>
      <p class="note"><b>100 %</b> de précision (top-1) en conditions contrôlées (jeu LFW).</p>
    </section>""")

    slides.append(f"""
    <section class="slide">
      <h2>Résultats — calibration du seuil</h2>
      <div class="fig">{img_tag(im['fig_far_frr'], 'FAR/FRR')}</div>
      <p class="note">FAR = FRR = 0 sur une large plage ; seuil retenu : <b>0,35</b>.</p>
    </section>""")

    slides.append("""
    <section class="slide">
      <h2>Anti-spoofing (détection du vivant)</h2>
      <ul>
        <li>Modèle <b>MiniFASNet</b> (ONNX) — distingue un visage réel d'une photo.</li>
        <li>Les visages suspects sont <b>signalés en orange</b> dans le tableau de bord.</li>
        <li>Vrais visages <b>validés</b> ; rejet d'attaque à éprouver avec une webcam.</li>
      </ul>
    </section>""")

    slides.append("""
    <section class="slide">
      <h2>Conclusion &amp; perspectives</h2>
      <ul>
        <li>Un système <b>complet et fonctionnel</b>, accompagné d'un rapport rédigé.</li>
        <li>La <b>protection des données</b> au cœur de la démarche (empreintes, consentement).</li>
        <li>Perspectives : <b>validation en conditions réelles</b>, temps réel, application mobile.</li>
      </ul>
    </section>""")

    slides.append("""
    <section class="slide title">
      <h1>Merci de votre attention</h1>
      <div class="subtitle">Questions ?</div>
    </section>""")

    css = """
    *{box-sizing:border-box;margin:0;padding:0}
    :root{--indigo:#4f46e5;--ink:#1f2937;--muted:#6b7280;--bg:#f4f5fb}
    html,body{height:100%}
    body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);
      background:var(--bg);scroll-snap-type:y mandatory;overflow-y:scroll}
    .slide{height:100vh;scroll-snap-align:start;display:flex;flex-direction:column;
      justify-content:center;padding:6vh 9vw;position:relative}
    .slide h2{font-size:2.1rem;color:var(--indigo);margin-bottom:24px;
      border-bottom:3px solid #e0e0f5;padding-bottom:10px}
    .slide ul{list-style:none;max-width:60ch}
    .slide li{font-size:1.4rem;line-height:1.9;padding-left:28px;position:relative}
    .slide li:before{content:"▹";color:var(--indigo);position:absolute;left:0}
    .lead{font-size:1.5rem;margin-top:26px;color:var(--indigo);font-weight:600}
    .note{font-size:1.15rem;color:var(--muted);margin-top:18px;font-style:italic}
    .fig{flex:1;display:flex;align-items:center;justify-content:center;min-height:0;margin-top:10px}
    .fig img{max-width:100%;max-height:64vh;border-radius:12px;
      box-shadow:0 8px 30px rgba(31,41,55,.12)}
    .title{align-items:center;text-align:center;
      background:linear-gradient(135deg,#4f46e5,#4338ca);color:#fff}
    .title h1{font-size:2.7rem;line-height:1.25;margin-bottom:18px}
    .title .kicker{text-transform:uppercase;letter-spacing:.14em;font-size:.95rem;
      opacity:.85;margin-bottom:28px}
    .title .subtitle{font-size:1.5rem;opacity:.95;margin-bottom:34px}
    .title .team{font-size:1.25rem;font-weight:600;margin-bottom:8px}
    .title .enc{font-size:1.05rem;opacity:.85}
    .pageno{position:absolute;bottom:3vh;right:4vw;color:var(--muted);font-size:.9rem}
    .title .pageno{color:rgba(255,255,255,.7)}
    """

    js = """
    const slides=[...document.querySelectorAll('.slide')];
    slides.forEach((s,i)=>{const n=document.createElement('div');n.className='pageno';
      n.textContent=(i+1)+' / '+slides.length;s.appendChild(n);});
    let cur=0;
    function go(d){cur=Math.max(0,Math.min(slides.length-1,cur+d));
      slides[cur].scrollIntoView({behavior:'smooth'});}
    addEventListener('keydown',e=>{
      if(['ArrowDown','ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(1);}
      if(['ArrowUp','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(-1);}});
    """

    html = (
        "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>Soutenance — AI Class Attendance</title><style>"
        + css + "</style></head><body>"
        + "\n".join(slides)
        + "<script>" + js + "</script></body></html>"
    )
    OUT.write_text(html, encoding="utf-8")
    print("Présentation écrite :", OUT, f"({len(slides)} diapositives)")


if __name__ == "__main__":
    build()
