from pathlib import Path
from decimal import Decimal
import csv
import sys

ROOT = Path(r"C:\Paykan\COSVEN")
BASELINE = ROOT / "data" / "cosven_exacto_total.csv"
NUEVO = ROOT / "data" / "validacion_agosto" / "cosven_total.csv"
VALIDATION_FLAG = ROOT / "data" / "motor_validado_2026-08.ok"

KEY = ("XFLIA", "XART")
NUM = ("CANT", "BONI", "COSTO", "IMP", "UTILIDAD", "PUTIL")


def D(v):
    s = str(v or "").strip().replace(",", ".")
    return Decimal(s) if s else Decimal("0")


def cargar(path):
    data = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=";")
        for x in r:
            k = (str(x["XFLIA"]).strip(), str(x["XART"]).strip())
            data[k] = {c: D(x.get(c)) for c in NUM}
    return data


def main():
    if not BASELINE.exists():
        raise SystemExit(
            f"No existe el resultado base validado: {BASELINE}\n"
            "Conserve/copíe allí el cosven_exacto_total.csv validado de agosto antes de ejecutar esta comparación."
        )
    if not NUEVO.exists():
        raise SystemExit(f"No existe el resultado nuevo: {NUEVO}")

    a = cargar(BASELINE)
    b = cargar(NUEVO)
    keys = sorted(set(a) | set(b))
    dif = []
    for k in keys:
        if k not in a or k not in b:
            dif.append((k, "FILA", a.get(k), b.get(k)))
            continue
        for c in NUM:
            if a[k][c] != b[k][c]:
                dif.append((k, c, a[k][c], b[k][c]))

    print("Base validada:", len(a), "artículos")
    print("Motor nuevo:", len(b), "artículos")
    if not dif:
        from datetime import datetime
        VALIDATION_FLAG.write_text(
            "Motor por período validado contra agosto 2026: "
            + datetime.now().isoformat(timespec="seconds") + "\n",
            encoding="utf-8",
        )
        print("VALIDACION OK: resultados idénticos para agosto 2026.")
        print("Marca de validación:", VALIDATION_FLAG)
        return

    print("VALIDACION CON DIFERENCIAS:", len(dif))
    for x in dif[:50]:
        print(x)
    sys.exit(2)


if __name__ == "__main__":
    main()
