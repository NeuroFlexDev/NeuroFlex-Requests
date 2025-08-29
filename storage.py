import sqlite3, json, pandas as pd, shutil, os
from pathlib import Path
from datetime import datetime
from config import settings, BASE_DIR

DB_PATH = settings.DB_PATH
DATA_DIR = Path(BASE_DIR) / "data"
FILES_ROOT = DATA_DIR / "files"
BRIEFS_DIR = DATA_DIR / "briefs"
for d in (Path(DB_PATH).parent, FILES_ROOT, BRIEFS_DIR): d.mkdir(parents=True, exist_ok=True)

DDL = """
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  lang TEXT,
  name TEXT NOT NULL,
  company TEXT,
  email TEXT NOT NULL,
  contact TEXT NOT NULL,
  req_type TEXT NOT NULL,
  description TEXT NOT NULL,
  budget TEXT,
  ai_data TEXT,
  ai_dataset TEXT,
  web_auth TEXT,
  web_integrations TEXT
);
CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER,
  user_id INTEGER,
  file_id TEXT NOT NULL,
  file_name TEXT,
  mime_type TEXT,
  file_size INTEGER,
  local_path TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(request_id) REFERENCES requests(id)
);
CREATE TABLE IF NOT EXISTS drafts (
  user_id INTEGER PRIMARY KEY,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.executescript(DDL)
    return c

def save_request(d: dict) -> int:
    with _conn() as c:
        cur = c.execute("""
            INSERT INTO requests(created_at,lang,name,company,email,contact,req_type,description,budget,ai_data,ai_dataset,web_auth,web_integrations)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,(datetime.utcnow().isoformat(), d.get("lang"), d["name"], d.get("company"), d["email"], d["contact"],
             d["req_type"], d["description"], d.get("budget"), d.get("ai_data"), d.get("ai_dataset"),
             d.get("web_auth"), d.get("web_integrations")))
        return cur.lastrowid

def save_temp_attachment(user_id:int, *, file_id:str, file_name:str|None, mime_type:str|None, file_size:int|None, local_path:str|None)->int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO attachments(request_id,user_id,file_id,file_name,mime_type,file_size,local_path,created_at) VALUES(NULL,?,?,?,?,?,?,?)",
            (user_id, file_id, file_name, mime_type, file_size, local_path, datetime.utcnow().isoformat())
        )
        return cur.lastrowid

def link_user_files_to_request(user_id:int, request_id:int):
    dest_dir = FILES_ROOT / f"request_{request_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        rows = c.execute("SELECT id, local_path, file_name FROM attachments WHERE user_id=? AND request_id IS NULL",(user_id,)).fetchall()
        for att_id, local_path, file_name in rows:
            if local_path and os.path.exists(local_path):
                new_path = dest_dir / (Path(local_path).name if not file_name else file_name)
                shutil.move(local_path, new_path)
                c.execute("UPDATE attachments SET request_id=?, local_path=? WHERE id=?", (request_id, str(new_path), att_id))
            else:
                c.execute("UPDATE attachments SET request_id=? WHERE id=?", (request_id, att_id))

def list_attachments_by_request(request_id:int)->list[dict]:
    with _conn() as c:
        cur = c.execute("SELECT id,file_name,mime_type,file_size,local_path FROM attachments WHERE request_id=? ORDER BY id",(request_id,))
        cols = [x[0] for x in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

def export_csv(path: str) -> str:
    with _conn() as c:
        df = pd.read_sql_query("SELECT * FROM requests ORDER BY id DESC", c)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig"); return path

def export_json(path: str) -> str:
    with _conn() as c:
        cur = c.execute("SELECT * FROM requests ORDER BY id DESC")
        rows = [dict(zip([col[0] for col in cur.description], r)) for r in cur.fetchall()]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"); return path

def stats() -> dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        by_type = dict(c.execute("SELECT req_type, COUNT(*) FROM requests GROUP BY req_type").fetchall())
    return {"total": total, "by_type": by_type}

def search_requests(q: str, limit: int = 10, offset: int = 0):
    q_like = f"%{q}%"
    with _conn() as c:
        cur = c.execute("""
          SELECT id, created_at, name, company, email, contact, req_type, substr(description,1,120) AS snippet
          FROM requests
          WHERE name LIKE ? OR company LIKE ? OR email LIKE ? OR description LIKE ?
          ORDER BY id DESC LIMIT ? OFFSET ?
        """, (q_like,q_like,q_like,q_like,limit,offset))
        cols=[x[0] for x in cur.description]
        rows=[dict(zip(cols,r)) for r in cur.fetchall()]
    return rows

def get_latest(limit: int=10, offset:int=0):
    with _conn() as c:
        cur = c.execute("SELECT id, created_at, name, company, email, contact, req_type FROM requests ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
        cols=[x[0] for x in cur.description]
        return [dict(zip(cols,r)) for r in cur.fetchall()]

def get_request(rid: int) -> dict | None:
    with _conn() as c:
        cur = c.execute("SELECT * FROM requests WHERE id=?", (rid,))
        row = cur.fetchone()
        if not row: return None
        cols=[x[0] for x in cur.description]
        return dict(zip(cols,row))

# ---- drafts ----
def draft_save(user_id:int, payload:dict):
    with _conn() as c:
        c.execute("INSERT INTO drafts(user_id,payload,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
                  (user_id, json.dumps(payload, ensure_ascii=False), datetime.utcnow().isoformat()))

def draft_load(user_id:int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT payload FROM drafts WHERE user_id=?", (user_id,)).fetchone()
        if not row: return None
        try: return json.loads(row[0])
        except: return None

def draft_delete(user_id:int):
    with _conn() as c:
        c.execute("DELETE FROM drafts WHERE user_id=?", (user_id,))

# ---- PDF brief ----
def make_pdf_brief(request_id:int) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    req = get_request(request_id)
    if not req: raise ValueError("Request not found")
    pdf_path = BRIEFS_DIR / f"request_{request_id}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    x, y = 20*mm, 280*mm
    c.setFont("Helvetica-Bold", 16); c.drawString(x, y, f"NeuroFlex — Brief #{request_id}"); y -= 12*mm
    c.setFont("Helvetica", 11)
    def line(k,v):
        nonlocal y
        c.drawString(x, y, f"{k}: {v or ''}"); y -= 8*mm
    fields = [
      ("Created", req["created_at"]), ("Name", req["name"]), ("Company", req["company"]),
      ("Email", req["email"]), ("Contact", req["contact"]), ("Type", req["req_type"]),
      ("Budget", req["budget"]), ("AI Data", req.get("ai_data")), ("AI Dataset", req.get("ai_dataset")),
      ("Web Auth", req.get("web_auth")), ("Web Integrations", req.get("web_integrations")),
      ("Description", req["description"])
    ]
    for k,v in fields: line(k,v)
    c.showPage(); c.save()
    return str(pdf_path)
