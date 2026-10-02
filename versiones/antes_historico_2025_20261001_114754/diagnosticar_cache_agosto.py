from pathlib import Path
import pickle
from decimal import Decimal

ROOT = Path(r"C:\Paykan\COSVEN")
CACHE = ROOT / "cache"

OLD_HIST_CANDIDATES = [
    CACHE / "cosven_historico.pkl",
    Path(r"C:\temp\cosven_historico.pkl"),
]
OLD_CS_CANDIDATES = [
    CACHE / "cosven_ultcoscs.pkl",
    Path(r"C:\temp\cosven_ultcoscs.pkl"),
]

NEW_HIST = CACHE / "cosven_historico_2026.pkl"
REPORT = ROOT / "logs" / "diagnostico_cache_agosto.txt"
REPORT.parent.mkdir(parents=True, exist_ok=True)


def D(v):
    if v is None:
        return Decimal("0")
    s = str(v).strip()
    return Decimal(s) if s else Decimal("0")


def key7(v):
    return str(v or "")[:7].ljust(7)


def first_existing(candidates):
    for p in candidates:
        if p.exists():
            return p
    return None


def mov_value(v):
    if isinstance(v, dict):
        return D(v.get("MOVIMIENTO", 0))
    return D(v)


def ultcs_value(v):
    if not isinstance(v, dict):
        return None
    x = v.get("ULTCS")
    if not x:
        return None
    return (
        x.get("FECHA"),
        int(x.get("SEQ", 0)),
        D(x.get("COSTO", 0)),
    )


def main():
    old_hist_path = first_existing(OLD_HIST_CANDIDATES)
    old_cs_path = first_existing(OLD_CS_CANDIDATES)

    lines = []

    if old_hist_path is None:
        lines.append("ERROR: no se encontró el cache histórico validado anterior.")
        lines.append("Buscado en:")
        for p in OLD_HIST_CANDIDATES:
            lines.append(f"  - {p}")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print("\n".join(lines))
        raise SystemExit(2)

    if not NEW_HIST.exists():
        lines.append(f"ERROR: no existe el cache nuevo: {NEW_HIST}")
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print("\n".join(lines))
        raise SystemExit(2)

    with old_hist_path.open("rb") as f:
        old = pickle.load(f)

    with NEW_HIST.open("rb") as f:
        new = pickle.load(f)

    old_mov = {key7(k): v for k, v in old.get("movaant", {}).items()}
    new_mov = {key7(k): v for k, v in new.get("movaant", {}).items()}

    common = sorted(set(old_mov) & set(new_mov))
    only_old = sorted(set(old_mov) - set(new_mov))
    only_new = sorted(set(new_mov) - set(old_mov))

    dif_mov = []
    for k in common:
        a = mov_value(old_mov[k])
        b = mov_value(new_mov[k])
        if a != b:
            dif_mov.append((k, a, b, b - a))

    lines.append("DIAGNOSTICO CACHE COSVEN AGOSTO 2026")
    lines.append("=" * 72)
    lines.append(f"Cache validado anterior: {old_hist_path}")
    lines.append(f"Cache nuevo:             {NEW_HIST}")
    lines.append("")
    lines.append(f"Artículos cache anterior: {len(old_mov):,}")
    lines.append(f"Artículos cache nuevo:    {len(new_mov):,}")
    lines.append(f"Artículos comunes:        {len(common):,}")
    lines.append(f"Solo anterior:            {len(only_old):,}")
    lines.append(f"Solo nuevo:               {len(only_new):,}")
    lines.append(f"MOVIMIENTO distintos:     {len(dif_mov):,}")
    lines.append("")

    if dif_mov:
        lines.append("PRIMERAS 100 DIFERENCIAS DE MOVIMIENTO HISTORICO")
        lines.append("ARTKEY | ANTERIOR | NUEVO | DIFERENCIA")
        for k, a, b, d in dif_mov[:100]:
            lines.append(f"{k!r} | {a} | {b} | {d}")
    else:
        lines.append("MOVIMIENTO histórico: SIN DIFERENCIAS.")

    # Comparación ULTCS si existe cache antiguo separado.
    lines.append("")
    lines.append("=" * 72)
    lines.append("ULTCS")
    if old_cs_path is None:
        lines.append("No se encontró cosven_ultcoscs.pkl anterior; no se compara ULTCS.")
    else:
        with old_cs_path.open("rb") as f:
            oldcs = pickle.load(f)
        old_cs = {key7(k): v for k, v in oldcs.get("movaant", {}).items()}
        new_cs = {key7(k): ultcs_value(v) for k, v in new_mov.items()}

        dif_cs = []
        keys_cs = sorted(set(old_cs) | set(new_cs))
        for k in keys_cs:
            a0 = old_cs.get(k)
            if isinstance(a0, dict):
                a = (
                    a0.get("FECHA"),
                    int(a0.get("SEQ", 0)),
                    D(a0.get("COSTO", 0)),
                )
            else:
                a = None
            b = new_cs.get(k)
            if a != b:
                dif_cs.append((k, a, b))

        lines.append(f"Cache ULTCS anterior: {old_cs_path}")
        lines.append(f"ULTCS distintos:      {len(dif_cs):,}")
        if dif_cs:
            lines.append("PRIMERAS 100 DIFERENCIAS ULTCS")
            for k, a, b in dif_cs[:100]:
                lines.append(f"{k!r} | ANTERIOR={a} | NUEVO={b}")
        else:
            lines.append("ULTCS: SIN DIFERENCIAS.")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines[:35]))
    print("")
    print("Reporte completo:", REPORT)


if __name__ == "__main__":
    main()
