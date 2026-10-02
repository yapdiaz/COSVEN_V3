from pathlib import Path
from datetime import date, timedelta, datetime
import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time

from cosven_store import PROCESO_DIR, importar_detalle, copiar_historico, DB_PATH

ROOT = Path(r"C:\Paykan\COSVEN_V3")
APP = ROOT / "app"
CACHE_DIR = ROOT / "cache"
SNAPSHOT_DIR = CACHE_DIR / "snapshot_actual"
LOG_DIR = ROOT / "logs"
LOCK_PATH = CACHE_DIR / "actualizacion.lock"
FUENTE = Path(r"\\Paykans\c\paykann\libres")

CACHE_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_FILES = [
    "ARTICULO.DBF",
    "FLIASNEW.DBF",
    "CLIENTES.DBF",
    "MOVART.DBF",
    "HISVTA.DBF",
    "PEDIDOS.DBF",
    "USUARIOS.DBF",
    "MO180709.DBF",
    "PEDCOM.DBF",
    "ARTCOM.DBF",
]


def parse_args():
    p = argparse.ArgumentParser(
        description="ActualizaciÃ³n incremental del mes abierto de COSVEN."
    )
    p.add_argument(
        "--modo",
        choices=["cierre", "intradia"],
        default="cierre",
        help="cierre=hasta ayer; intradia=incluye hoy.",
    )
    p.add_argument(
        "--origen",
        default="manual",
        help="Texto informativo: programada-0500, programada-1300 o manual.",
    )
    return p.parse_args()


def set_meta(clave, valor):
    if not DB_PATH.exists():
        return
    con = sqlite3.connect(DB_PATH, timeout=30)
    try:
        con.execute(
            """
            INSERT INTO metadata(clave, valor) VALUES (?, ?)
            ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor
            """,
            (clave, str(valor)),
        )
        con.commit()
    finally:
        con.close()


def set_estado(estado, origen, **otros):
    set_meta("actualizacion_estado", estado)
    set_meta("actualizacion_origen", origen)
    for k, v in otros.items():
        set_meta(k, v)


def lock_activo():
    if not LOCK_PATH.exists():
        return False

    # Un lock de mÃ¡s de 4 horas se considera huÃ©rfano de una ejecuciÃ³n fallida.
    try:
        edad = time.time() - LOCK_PATH.stat().st_mtime
    except OSError:
        edad = 0

    if edad > 4 * 3600:
        try:
            LOCK_PATH.unlink()
            return False
        except OSError:
            return True

    return True


def adquirir_lock(origen):
    if lock_activo():
        return False

    try:
        fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False

    datos = {
        "pid": os.getpid(),
        "inicio": datetime.now().isoformat(timespec="seconds"),
        "origen": origen,
    }
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)

    return True


def liberar_lock():
    try:
        LOCK_PATH.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        pass


def ejecutar(cmd, log, env=None):
    log.write("\n> " + " ".join(map(str, cmd)) + "\n")
    log.flush()

    p = subprocess.run(
        [str(x) for x in cmd],
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    if p.returncode != 0:
        raise RuntimeError(
            f"FallÃ³ un subproceso con cÃ³digo {p.returncode}. Revisar {log.name}"
        )


def snapshot(log):
    log.write("\n--- SNAPSHOT LOCAL DE DBF OPERATIVOS ---\n")
    log.flush()

    for nombre in SNAPSHOT_FILES:
        src = FUENTE / nombre
        dst = SNAPSHOT_DIR / nombre

        if not src.exists():
            raise FileNotFoundError(f"No existe {src}")

        t0 = time.time()
        shutil.copy2(src, dst)
        mb = dst.stat().st_size / 1024 / 1024
        log.write(
            f"{nombre}: {mb:,.1f} MB copiados en {time.time() - t0:,.1f} s\n"
        )
        log.flush()


def periodo_objetivo(modo):
    hoy = date.today()

    if modo == "intradia":
        hasta = hoy
    else:
        hasta = hoy - timedelta(days=1)

    desde = hasta.replace(day=1)
    return desde, hasta


def main():
    args = parse_args()

    if not adquirir_lock(args.origen):
        print("Ya existe una actualizaciÃ³n COSVEN en curso.")
        print("No se iniciÃ³ una segunda ejecuciÃ³n.")
        return 10

    desde, hasta = periodo_objetivo(args.modo)
    inicio = datetime.now()

    log_path = LOG_DIR / f"actualizacion_{inicio:%Y%m%d}.log"

    set_estado(
        "EN_CURSO",
        args.origen,
        actualizacion_inicio=inicio.isoformat(timespec="seconds"),
        actualizacion_desde=desde.isoformat(),
        actualizacion_hasta_objetivo=hasta.isoformat(),
    )

    try:
        with log_path.open("a", encoding="utf-8") as log:
            log.write("\n" + "=" * 78 + "\n")
            log.write(f"Inicio: {inicio:%Y-%m-%d %H:%M:%S}\n")
            log.write(f"Origen: {args.origen}\n")
            log.write(f"Modo: {args.modo}\n")
            log.write(f"PerÃ­odo abierto a reconstruir: {desde} - {hasta}\n")
            log.write("HistÃ³rico de meses cerrados: NO SE TOCA.\n")
            log.flush()

            # Detecta artÃ­culos nuevos. SÃ³lo recorrerÃ¡ MOVAANT si realmente falta
            # algÃºn artÃ­culo en la cache histÃ³rica existente.
            ejecutar(
                [
                    sys.executable,
                    APP / "preparar_cache_historica.py",
                    "--desde", desde.isoformat(),
                    "--hasta", hasta.isoformat(),
                ],
                log,
            )

            # Copia DBF operativos a local para que el cÃ¡lculo pesado no recorra
            # PEDIDOS/HISVTA/MOVART permanentemente por red.
            snapshot(log)

            env = os.environ.copy()
            env["COSVEN_DBF_BASE"] = str(SNAPSHOT_DIR)

            ejecutar(
                [
                    sys.executable,
                    APP / "cosven_periodo.py",
                    "--desde", desde.isoformat(),
                    "--hasta", hasta.isoformat(),
                    "--salida-dir", PROCESO_DIR,
                ],
                log,
                env=env,
            )

            detalle = PROCESO_DIR / "cosven_detalle.csv"
            n = importar_detalle(detalle, desde, hasta)
            hist = copiar_historico(detalle, desde)

            fin = datetime.now()
            duracion = (fin - inicio).total_seconds()

            log.write(f"\nFilas importadas: {n:,}\n")
            log.write(f"SQLite: {DB_PATH}\n")
            log.write(f"Copia mensual: {hist}\n")
            log.write(f"Fin: {fin:%Y-%m-%d %H:%M:%S}\n")
            log.write(f"DuraciÃ³n: {duracion:,.1f} segundos\n")
            log.flush()

        set_estado(
            "OK",
            args.origen,
            actualizacion_fin=fin.isoformat(timespec="seconds"),
            actualizacion_duracion_seg=f"{duracion:.1f}",
            datos_hasta=hasta.isoformat(),
            actualizacion_error="",
        )

        print(f"ActualizaciÃ³n finalizada: {desde} - {hasta}")
        print(f"Filas importadas: {n:,}")
        print("Base local:", DB_PATH)
        print("Log:", log_path)
        return 0

    except Exception as exc:
        fin = datetime.now()
        set_estado(
            "ERROR",
            args.origen,
            actualizacion_fin=fin.isoformat(timespec="seconds"),
            actualizacion_error=str(exc)[:500],
        )

        try:
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"\nERROR: {type(exc).__name__}: {exc}\n")
                log.write(f"Fin con error: {fin:%Y-%m-%d %H:%M:%S}\n")
        except Exception:
            pass

        print(f"ERROR: {exc}")
        return 1

    finally:
        liberar_lock()


if __name__ == "__main__":
    raise SystemExit(main())

