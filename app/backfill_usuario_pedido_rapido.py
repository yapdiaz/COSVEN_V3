from pathlib import Path
from decimal import Decimal
from datetime import datetime
import sqlite3
import shutil
import time

from dbfread import DBF, FieldParser

ROOT = Path(r"C:\Paykan\COSVEN_V3")
DB_PATH = ROOT / "data" / "cosven.db"
FUENTE = Path(r"\\Paykans\c\paykann\libres")
CACHE = ROOT / "cache" / "usuario_pedido"
LOG_DIR = ROOT / "logs"

CACHE.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

PEDIDOS_SRC = FUENTE / "PEDIDOS.DBF"
USUARIOS_SRC = FUENTE / "USUARIOS.DBF"
PEDIDOS_LOCAL = CACHE / "PEDIDOS.DBF"
USUARIOS_LOCAL = CACHE / "USUARIOS.DBF"


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


def copiar_local(src, dst):
    if not src.exists():
        raise FileNotFoundError(f"No existe: {src}")

    print(f"Copiando {src.name} a cache local...", flush=True)
    t0 = time.time()
    shutil.copy2(src, dst)
    mb = dst.stat().st_size / 1024 / 1024
    print(f"  OK: {mb:,.1f} MB en {time.time()-t0:,.1f} s", flush=True)


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"No existe la base local: {DB_PATH}")

    print("=" * 72, flush=True)
    print("BACKFILL RAPIDO - USUARIO QUE HIZO EL PEDIDO", flush=True)
    print("=" * 72, flush=True)
    print("Los DBF de Paykan se copian primero a cache local y luego se leen allÃ­.", flush=True)
    print("No se modifica ningÃºn DBF fuente.", flush=True)
    print("", flush=True)

    # Copiar una sola vez para que el recorrido no se haga sobre la red.
    copiar_local(USUARIOS_SRC, USUARIOS_LOCAL)
    copiar_local(PEDIDOS_SRC, PEDIDOS_LOCAL)

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
                """
                SELECT DISTINCT pedido
                FROM cosven_detalle
                WHERE pedido IS NOT NULL AND pedido > 0
                """
            ).fetchall()
        }

        print(f"Pedidos distintos a resolver: {len(pedidos_necesarios):,}", flush=True)

        usuarios = {}
        udb = DBF(
            USUARIOS_LOCAL,
            encoding="latin1",
            load=False,
            char_decode_errors="ignore",
            parserclass=ParserTolerante,
        )

        for r in udb:
            ncla = entero(r.get("NCLA"))
            if ncla > 0 and ncla not in usuarios:
                usuarios[ncla] = texto(r.get("USUARIO"))

        print(f"Usuarios cargados: {len(usuarios):,}", flush=True)

        usuario_por_pedido = {}
        pdb = DBF(
            PEDIDOS_LOCAL,
            encoding="latin1",
            load=False,
            char_decode_errors="ignore",
            parserclass=ParserTolerante,
        )

        total_registros = len(pdb)
        print(f"Registros PEDIDOS.DBF: {total_registros:,}", flush=True)
        print("Buscando pedidos requeridos...", flush=True)

        t0 = time.time()

        for i, r in enumerate(pdb, 1):
            ped = entero(r.get("PED"))

            if ped in pedidos_necesarios and ped not in usuario_por_pedido:
                claing = entero(r.get("CLAING"))
                usuario_por_pedido[ped] = usuarios.get(claing, "")

                if len(usuario_por_pedido) >= len(pedidos_necesarios):
                    print(f"  Todos los pedidos fueron encontrados en registro {i:,}.", flush=True)
                    break

            if i % 50000 == 0:
                pct = (i / total_registros * 100) if total_registros else 0
                print(
                    f"  {i:,}/{total_registros:,} ({pct:,.1f}%) | "
                    f"Pedidos encontrados: {len(usuario_por_pedido):,}/{len(pedidos_necesarios):,}",
                    flush=True
                )

        print(
            f"Recorrido terminado en {time.time()-t0:,.1f} s. "
            f"Pedidos encontrados: {len(usuario_por_pedido):,}",
            flush=True
        )

        # Un Ãºnico UPDATE masivo local.
        print("Actualizando cosven.db...", flush=True)
        con.execute("BEGIN IMMEDIATE")

        # Vaciar primero el usuario previo para que no queden datos del criterio anterior.
        con.execute("UPDATE cosven_detalle SET usuario = ''")

        cambios = [
            (usuario, ped)
            for ped, usuario in usuario_por_pedido.items()
        ]

        con.executemany(
            "UPDATE cosven_detalle SET usuario = ? WHERE pedido = ?",
            cambios,
        )

        con.execute(
            """
            INSERT INTO metadata(clave, valor)
            VALUES('usuario_pedido_backfill', ?)
            ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """,
            (datetime.now().isoformat(timespec="seconds"),),
        )

        con.commit()

        total = con.execute("SELECT COUNT(*) FROM cosven_detalle").fetchone()[0]
        con_usuario = con.execute(
            """
            SELECT COUNT(*)
            FROM cosven_detalle
            WHERE TRIM(COALESCE(usuario,'')) <> ''
            """
        ).fetchone()[0]

        print("", flush=True)
        print("=" * 72, flush=True)
        print("FINALIZADO", flush=True)
        print(f"Filas de detalle: {total:,}", flush=True)
        print(f"Filas con usuario de pedido: {con_usuario:,}", flush=True)
        print(
            "Fuente: PEDIDOS.CLAING -> USUARIOS.NCLA -> USUARIOS.USUARIO",
            flush=True
        )
        print("DBF fuente: SOLO LECTURA.", flush=True)

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()

