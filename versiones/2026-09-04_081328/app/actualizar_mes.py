from pathlib import Path
from datetime import date, timedelta, datetime
import subprocess
import sys

from cosven_store import PROCESO_DIR, importar_detalle, copiar_historico, DB_PATH

ROOT = Path(r"C:\Paykan\COSVEN")
APP = ROOT / "app"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def ejecutar(cmd, log):
    log.write("\n> " + " ".join(map(str, cmd)) + "\n")
    log.flush()
    p = subprocess.run(
        [str(x) for x in cmd],
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if p.returncode != 0:
        raise SystemExit(f"Falló el proceso. Revisar {log.name}")


def main():
    hoy = date.today()
    hasta = hoy - timedelta(days=1)
    desde = hasta.replace(day=1)

    log_path = LOG_DIR / f"actualizacion_{hoy:%Y%m%d}.log"
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n" + "=" * 70 + "\n")
        log.write(f"Inicio: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        log.write(f"Período a reconstruir: {desde} - {hasta}\n")

        # Solo amplía la cache si aparece un artículo que todavía no estaba.
        ejecutar(
            [
                sys.executable,
                APP / "preparar_cache_historica.py",
                "--desde", desde.isoformat(),
                "--hasta", hasta.isoformat(),
            ],
            log,
        )

        ejecutar(
            [
                sys.executable,
                APP / "cosven_periodo.py",
                "--desde", desde.isoformat(),
                "--hasta", hasta.isoformat(),
                "--salida-dir", PROCESO_DIR,
            ],
            log,
        )

        detalle = PROCESO_DIR / "cosven_detalle.csv"
        n = importar_detalle(detalle, desde, hasta)
        hist = copiar_historico(detalle, desde)

        log.write(f"Filas importadas: {n:,}\n")
        log.write(f"SQLite: {DB_PATH}\n")
        log.write(f"Copia mensual: {hist}\n")
        log.write(f"Fin: {datetime.now():%Y-%m-%d %H:%M:%S}\n")

    print(f"Actualización finalizada: {desde} - {hasta}")
    print("Base local:", DB_PATH)
    print("Log:", log_path)


if __name__ == "__main__":
    main()
