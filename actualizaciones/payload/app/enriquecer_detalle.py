from pathlib import Path
from datetime import date, datetime
from collections import defaultdict, deque
from decimal import Decimal
import sqlite3

from dbfread import DBF, FieldParser

ROOT = Path(r"C:\Paykan\COSVEN")
DB_PATH = ROOT / "data" / "cosven.db"
BASE = Path(r"\\Paykans\c\paykann\libres")
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class ParserTolerante(FieldParser):
    def parseN(self, field, data):
        try:
            return super().parseN(field, data)
        except Exception:
            return None

    def parseD(self, field, data):
        try:
            return super().parseD(field, data)
        except Exception:
            return None


def key7_local(familia, articulo):
    try:
        return str(int(familia)).rjust(3) + str(int(articulo)).rjust(4)
    except Exception:
        return ""


def key7_dbf(v):
    if isinstance(v, bytes):
        s = v.decode("latin1", errors="ignore")
    else:
        s = str(v or "")
    return s[:7].ljust(7)


def txt(v):
    return str(v or "").strip()


def entero(v):
    try:
        return int(Decimal(str(v or "").strip() or "0"))
    except Exception:
        return 0


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"No existe la base local: {DB_PATH}")

    log_path = LOG_DIR / f"enriquecer_detalle_{datetime.now():%Y%m%d_%H%M%S}.log"

    con = sqlite3.connect(DB_PATH, timeout=60)
    try:
        con.execute("PRAGMA journal_mode=WAL")

        columnas = {
            str(r[1]).lower()
            for r in con.execute("PRAGMA table_info(cosven_detalle)").fetchall()
        }

        if "descuento" not in columnas:
            con.execute("ALTER TABLE cosven_detalle ADD COLUMN descuento REAL DEFAULT 0")
        if "claing" not in columnas:
            con.execute("ALTER TABLE cosven_detalle ADD COLUMN claing INTEGER DEFAULT 0")
        if "usuario" not in columnas:
            con.execute("ALTER TABLE cosven_detalle ADD COLUMN usuario TEXT DEFAULT ''")
        con.commit()

        filas = con.execute(
            """
            SELECT id, familia, articulo, tm, documento, cliente, fecha
            FROM cosven_detalle
            ORDER BY id
            """
        ).fetchall()

        if not filas:
            print("La base local no tiene detalle para enriquecer.")
            return

        claves_locales = defaultdict(deque)
        for rid, fam, art, tm, doc, cli, fecha in filas:
            k = (
                str(tm or "").strip(),
                int(doc or 0),
                int(cli or 0),
                str(fecha or ""),
                key7_local(fam, art),
            )
            claves_locales[k].append(rid)

        claves_pendientes = set(claves_locales.keys())

        # Fuente exacta del descuento y del usuario:
        # MOVART.DTO
        # MOVART.CLAING -> USUARIOS.NCLA -> USUARIOS.USUARIO
        usuarios = {}
        udb = DBF(
            BASE / "USUARIOS.DBF",
            encoding="latin1",
            load=False,
            char_decode_errors="ignore",
            parserclass=ParserTolerante,
        )

        for r in udb:
            ncla = entero(r.get("NCLA"))
            if ncla <= 0 or ncla in usuarios:
                continue
            usuarios[ncla] = txt(r.get("USUARIO"))

        actualizaciones = []
        encontrados = 0

        mdb = DBF(
            BASE / "MOVART.DBF",
            encoding="latin1",
            load=False,
            char_decode_errors="ignore",
            parserclass=ParserTolerante,
        )

        for r in mdb:
            fecha = r.get("FECHA")
            if not fecha:
                continue

            k = (
                txt(r.get("TM")),
                entero(r.get("DOC")),
                entero(r.get("CLI")),
                fecha.isoformat() if hasattr(fecha, "isoformat") else str(fecha),
                key7_dbf(r.get("ART")),
            )

            ids = claves_locales.get(k)
            if not ids:
                continue

            rid = ids.popleft()
            dto = float(r.get("DTO") or 0)
            claing = entero(r.get("CLAING"))
            usuario = usuarios.get(claing, "")

            actualizaciones.append((dto, claing, usuario, rid))
            encontrados += 1

            if not ids:
                claves_pendientes.discard(k)

        con.execute("BEGIN IMMEDIATE")
        con.executemany(
            """
            UPDATE cosven_detalle
            SET descuento = ?, claing = ?, usuario = ?
            WHERE id = ?
            """,
            actualizaciones,
        )
        con.execute(
            """
            INSERT INTO metadata(clave, valor) VALUES('detalle_descuento_usuario', ?)
            ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """,
            (datetime.now().isoformat(timespec="seconds"),),
        )
        con.commit()

        total = len(filas)
        faltantes = total - encontrados

        with log_path.open("w", encoding="utf-8") as log:
            log.write(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            log.write(f"Base local: {DB_PATH}\n")
            log.write(f"Fuente DBF: {BASE}\n")
            log.write(f"Filas SQLite: {total}\n")
            log.write(f"Filas enriquecidas: {encontrados}\n")
            log.write(f"Filas sin match exacto: {faltantes}\n")
            log.write("DBF fuente: solo lectura.\n")

        print(f"Filas locales: {total:,}")
        print(f"Enriquecidas: {encontrados:,}")
        print(f"Sin match exacto: {faltantes:,}")
        print("Log:", log_path)

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
