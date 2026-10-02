from pathlib import Path
from dbfread import DBF
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import csv

ROOT = Path(r"C:\Paykan\COSVEN_V3")
BASE = ROOT / "cache" / "snapshot_historico"
SALIDA_DIR = ROOT / "data" / "historico_prueba_2025"

SALIDA_DIR.mkdir(parents=True, exist_ok=True)

DESDE = date(2025, 1, 1)
HASTA = date(2025, 12, 31)

SALIDA = SALIDA_DIR / "cosven_detalle_2025.csv"


def D(v):
    if v is None:
        return Decimal("0")
    s = str(v).strip()
    return Decimal(s) if s else Decimal("0")


def rnd(v, dec=2):
    q = Decimal("1").scaleb(-dec)
    return D(v).quantize(q, rounding=ROUND_HALF_UP)


def blank(v):
    return str(v or "").strip() == ""


def txt(v):
    return str(v or "")


def key7(v):
    return txt(v)[:7].ljust(7)


def foxstr(v, ancho):
    return str(int(D(v))).rjust(ancho)


def abrir(nombre):
    return DBF(
        BASE / nombre,
        encoding="latin1",
        load=False,
        char_decode_errors="ignore",
    )


print("=" * 70)
print("COSVEN HISTORICO 2025 - MODO PRUEBA")
print("=" * 70)
print("Fuente:", BASE)
print("Periodo:", DESDE, "-", HASTA)
print()


# ============================================================
# ARTICULOS
# ============================================================

print("1/7 ARTICULO")

articulos = {}
activos = set()

for r in abrir("ARTICULO.DBF"):

    if not blank(r.get("ELI")):
        continue

    k = key7(r.get("ART"))

    eq = D(r.get("EQ"))
    if eq <= 0:
        eq = Decimal("1")

    articulos[k] = {
        "ART": txt(r.get("ART")),
        "XFLIA": txt(r.get("XFLIA")),
        "XART": txt(r.get("XART")),
        "DET": txt(r.get("DET")).strip(),
        "FLIANEW": int(D(r.get("FLIANEW"))),
        "IVA": D(r.get("IVA")),
        "EQ": eq,
        "MUL2": D(r.get("MUL2")),
        "ACTIVO": txt(r.get("ACTIVO")),
    }

    if txt(r.get("ACTIVO")) != "N":
        activos.add(k)


# ============================================================
# FAMILIAS / CLIENTES
# ============================================================

fliasnew = {}

for r in abrir("FLIASNEW.DBF"):
    fliasnew[int(D(r.get("FLIANEW")))] = txt(r.get("DET")).strip()


clientes = {}

for r in abrir("CLIENTES.DBF"):
    cli = int(D(r.get("CLI")))
    if cli > 0:
        clientes[cli] = txt(r.get("NOM")).strip()


# ============================================================
# MOVAANT
# ============================================================

print("2/7 MOVAANT")

ventas = []
movimientos = defaultdict(list)
ingresos = defaultdict(list)
cs_hist = defaultdict(list)

seq = 0

for r in abrir("MOVAANT.DBF"):

    seq += 1

    if seq % 500000 == 0:
        print(f"   {seq:,} registros procesados")

    fecha = r.get("FECHA")

    if not fecha:
        continue

    k = key7(r.get("ART"))

    art = articulos.get(k)

    if art is None:
        continue

    # --------------------------------------------------------
    # MOVIMIENTOS PARA STOCK HISTORICO
    # --------------------------------------------------------

    if fecha <= HASTA:

        movimientos[k].append({
            "FECHA": fecha,
            "SEQ": seq,
            "CANT": D(r.get("CANT")),
            "BONI": D(r.get("BONI")),
            "EQ": D(r.get("EQ")),
            "MM": txt(r.get("MM")),
        })

    # --------------------------------------------------------
    # INGRESOS STOCK
    # --------------------------------------------------------

    if (
        txt(r.get("TM")) == "IS"
        and blank(r.get("ELI"))
        and (D(r.get("CANT")) + D(r.get("BONI"))) > 0
        and txt(r.get("MON")) == "$  "
        and D(r.get("IMP")) > 0
    ):

        ingresos[k].append({
            "FECHA": fecha,
            "SEQ": seq,
            "DOC": int(D(r.get("DOC"))),
            "CANT": D(r.get("CANT")),
            "BONI": D(r.get("BONI")),
            "IMP": D(r.get("IMP")),
        })

    # --------------------------------------------------------
    # ULTIMO CS
    # --------------------------------------------------------

    if (
        txt(r.get("TM")) == "CS"
        and blank(r.get("ELI"))
    ):

        cs_hist[k].append({
            "FECHA": fecha,
            "SEQ": seq,
            "COSTO": D(r.get("COSTO")),
        })

    # --------------------------------------------------------
    # SELECCION COSVEN 2025
    # --------------------------------------------------------

    if fecha < DESDE or fecha > HASTA:
        continue

    if not blank(r.get("ELI")):
        continue

    if D(r.get("CLI")) <= 0:
        continue

    mm = txt(r.get("MM")).strip()

    if mm not in ("-", "+"):
        continue

    cant_original = D(r.get("CANT"))
    boni_original = D(r.get("BONI"))

    if cant_original + boni_original == 0:
        continue

    cant = cant_original
    boni = boni_original
    imp = D(r.get("IMP"))

    costo = rnd(
        D(r.get("COSTO"))
        * (cant_original + boni_original),
        2
    )

    if mm == "+":
        cant = -cant
        boni = -boni
        imp = -imp
        costo = -costo

    cli = int(D(r.get("CLI")))

    ventas.append({
        "ARTKEY": k,
        "XFLIA": art["XFLIA"],
        "XART": art["XART"],
        "DET": art["DET"],
        "FLIANEW": art["FLIANEW"],
        "IVA": art["IVA"],
        "FECHA": fecha,
        "CLI": cli,
        "NOM": clientes.get(cli, ""),
        "TM": txt(r.get("TM")).strip(),
        "DOC": int(D(r.get("DOC"))),
        "CANT": cant,
        "BONI": boni,
        "DTO": D(r.get("DTO")),
        "IMP": rnd(imp, 2),
        "COSTO": rnd(costo, 2),
    })


ventas.sort(
    key=lambda x: (
        x["ARTKEY"],
        x["CLI"],
        x["FECHA"],
        x["DOC"],
    )
)

arts_vendidos = {x["ARTKEY"] for x in ventas}

print()
print("Movimientos COSVEN 2025:", f"{len(ventas):,}")
print("Articulos vendidos:", f"{len(arts_vendidos):,}")


# ============================================================
# STOCK BASE
# ============================================================

print("3/7 MO180709")

stock_base = defaultdict(Decimal)

for r in abrir("MO180709.DBF"):
    k = key7(r.get("ART"))
    if k in arts_vendidos:
        stock_base[k] = D(r.get("CANT"))


# ============================================================
# COMPRAS PEDCOM / ARTCOM
# ============================================================

print("4/7 PEDCOM")

pedidos = {}

for r in abrir("PEDCOM.DBF"):

    fecha = r.get("FECHA")

    if not fecha:
        continue

    if fecha.year < 2017 or fecha > HASTA:
        continue

    if not blank(r.get("ELI")):
        continue

    if txt(r.get("TM")) != "FC":
        continue

    clave = (
        int(D(r.get("ACR"))),
        txt(r.get("TM")),
        int(D(r.get("DOC"))),
    )

    pedidos[clave] = {
        "FECHA": fecha,
        "DTOF1": D(r.get("DTOF1")),
        "DTOF2": D(r.get("DTOF2")),
        "DTOF3": D(r.get("DTOF3")),
    }


print("5/7 ARTCOM")

wcosart = defaultdict(list)
seq_compra = 0

for r in abrir("ARTCOM.DBF"):

    clave = (
        int(D(r.get("ACR"))),
        txt(r.get("TM")),
        int(D(r.get("DOC"))),
    )

    ped = pedidos.get(clave)

    if ped is None:
        continue

    if not blank(r.get("ELI")):
        continue

    k = key7(
        foxstr(r.get("FLIA"), 3)
        + foxstr(r.get("ART"), 4)
    )

    if k not in arts_vendidos:
        continue

    seq_compra += 1

    wvar = D(r.get("PRECIO"))

    for dto in (
        D(r.get("DTO")),
        ped["DTOF1"],
        ped["DTOF2"],
        ped["DTOF3"],
    ):
        if dto > 0:
            wvar = (
                wvar
                - rnd(
                    wvar * dto / Decimal("100"),
                    2
                )
            )

    if articulos[k]["MUL2"] == Decimal("1.020"):
        wvar = rnd(
            wvar * Decimal("1.02"),
            2
        )

    cant = D(r.get("CANT"))
    boni = D(r.get("BONI"))

    wcosto = rnd(wvar * cant, 2)

    if cant + boni > 0:
        cosfin = rnd(
            wcosto / (cant + boni),
            2
        )
    else:
        cosfin = wcosto

    wcosart[k].append({
        "SEQ": seq_compra,
        "FECHA": ped["FECHA"],
        "DOC": clave[2],
        "CANT": cant,
        "BONI": boni,
        "COSFIN": cosfin,
    })


for k in wcosart:
    wcosart[k].sort(
        key=lambda x: (
            x["FECHA"],
            x["DOC"],
            x["SEQ"],
        )
    )


# ============================================================
# PRECALCULAR STOCK DIARIO
# ============================================================

print("6/7 Reconstruyendo costos 2025")

# Ordenamos movimientos histÃ³ricos una sola vez.
for k in movimientos:
    movimientos[k].sort(
        key=lambda x: (
            x["FECHA"],
            x["SEQ"],
        )
    )


# Ãšltimo CS disponible por artÃ­culo hasta cada necesidad.
def ultimo_cs(k, dia):

    candidatos = [
        x
        for x in cs_hist.get(k, [])
        if x["FECHA"] < dia
    ]

    if not candidatos:
        return Decimal("0")

    candidatos.sort(
        key=lambda x: (
            x["FECHA"],
            x["SEQ"],
        )
    )

    return rnd(candidatos[-1]["COSTO"], 2)


def stock_dia(k, dia):

    stock = D(stock_base.get(k, 0))

    eq = articulos[k]["EQ"]

    if eq <= 0:
        eq = Decimal("1")

    for m in movimientos.get(k, []):

        if m["FECHA"] >= dia:
            break

        if m["EQ"] > 0:
            eq = m["EQ"]

        wvar = (
            rnd(m["CANT"] * eq, 3)
            + rnd(m["BONI"] * eq, 3)
        )

        mm = str(m["MM"] or "").strip()

        if mm == "":
            wvar = Decimal("0")
        elif mm == "-":
            wvar = -wvar

        stock += wvar

    return stock


def costo_dia(k, dia):

    if k not in activos:
        return None

    stock = stock_dia(k, dia)

    previas = [
        x
        for x in wcosart.get(k, [])
        if x["FECHA"] < dia
    ]

    precio4 = Decimal("0")

    if stock > 0:

        orden = sorted(
            previas,
            key=lambda x: (
                x["FECHA"],
                x["DOC"],
                x["SEQ"],
            ),
            reverse=True,
        )

        wstk = stock
        wimp = Decimal("0")
        whecho = Decimal("0")

        for x in orden:

            if wstk <= 0:
                break

            weste = x["CANT"] + x["BONI"]

            if weste >= wstk:

                wimp += rnd(
                    wstk * x["COSFIN"],
                    2
                )

                whecho += wstk
                wstk = Decimal("0")

            else:

                wimp += rnd(
                    weste * x["COSFIN"],
                    2
                )

                wstk -= weste
                whecho += weste

        if whecho > 0:
            precio4 = rnd(
                wimp / whecho,
                2
            )

    positivos = [
        x
        for x in previas
        if x["COSFIN"] > 0
    ]

    cosrep = Decimal("0")

    if positivos:

        positivos.sort(
            key=lambda x: (
                x["FECHA"],
                x["DOC"],
                x["SEQ"],
            )
        )

        cosrep = positivos[-1]["COSFIN"]

    if cosrep <= 0:

        lista_is = [
            x
            for x in ingresos.get(k, [])
            if x["FECHA"] < dia
        ]

        if lista_is:

            lista_is.sort(
                key=lambda x: (
                    x["FECHA"],
                    x["DOC"],
                    x["SEQ"],
                )
            )

            ultimo = lista_is[-1]

            unidades = (
                ultimo["CANT"]
                + ultimo["BONI"]
            )

            if unidades != 0:
                cosrep = rnd(
                    ultimo["IMP"] / unidades,
                    2
                )

    ultcs = ultimo_cs(k, dia)

    if cosrep <= 0:
        cosrep = ultcs

    if precio4 <= 0:
        precio4 = ultcs

    return {
        "COSREP": rnd(cosrep, 2),
        "PRECIO4": rnd(precio4, 2),
    }


# Solo calculamos una vez cada combinaciÃ³n artÃ­culo/dÃ­a
necesidades = sorted({
    (x["ARTKEY"], x["FECHA"])
    for x in ventas
})

costos_dia = {}

total_necesidades = len(necesidades)

for i, (k, dia) in enumerate(necesidades, 1):

    costos_dia[(k, dia)] = costo_dia(k, dia)

    if i % 5000 == 0:
        print(
            f"   {i:,} / {total_necesidades:,} "
            f"articulo-fecha"
        )


# ============================================================
# APLICAR COSTOS
# ============================================================

print("7/7 Generando detalle")

detalle = []

for x0 in ventas:

    x = dict(x0)

    c = costos_dia.get(
        (x["ARTKEY"], x["FECHA"])
    )

    if c is not None:

        x["COSTO"] = rnd(
            c["PRECIO4"]
            * (
                x["CANT"]
                + x["BONI"]
            ),
            2
        )

    x["UTILIDAD"] = rnd(
        x["IMP"] - x["COSTO"],
        2
    )

    if x["COSTO"] > 0:

        x["PUTIL"] = rnd(
            (
                x["IMP"]
                / x["COSTO"]
                - Decimal("1")
            )
            * Decimal("100"),
            2
        )

    else:

        x["PUTIL"] = Decimal("0")

    detalle.append(x)


campos = [
    "XFLIA",
    "XART",
    "DET",
    "FLIANEW",
    "FAMILIA_DESC",
    "FECHA",
    "CLI",
    "NOM",
    "TM",
    "DOC",
    "CANT",
    "BONI",
    "DTO",
    "COSTO",
    "IMP",
    "UTILIDAD",
    "PUTIL",
    "IVA",
]


with SALIDA.open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as f:

    w = csv.DictWriter(
        f,
        fieldnames=campos,
        delimiter=";",
    )

    w.writeheader()

    for x in detalle:

        w.writerow({
            "XFLIA": x["XFLIA"],
            "XART": x["XART"],
            "DET": x["DET"],
            "FLIANEW": x["FLIANEW"],
            "FAMILIA_DESC": fliasnew.get(
                x["FLIANEW"], ""
            ),
            "FECHA": x["FECHA"],
            "CLI": x["CLI"],
            "NOM": x["NOM"],
            "TM": x["TM"],
            "DOC": x["DOC"],
            "CANT": x["CANT"],
            "BONI": x["BONI"],
            "DTO": x["DTO"],
            "COSTO": x["COSTO"],
            "IMP": x["IMP"],
            "UTILIDAD": x["UTILIDAD"],
            "PUTIL": x["PUTIL"],
            "IVA": x["IVA"],
        })


print()
print("=" * 70)
print("TERMINADO")
print("=" * 70)

print("Movimientos:", f"{len(detalle):,}")
print("Archivo:", SALIDA)

print(
    "FC:",
    sum(1 for x in detalle if x["TM"] == "FC")
)

print(
    "NC:",
    sum(1 for x in detalle if x["TM"] == "NC")
)

print(
    "Venta:",
    rnd(sum((x["IMP"] for x in detalle), Decimal("0")), 2)
)

print(
    "Costo:",
    rnd(sum((x["COSTO"] for x in detalle), Decimal("0")), 2)
)

print(
    "Utilidad:",
    rnd(sum((x["UTILIDAD"] for x in detalle), Decimal("0")), 2)
)
