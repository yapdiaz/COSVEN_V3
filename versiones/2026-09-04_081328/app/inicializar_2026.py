from pathlib import Path
from datetime import date, timedelta, datetime
import calendar
import subprocess
import sys

from cosven_store import PROCESO_DIR, importar_detalle, copiar_historico, DB_PATH

ROOT = Path(r"C:\Paykan\COSVEN")
APP = ROOT / "app"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
VALIDATION_FLAG = ROOT / "data" / "motor_validado_2026-08.ok"


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
        raise SystemExit(f"Falló la inicialización. Revisar {log.name}")


def meses(desde, hasta):
    y, m = desde.year, desde.month
    while (y, m) <= (hasta.year, hasta.month):
        ini = date(y, m, 1)
        fin = date(y, m, calendar.monthrange(y, m)[1])
        if ini < desde:
            ini = desde
        if fin > hasta:
            fin = hasta
        yield ini, fin
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1


def main():
    if not VALIDATION_FLAG.exists():
        raise SystemExit(
            "No se inicia la carga 2026 porque el motor por período todavía no fue validado. "
            "Ejecute primero validar_agosto.bat y continúe solo si informa VALIDACION OK."
        )

    hoy = date.today()
    hasta = hoy - timedelta(days=1)
    desde = date(2026, 1, 1)

    if hasta < desde:
        raise SystemExit("Todavía no existe período 2026 para inicializar.")

    log_path = LOG_DIR / f"inicializacion_2026_{hoy:%Y%m%d}.log"
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n" + "=" * 70 + "\n")
        log.write(f"Inicio: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
        log.write(f"Carga inicial: {desde} - {hasta}\n")

        # Una única preparación histórica para todos los artículos vendidos en 2026.
        ejecutar(
            [
                sys.executable,
                APP / "preparar_cache_historica.py",
                "--desde", desde.isoformat(),
                "--hasta", hasta.isoformat(),
            ],
            log,
        )

        for ini, fin in meses(desde, hasta):
            log.write(f"\n--- MES {ini:%Y-%m}: {ini} - {fin} ---\n")
            ejecutar(
                [
                    sys.executable,
                    APP / "cosven_periodo.py",
                    "--desde", ini.isoformat(),
                    "--hasta", fin.isoformat(),
                    "--salida-dir", PROCESO_DIR,
                ],
                log,
            )

            detalle = PROCESO_DIR / "cosven_detalle.csv"
            n = importar_detalle(detalle, ini, fin)
            hist = copiar_historico(detalle, ini)
            log.write(f"Filas importadas: {n:,}\n")
            log.write(f"Copia mensual: {hist}\n")

        log.write(f"SQLite: {DB_PATH}\n")
        log.write(f"Fin: {datetime.now():%Y-%m-%d %H:%M:%S}\n")

    print("Carga inicial 2026 finalizada.")
    print("Base local:", DB_PATH)
    print("Log:", log_path)


if __name__ == "__main__":
    main()
