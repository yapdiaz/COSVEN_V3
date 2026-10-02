from pathlib import Path
from decimal import Decimal
from datetime import datetime
import sqlite3

from dbfread import DBF, FieldParser

ROOT = Path(r"C:\Paykan\COSVEN_V3")
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


def entero(v):
    try:
        return int(Decimal(str(v or "").strip() or "0"))
    except Exception:
        return 0


def texto(v):
    return str(v or "").strip()


def main():
    con = sqlite3.connect(DB_PATH, timeout=60)

    try:
        columnas = {
            str(r[1]).lower()
            for r in con.execute("PRAGMA table_info(cosven_detalle)").fetchall()
        }

        if "usuario" not in columnas:
            con.execute("ALTER TABLE cosven_detalle ADD COLUMN usuario TEXT DEFAULT ''")
            con.commit()

        pedidos_necesarios = {
            int(r[0])
            for r in con.execute(
                "SELECT DISTINCT pedido FROM cosven_detalle WHERE pedido IS NOT NULL AND pedido > 0"
            ).fetchall()
        }

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
            if ncla > 0 and ncla not in usuarios:
                usuarios[ncla] = texto(r.get("USUARIO"))

        usuario_por_pedido = {}
        pdb = DBF(
            BASE / "PEDIDOS.DBF",
            encoding="latin1",
            load=False,
            char_decode_errors="ignore",
            parserclass=ParserTolerante,
        )

        for r in pdb:
            ped = entero(r.get("PED"))
            if ped not in pedidos_necesarios:
                continue

            claing = entero(r.get("CLAING"))
            usuario_por_pedido[ped] = usuarios.get(claing, "")

            if len(usuario_por_pedido) >= len(pedidos_necesarios):
                break

        cambios = [
            (usuario, ped)
            for ped, usuario in usuario_por_pedido.items()
        ]

        con.execute("BEGIN IMMEDIATE")
        con.executemany(
            "UPDATE cosven_detalle SET usuario = ? WHERE pedido = ?",
            cambios,
        )
        con.execute(
            """
            INSERT INTO metadata(clave, valor) VALUES('usuario_pedido_backfill', ?)
            ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """,
            (datetime.now().isoformat(timespec="seconds"),),
        )
        con.commit()

        con_usuario = con.execute(
            "SELECT COUNT(*) FROM cosven_detalle WHERE TRIM(COALESCE(usuario,'')) <> ''"
        ).fetchone()[0]
        total = con.execute("SELECT COUNT(*) FROM cosven_detalle").fetchone()[0]

        print(f"Pedidos distintos requeridos: {len(pedidos_necesarios):,}")
        print(f"Pedidos encontrados: {len(usuario_por_pedido):,}")
        print(f"Filas con usuario de pedido: {con_usuario:,} de {total:,}")
        print("Fuente: PEDIDOS.CLAING -> USUARIOS.NCLA -> USUARIOS.USUARIO")
        print("DBF fuente: sÃ³lo lectura.")

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()

