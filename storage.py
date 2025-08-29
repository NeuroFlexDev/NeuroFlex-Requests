import sqlite3, json, pandas as pd, shutil, os
from pathlib import Path
from datetime import datetime
from config import settings, BASE_DIR

DB_PATH = settings.DB_PATH
FILES_ROOT = Path(BASE_DIR) / "data" / "files"
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
FILES_ROOT.mkdir(parents=True, exist_ok=True)

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
  budget TEXT
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
"""

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.executescript(DDL)
    return c

def save_request(d: dict) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO requests(created_at,lang,name,company,email,contact,req_type,description,budget)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (datetime.utcnow().isoformat(), d.get("lang"), d["name"], d.get("company"),
             d["email"], d["contact"], d["req_type"], d["description"], d.get("budget"))
        )
        return cur.lastrowid

def save_temp_attachment(user_id:int, *, file_id:str, file_name:str|None,
                         mime_type:str|None, file_size:int|None, local_path:str|None)->int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO attachments(request_id,user_id,file_id,file_name,mime_type,file_size,local_path,created_at)"
            " VALUES(NULL,?,?,?,?,?,?,?)",
            (user_id, file_id, file_name, mime_type, file_size, local_path, datetime.utcnow().isoformat())
        )
        return cur.lastrowid

def link_user_files_to_request(user_id:int, request_id:int):
    dest_dir = FILES_ROOT / f"request_{request_id}"
    dest_dir.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        rows = c.execute("SELECT id, local_path, file_name FROM attachments WHERE user_id=? AND request_id IS NULL",
                         (user_id,)).fetchall()
        for att_id, local_path, file_name in rows:
            if local_path and os.path.exists(local_path):
                new_path = dest_dir / (Path(local_path).name if not file_name else file_name)
                shutil.move(local_path, new_path)
                c.execute("UPDATE attachments SET request_id=?, local_path=? WHERE id=?",
                          (request_id, str(new_path), att_id))
            else:
                c.execute("UPDATE attachments SET request_id=? WHERE id=?", (request_id, att_id))

def list_attachments_by_request(request_id:int)->list[dict]:
    with _conn() as c:
        cur = c.execute("SELECT id,file_name,mime_type,file_size,local_path FROM attachments WHERE request_id=? ORDER BY id",
                        (request_id,))
        cols = [x[0] for x in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

def export_csv(path: str) -> str:
    with _conn() as c:
        df = pd.read_sql_query("SELECT * FROM requests ORDER BY id DESC", c)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path

def export_json(path: str) -> str:
    with _conn() as c:
        cur = c.execute("SELECT * FROM requests ORDER BY id DESC")
        rows = [dict(zip([col[0] for col in cur.description], r)) for r in cur.fetchall()]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return path

def stats() -> dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
        by_type = dict(c.execute("SELECT req_type, COUNT(*) FROM requests GROUP BY req_type").fetchall())
    return {"total": total, "by_type": by_type}
