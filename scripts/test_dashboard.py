"""Vérifie le dashboard sans serveur réseau (TestClient) et exporte le HTML rendu."""

import glob
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from sklearn.datasets import get_data_home  # noqa: E402

from face_attendance.api.database import init_db  # noqa: E402
from face_attendance.api.main import app  # noqa: E402

init_db()
client = TestClient(app)
out = Path("/tmp/dash")
out.mkdir(exist_ok=True)

pages = [
    ("/", "home"),
    ("/ui/students", "students"),
    ("/ui/attendance", "attendance"),
    ("/ui/reports?module_id=1", "reports"),
    ("/ui/portail", "portal"),
]
for path, name in pages:
    r = client.get(path)
    (out / f"{name}.html").write_text(r.text, encoding="utf-8")
    print(f"GET {path:32s} -> {r.status_code}  ({len(r.text)} o)")

# Portail d'un étudiant précis
studs = client.get("/students").json()
if studs:
    sid = studs[0]["id"]
    r = client.get(f"/ui/portail?student_id={sid}")
    (out / "portal_student.html").write_text(r.text, encoding="utf-8")
    print(f"GET /ui/portail?student_id={sid}           -> {r.status_code}  (taux affiché: {'%' in r.text})")

# Reconnaissance rendue (page résultat avec image annotée)
seances = client.get("/seances").json()
sid = seances[0]["id"] if seances else None
aaron = sorted(
    glob.glob(os.path.join(get_data_home(), "lfw_home", "lfw_funneled",
                           "Aaron_Peirsol", "*.jpg"))
)
if sid and aaron:
    with open(aaron[-1], "rb") as fh:
        r = client.post(
            "/ui/attendance/recognize",
            data={"seance_id": sid},
            files={"photo": ("a.jpg", fh, "image/jpeg")},
        )
    (out / "attendance_result.html").write_text(r.text, encoding="utf-8")
    print(f"POST recognize                       -> {r.status_code}  "
          f"(Aaron reconnu: {'Aaron' in r.text}, image: {'base64' in r.text})")

print("Pages exportées dans", out)
