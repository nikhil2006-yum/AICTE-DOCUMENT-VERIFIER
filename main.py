"""AICTE validation backend (prototype).
Run: pip install fastapi uvicorn python-multipart
     uvicorn main:app --reload
"""
from io import BytesIO
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
import sqlite3, uuid, datetime as dt
from pathlib import Path
from enum import Enum
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---- SECRET TOGGLE: "positive" or "bad" (replace with real model later) ----
MOCK_VERDICT = "positive"
# ----------------------------------------------------------------------------

UPLOAD_DIR = Path("uploads"); UPLOAD_DIR.mkdir(exist_ok=True)
DB = "docs.db"

class Flag(str, Enum):
    verified = "verified"
    mismatch = "mismatch_detected"
    expired = "expired"
    pending = "verification_pending"
    unavailable = "source_unavailable"
    manual = "manual_review_required"

class FlagUpdate(BaseModel):
    flag: Flag
    note: str | None = None

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS documents(
        id TEXT PRIMARY KEY, filename TEXT, path TEXT, review TEXT,
        flag TEXT, note TEXT, created_at TEXT, updated_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit(
        id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id TEXT, action TEXT, detail TEXT, at TEXT)""")

def now(): return dt.datetime.utcnow().isoformat()

def log(c, doc_id, action, detail):
    c.execute("INSERT INTO audit(doc_id,action,detail,at) VALUES(?,?,?,?)",
              (doc_id, action, detail, now()))

def review_pdf(path: Path) -> tuple[str, Flag]:
    """Placeholder for the real AI model."""
    if MOCK_VERDICT == "positive":
        return "positive", Flag.verified
    return "bad", Flag.manual

app = FastAPI(title="AICTE Validation Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.post("/documents")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "Only PDF files are accepted")
    doc_id = uuid.uuid4().hex
    path = UPLOAD_DIR / f"{doc_id}.pdf"
    path.write_bytes(data)
    review, flag = review_pdf(path)
    t = now()
    with db() as c:
        c.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?,?)",
                  (doc_id, file.filename, str(path), review, flag.value, None, t, t))
        log(c, doc_id, "uploaded", f"review={review}, flag={flag.value}")
    return {"id": doc_id, "filename": file.filename, "review": review, "flag": flag.value}

@app.get("/documents")
def list_docs():
    with db() as c:
        return [dict(r) for r in c.execute(
            "SELECT id,filename,review,flag,note,created_at,updated_at FROM documents ORDER BY created_at DESC")]

@app.get("/documents/{doc_id}")
def get_doc(doc_id: str):
    with db() as c:
        r = c.execute("SELECT id,filename,review,flag,note,created_at,updated_at FROM documents WHERE id=?",
                      (doc_id,)).fetchone()
        if not r: raise HTTPException(404, "Not found")
        out = dict(r)
        out["audit"] = [dict(a) for a in c.execute(
            "SELECT action,detail,at FROM audit WHERE doc_id=? ORDER BY id", (doc_id,))]
        return out

@app.patch("/documents/{doc_id}/flag")
def set_flag(doc_id: str, body: FlagUpdate):
    with db() as c:
        if not c.execute("SELECT 1 FROM documents WHERE id=?", (doc_id,)).fetchone():
            raise HTTPException(404, "Not found")
        c.execute("UPDATE documents SET flag=?, note=?, updated_at=? WHERE id=?",
                  (body.flag.value, body.note, now(), doc_id))
        log(c, doc_id, "flag_changed", f"flag={body.flag.value}, note={body.note}")
    return {"id": doc_id, "flag": body.flag.value, "note": body.note}

@app.get("/documents/{doc_id}/report")
def generate_report(doc_id: str):
    with db() as c:
        doc = c.execute(
            """SELECT id, filename, review, flag, note,
                      created_at, updated_at
               FROM documents WHERE id = ?""",
            (doc_id,)
        ).fetchone()

        if not doc:
            raise HTTPException(404, "Document not found")

        audit_rows = c.execute(
            """SELECT action, detail, at FROM audit
               WHERE doc_id = ? ORDER BY id""",
            (doc_id,)
        ).fetchall()

    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(
        "AICTE DOCUMENT VALIDATION REPORT",
        styles["Title"]
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Prototype report — not an official AICTE certificate",
        styles["Italic"]
    ))
    story.append(Spacer(1, 16))

    details = [
        ["Field", "Value"],
        ["Document ID", str(doc["id"])],
        ["Filename", str(doc["filename"] or "Unknown")],
        ["Review result", str(doc["review"] or "Pending")],
        ["Current status", str(doc["flag"] or "Pending")],
        ["Review note", str(doc["note"] or "No additional notes")],
        ["Uploaded at (UTC)", str(doc["created_at"])],
        ["Last updated (UTC)", str(doc["updated_at"])],
    ]

    table = Table(details, colWidths=[4 * cm, 12 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Validation findings", styles["Heading2"]))
    story.append(Paragraph(
        "The current prototype uses a mock review verdict. "
        "Actual digital-signature authentication, trusted-source "
        "matching, expiry validation and AICTE compliance checks "
        "have not yet been implemented. The status shown above "
        "must not be interpreted as proof of authenticity.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Audit history", styles["Heading2"]))

    audit_data = [["Action", "Details", "Timestamp (UTC)"]]

    for item in audit_rows:
        audit_data.append([
            str(item["action"] or ""),
            str(item["detail"] or ""),
            str(item["at"] or "")
        ])

    audit_table = Table(
        audit_data,
        colWidths=[3 * cm, 7 * cm, 6 * cm],
        repeatRows=1
    )
    audit_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(audit_table)
    pdf.build(story)

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="AICTE_Report_{doc_id}.pdf"'
        }
    )
 
