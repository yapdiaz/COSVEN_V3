from pathlib import Path
from datetime import datetime, date
import csv
import sqlite3

ROOT = Path(r"C:\Paykan\COSVEN")
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "cosven.db"
HIST_DIR = DATA_DIR / "historico"
PROCESO_DIR = DATA_DIR / "proceso"

DATA_DIR.mkdir(parents=True, exist_ok=True)
HIST_DIR.mkdir(parents=True, exist_ok=True)
PROCESO_DIR.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS cosven_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    familia INTEGER NOT NULL,
    articulo INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    familia_new INTEGER,
    familia_desc TEXT,
    fecha TEXT NOT NULL,
    cliente INTEGER,
    nombre_cliente TEXT,
    pedido INTEGER,
    vrll TEXT,
    tipo_pedido TEXT,
    tm TEXT,
    documento INTEGER,
    cantidad REAL,
    bonificacion REAL,
    costo REAL,
    venta REAL,
    utilidad REAL,
    putil REAL,
    iva REAL
);

CREATE INDEX IF NOT EXISTS ix_cosven_fecha ON cosven_detalle(fecha);
CREATE INDEX IF NOT EXISTS ix_cosven_art ON cosven_detalle(familia, articulo);
CREATE INDEX IF NOT EXISTS ix_cosven_cliente ON cosven_detalle(cliente);
CREATE INDEX IF NOT EXISTS ix_cosven_tipo ON cosven_detalle(tipo_pedido);

CREATE TABLE IF NOT EXISTS metadata (
    clave TEXT PRIMARY KEY,
    valor TEXT
);
"""


def _int(v):
    s = str(v or "").strip()
    if not s:
        return 0
    try:
        return int(float(s.replace(",", ".")))
    except Exception:
        return 0


def _float(v):
    s = str(v or "").strip()
    if not s:
        return 0.0
    try:
        return float(s.replace(",", "."))
    except Exception:
        return 0.0


def conectar():
    con = sqlite3.connect(DB_PATH, timeout=60)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(SCHEMA)
    return con


def set_meta(con, clave, valor):
    con.execute(
        "INSERT INTO metadata(clave, valor) VALUES (?, ?) "
        "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
        (clave, str(valor)),
    )


def importar_detalle(csv_path: Path, desde: date, hasta: date):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    filas = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=";")
        for x in r:
            fecha = str(x.get("FECHA") or "").strip()
            if not fecha:
                continue
            filas.append((
                _int(x.get("XFLIA")),
                _int(x.get("XART")),
                str(x.get("DET") or "").strip(),
                _int(x.get("FLIANEW")),
                str(x.get("FAMILIA_DESC") or x.get("FLIAD4") or "").strip(),
                fecha,
                _int(x.get("CLI")),
                str(x.get("NOM") or "").strip(),
                _int(x.get("PED")),
                str(x.get("VRLL") or "").strip(),
                str(x.get("TIPO_PEDIDO") or "").strip(),
                str(x.get("TM") or "").strip(),
                _int(x.get("DOC")),
                _float(x.get("CANT")),
                _float(x.get("BONI")),
                _float(x.get("COSTO")),
                _float(x.get("IMP")),
                _float(x.get("UTILIDAD")),
                _float(x.get("PUTIL")),
                _float(x.get("IVA")),
            ))

    con = conectar()
    try:
        con.execute("BEGIN IMMEDIATE")
        con.execute(
            "DELETE FROM cosven_detalle WHERE fecha BETWEEN ? AND ?",
            (desde.isoformat(), hasta.isoformat()),
        )
        con.executemany(
            """
            INSERT INTO cosven_detalle (
                familia, articulo, descripcion, familia_new, familia_desc, fecha,
                cliente, nombre_cliente, pedido, vrll, tipo_pedido, tm, documento,
                cantidad, bonificacion, costo, venta, utilidad, putil, iva
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            filas,
        )
        set_meta(con, "ultima_actualizacion", datetime.now().isoformat(timespec="seconds"))
        set_meta(con, "ultimo_desde", desde.isoformat())
        set_meta(con, "ultimo_hasta", hasta.isoformat())
        set_meta(con, "ultima_cantidad", len(filas))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    return len(filas)


def copiar_historico(csv_path: Path, desde: date):
    import shutil
    destino = HIST_DIR / f"cosven_{desde:%Y-%m}.csv"
    shutil.copy2(csv_path, destino)
    return destino
