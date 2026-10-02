from pathlib import Path
from dbfread import DBF
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import argparse
import mmap
import pickle
import sqlite3
import struct

ROOT = Path(r"C:\Paykan\COSVEN_V3")
BASE = Path(r"\\Paykans\c\paykann\libres")
CACHE_DIR = ROOT / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "cosven_historico.pkl"
TEMP_DB = CACHE_DIR / "_movaant_cache_build.sqlite"


def D(v):
    if v is None:
        return Decimal("0")
    if isinstance(v, bytes):
        v = v.decode("ascii", errors="ignore")
    s = str(v).strip()
    return Decimal(s) if s else Decimal("0")


def rnd(v, dec=3):
    q = Decimal("1").scaleb(-dec)
    return D(v).quantize(q, rounding=ROUND_HALF_UP)


def key7(v):
    return str(v or "")[:7].ljust(7)


def blank(v):
    return str(v or "").strip() == ""


def parse_fecha(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def abrir(nombre):
    return DBF(
        BASE / nombre,
        encoding="latin1",
        load=False,
        char_decode_errors="ignore",
    )


def estructura_dbf(path):
    with path.open("rb") as f:
        h = f.read(32)
        registros = struct.unpack("<I", h[4:8])[0]
        header_len = struct.unpack("<H", h[8:10])[0]
        record_len = struct.unpack("<H", h[10:12])[0]
        campos = {}
        offset = 1
        while True:
            d = f.read(32)
            if not d or d[0] == 0x0D:
                break
            nombre = (
                d[0:11]
                .split(b"\x00", 1)[0]
                .decode("ascii", errors="ignore")
                .upper()
            )
            largo = d[16]
            campos[nombre] = (offset, largo)
            offset += largo
    return registros, header_len, record_len, campos


def sold_articles(desde, hasta):
    validos = set()
    eq_art = {}

    for r in abrir("ARTICULO.DBF"):
        if not blank(r.get("ELI")):
            continue
        k = key7(r.get("ART"))
        validos.add(k)
        eq = D(r.get("EQ"))
        if eq <= 0:
            eq = Decimal("1")
        eq_art[k] = eq

    vendidos = set()
    for r in abrir("MOVART.DBF"):
        fecha = r.get("FECHA")
        if not fecha or fecha < desde or fecha > hasta:
            continue
        k = key7(r.get("ART"))
        if k not in validos:
            continue
        if not blank(r.get("ELI")):
            continue
        if D(r.get("CLI")) <= 0:
            continue
        if str(r.get("MM") or "").strip() not in ("-", "+"):
            continue
        if D(r.get("CANT")) + D(r.get("BONI")) == 0:
            continue
        vendidos.add(k)

    return vendidos, eq_art


def raw_field(mm, pos, campos, nombre):
    ini, largo = campos[nombre]
    return mm[pos + ini : pos + ini + largo]


def raw_text(b, strip=True):
    s = b.decode("latin1", errors="ignore")
    return s.strip() if strip else s


def ymd_to_date(v):
    s = str(v)
    if len(s) != 8:
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
    except Exception:
        return None


def ampliar_cache(missing, eq_art, cache):
    if not missing:
        return cache

    print(f"ArtÃ­culos nuevos para cache histÃ³rica: {len(missing)}")
    print("Recorriendo MOVAANT una vez. Este paso puede demorar en la carga inicial.")

    if TEMP_DB.exists():
        TEMP_DB.unlink()

    con = sqlite3.connect(TEMP_DB)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA temp_store=MEMORY")
    con.execute(
        """
        CREATE TABLE mov (
            art TEXT NOT NULL,
            fecha INTEGER NOT NULL,
            tm TEXT NOT NULL,
            doc INTEGER NOT NULL,
            seq INTEGER NOT NULL,
            cant TEXT,
            boni TEXT,
            eq TEXT,
            mm TEXT
        )
        """
    )

    path = BASE / "MOVAANT.DBF"
    registros, header_len, record_len, campos = estructura_dbf(path)
    requerido = {"ART", "FECHA", "TM", "DOC", "CANT", "BONI", "EQ", "MM", "ELI", "COSTO"}
    faltan = requerido - set(campos)
    if faltan:
        raise SystemExit(f"MOVAANT no contiene campos requeridos: {sorted(faltan)}")

    art_len = campos["ART"][1]
    missing_raw = {
        k.encode("latin1", errors="ignore")[:art_len].ljust(art_len, b" ")
        for k in missing
    }

    ultcs = {}
    batch = []
    encontrados = set()

    with path.open("rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        pos = header_len
        for i in range(registros):
            if mm[pos : pos + 1] == b"*":
                pos += record_len
                continue

            art_raw = raw_field(mm, pos, campos, "ART")
            if art_raw not in missing_raw:
                pos += record_len
                continue

            k = key7(raw_text(art_raw, strip=False))
            encontrados.add(k)

            fecha_raw = raw_text(raw_field(mm, pos, campos, "FECHA"))
            if len(fecha_raw) == 8 and fecha_raw.isdigit() and fecha_raw != "00000000":
                fecha_i = int(fecha_raw)
            else:
                pos += record_len
                continue

            tm = raw_text(raw_field(mm, pos, campos, "TM"))
            doc_s = raw_text(raw_field(mm, pos, campos, "DOC"))
            try:
                doc = int(Decimal(doc_s)) if doc_s else 0
            except Exception:
                doc = 0

            cant = raw_text(raw_field(mm, pos, campos, "CANT"))
            boni = raw_text(raw_field(mm, pos, campos, "BONI"))
            eq = raw_text(raw_field(mm, pos, campos, "EQ"))
            mmov = raw_text(raw_field(mm, pos, campos, "MM"), strip=False)

            batch.append((k, fecha_i, tm, doc, i, cant, boni, eq, mmov))
            if len(batch) >= 10000:
                con.executemany("INSERT INTO mov VALUES (?,?,?,?,?,?,?,?,?)", batch)
                batch.clear()

            # v_ultcoscs MOVAANT: TM=CS, ELI vacÃ­o; Ãºltimo por FECHA y SEQ.
            eli = raw_text(raw_field(mm, pos, campos, "ELI"))
            if tm == "CS" and eli == "":
                costo = raw_text(raw_field(mm, pos, campos, "COSTO"))
                ant = ultcs.get(k)
                clave = (fecha_i, i)
                if ant is None or clave >= ant[0]:
                    ultcs[k] = (clave, costo)

            pos += record_len

        if batch:
            con.executemany("INSERT INTO mov VALUES (?,?,?,?,?,?,?,?,?)", batch)
        mm.close()

    con.commit()
    print(f"Registros histÃ³ricos seleccionados: {con.execute('SELECT COUNT(*) FROM mov').fetchone()[0]:,}")
    print("Ordenando segÃºn ART + FECHA + TM + DOC (criterio del Ã­ndice MOVART)...")
    con.execute("CREATE INDEX ix_mov ON mov(art, fecha, tm, doc, seq)")
    con.commit()

    movimientos = {}
    actual_art = None
    eq_actual = Decimal("1")
    total = Decimal("0")

    cur = con.execute(
        "SELECT art, fecha, tm, doc, seq, cant, boni, eq, mm FROM mov ORDER BY art, fecha, tm, doc, seq"
    )

    for art, fecha_i, tm, doc, seq, cant_s, boni_s, eq_s, mmov in cur:
        if art != actual_art:
            if actual_art is not None:
                movimientos[actual_art] = total
            actual_art = art
            eq_actual = eq_art.get(art, Decimal("1"))
            if eq_actual <= 0:
                eq_actual = Decimal("1")
            total = Decimal("0")

        eq_mov = D(eq_s)
        if eq_mov > 0:
            eq_actual = eq_mov

        wvar = rnd(D(cant_s) * eq_actual, 3) + rnd(D(boni_s) * eq_actual, 3)
        if str(mmov or "").strip() == "":
            wvar = Decimal("0")
        elif str(mmov).strip() == "-":
            wvar = -wvar

        total += wvar

    if actual_art is not None:
        movimientos[actual_art] = total

    con.close()
    try:
        TEMP_DB.unlink()
    except Exception:
        pass

    mov_cache = cache.setdefault("movaant", {})
    for k in missing:
        ult = ultcs.get(k)
        ult_dict = None
        if ult:
            (fecha_i, seq), costo = ult
            ult_dict = {
                "FECHA": ymd_to_date(fecha_i),
                "SEQ": seq,
                "COSTO": str(D(costo)),
            }

        mov_cache[k] = {
            "MOVIMIENTO": str(movimientos.get(k, Decimal("0"))),
            "ULTCS": ult_dict,
        }

    cache["version"] = 2
    cache["actualizado"] = datetime.now().isoformat(timespec="seconds")
    return cache


def main():
    parser = argparse.ArgumentParser(
        description="AmplÃ­a la cache histÃ³rica MOVAANT requerida por COSVEN. Solo lectura sobre Paykan."
    )
    parser.add_argument("--desde", type=parse_fecha, default=date(2025, 1, 1))
    parser.add_argument("--hasta", type=parse_fecha, default=date.today() - timedelta(days=1))
    parser.add_argument("--reconstruir", action="store_true")
    args = parser.parse_args()

    if args.desde > args.hasta:
        raise SystemExit("PerÃ­odo invÃ¡lido")

    print("Buscando artÃ­culos vendidos:", args.desde, "-", args.hasta)
    target, eq_art = sold_articles(args.desde, args.hasta)
    print(f"ArtÃ­culos requeridos: {len(target):,}")

    if args.reconstruir or not CACHE_FILE.exists():
        cache = {"version": 2, "movaant": {}}
    else:
        with CACHE_FILE.open("rb") as f:
            cache = pickle.load(f)
        if not isinstance(cache, dict) or "movaant" not in cache:
            cache = {"version": 2, "movaant": {}}

    existentes = set(cache.get("movaant", {}).keys())
    missing = target - existentes

    if not missing:
        print("Cache histÃ³rica al dÃ­a. No es necesario recorrer MOVAANT.")
        return

    cache = ampliar_cache(missing, eq_art, cache)
    with CACHE_FILE.open("wb") as f:
        pickle.dump(cache, f, protocol=pickle.HIGHEST_PROTOCOL)

    print("Cache guardada:", CACHE_FILE)
    print(f"ArtÃ­culos en cache: {len(cache['movaant']):,}")


if __name__ == "__main__":
    main()

