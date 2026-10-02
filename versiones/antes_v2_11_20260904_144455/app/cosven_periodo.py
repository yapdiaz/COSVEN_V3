from pathlib import Path
from dbfread import DBF
from datetime import date, timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import csv
import mmap
import pickle
import struct
import argparse

ROOT = Path(r"C:\Paykan\COSVEN")
BASE = Path(r"\\Paykans\c\paykann\libres")
CACHE_DIR = ROOT / "cache"
DATA_DIR = ROOT / "data"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

CACHE_HIST = CACHE_DIR / "cosven_historico_2026.pkl"


def parse_fecha(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


parser = argparse.ArgumentParser(
    description="Calcula COSVEN para un período sin modificar los DBF fuente."
)
parser.add_argument("--desde", type=parse_fecha)
parser.add_argument("--hasta", type=parse_fecha)
parser.add_argument("--salida-dir", type=Path, default=DATA_DIR / "proceso")
args = parser.parse_args()

HOY = date.today()
AYER = HOY - timedelta(days=1)

# Por defecto, el cálculo operativo trabaja sobre el mes que contiene ayer.
# Esto también funciona correctamente el día 1: finaliza el mes anterior.
WHF = args.hasta or AYER
WDF = args.desde or WHF.replace(day=1)

if WDF > WHF:
    raise SystemExit(f"Período inválido: {WDF} > {WHF}")

args.salida_dir.mkdir(parents=True, exist_ok=True)

SALIDA_TOTAL = args.salida_dir / "cosven_total.csv"
SALIDA_PERDIDAS = args.salida_dir / "cosven_perdidas.csv"
SALIDA_DETALLE = args.salida_dir / "cosven_detalle.csv"

# Exacto de v_ultcoscs:
# XFINM = date() - day(date())
XFINM = HOY - timedelta(days=HOY.day)


# ============================================================
# FUNCIONES
# ============================================================

def D(v):
    if v is None:
        return Decimal("0")

    s = str(v).strip()

    if not s:
        return Decimal("0")

    return Decimal(s)


def rnd(v, dec=2):

    q = Decimal("1").scaleb(-dec)

    return D(v).quantize(
        q,
        rounding=ROUND_HALF_UP
    )


def blank(v):
    return str(v or "").strip() == ""


def txt(v):
    return str(v or "")


def key7(v):
    return txt(v)[:7].ljust(7)


def foxstr(v, ancho):

    n = int(D(v))

    return str(n).rjust(ancho)


def abrir(nombre):

    return DBF(
        BASE / nombre,
        encoding="latin1",
        load=False,
        char_decode_errors="ignore"
    )


# ============================================================
# CACHE HISTORICA MOVAANT
#
# Se carga después de identificar los artículos vendidos.
# El cache se construye con preparar_cache_historica.py.
# ============================================================

# ============================================================
# ARTICULO
# ============================================================

print("Periodo:", WDF, "-", WHF)
print("1/8 ARTICULO")

articulos = {}
activos = set()

for r in abrir("ARTICULO.DBF"):

    # seleccion y ARMOPP exigen ELI = " "
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

        "FLIANEW": int(
            D(r.get("FLIANEW"))
        ),

        "IVA": D(r.get("IVA")),

        "EQ": eq,

        "MUL2": D(r.get("MUL2")),

        "ACTIVO": txt(
            r.get("ACTIVO")
        )
    }

    # ARMOPP:
    # ARTICULO.ELI=" "
    # AND ACTIVO <> "N"
    if txt(r.get("ACTIVO")) != "N":

        activos.add(k)


# ============================================================
# FAMILIAS
# ============================================================

fliasnew = {}

for r in abrir("FLIASNEW.DBF"):

    fliasnew[
        int(D(r.get("FLIANEW")))
    ] = txt(
        r.get("DET")
    ).strip()


# ============================================================
# CLIENTES
# Sólo para enriquecer el detalle. No interviene en costos.
# ============================================================

clientes = {}

for r in abrir("CLIENTES.DBF"):

    cli = int(D(r.get("CLI")))

    if cli > 0:

        clientes[cli] = txt(
            r.get("NOM")
        ).strip()


# ============================================================
# MOVART
# ============================================================

print("2/8 MOVART")

ventas = []

movimientos = defaultdict(list)

ingresos = defaultdict(list)

cs_movart = defaultdict(list)

seq = 0


for r in abrir("MOVART.DBF"):

    seq += 1

    k = key7(r.get("ART"))

    fecha = r.get("FECHA")

    if not fecha:
        continue


    # --------------------------------------------------------
    # ARMOPP: movimientos para reconstruir stock
    #
    # El fuente NO filtra ELI aquí.
    # --------------------------------------------------------

    if (
        k in articulos
        and fecha <= WHF
    ):

        movimientos[k].append({

            "SEQ": seq,

            "FECHA": fecha,

            "CANT": D(
                r.get("CANT")
            ),

            "BONI": D(
                r.get("BONI")
            ),

            "EQ": D(
                r.get("EQ")
            ),

            "MM": txt(
                r.get("MM")
            )
        })


    # --------------------------------------------------------
    # INGRESO STOCK
    # --------------------------------------------------------

    if (
        k in articulos
        and txt(r.get("TM")) == "IS"
        and blank(r.get("ELI"))
        and (
            D(r.get("CANT"))
            + D(r.get("BONI"))
        ) > 0
        and txt(r.get("MON")) == "$  "
        and D(r.get("IMP")) > 0
    ):

        ingresos[k].append({

            "SEQ": seq,

            "FECHA": fecha,

            "DOC": int(
                D(r.get("DOC"))
            ),

            "CANT": D(
                r.get("CANT")
            ),

            "BONI": D(
                r.get("BONI")
            ),

            "IMP": D(
                r.get("IMP")
            )
        })


    # --------------------------------------------------------
    # v_ultcoscs MOVART
    # --------------------------------------------------------

    if (
        k in articulos
        and txt(r.get("TM")) == "CS"
        and blank(r.get("ELI"))
        and fecha <= XFINM
    ):

        cs_movart[k].append({

            "SEQ": seq,

            "FECHA": fecha,

            "COSTO": D(
                r.get("COSTO")
            )
        })


    # --------------------------------------------------------
    # seleccion
    # --------------------------------------------------------

    art = articulos.get(k)

    if art is None:
        continue

    if not blank(r.get("ELI")):
        continue

    if fecha < WDF:
        continue

    if fecha > WHF:
        continue

    if D(r.get("CLI")) <= 0:
        continue

    mm = txt(r.get("MM"))

    if mm not in ("-", "+"):
        continue

    cant_original = D(
        r.get("CANT")
    )

    boni_original = D(
        r.get("BONI")
    )

    if (
        cant_original
        + boni_original
    ) == 0:
        continue


    cant = cant_original
    boni = boni_original

    imp = D(
        r.get("IMP")
    )


    # COSTO inicial de seleccion
    costo = rnd(

        D(r.get("COSTO"))

        * (
            cant_original
            + boni_original
        ),

        2
    )


    if mm == "+":

        cant = -cant

        boni = -boni

        imp = -imp

        costo = -costo


    ventas.append({

        "ARTKEY": k,

        "ART": art["ART"],

        "XFLIA": art["XFLIA"],
        "XART": art["XART"],

        "DET": art["DET"],

        "FLIANEW": art["FLIANEW"],

        "IVA": art["IVA"],

        "FECHA": fecha,

        "CLI": int(
            D(r.get("CLI"))
        ),

        "NOM": clientes.get(
            int(D(r.get("CLI"))),
            ""
        ),

        "TM": txt(
            r.get("TM")
        ),

        "DOC": int(
            D(r.get("DOC"))
        ),

        "CANT": cant,

        "BONI": boni,

        # Datos informativos del movimiento. No intervienen en el cálculo COSVEN.
        "DTO": D(r.get("DTO")),
        "CLAING": int(D(r.get("CLAING"))),

        "IMP": rnd(
            imp,
            2
        ),

        "COSTO": rnd(
            costo,
            2
        )
    })


ventas.sort(

    key=lambda x: (

        x["ARTKEY"],
        x["CLI"],
        x["FECHA"],
        x["DOC"]
    )
)


arts_vendidos = {

    x["ARTKEY"]
    for x in ventas
}


print(
    "   Movimientos:",
    len(ventas)
)

print(
    "   Articulos:",
    len(arts_vendidos)
)


# ============================================================
# USUARIO QUE REGISTRÓ EL MOVIMIENTO / PEDIDO
#
# Relación confirmada en el fuente de ventas:
# MOVART.CLAING -> USUARIOS.NCLA -> USUARIOS.USUARIO
# Sólo enriquece el detalle; no interviene en costos ni utilidad.
# ============================================================

usuario_por_claing = {}

usuarios_dbf = DBF(
    BASE / "USUARIOS.DBF",
    encoding="latin1",
    load=False,
    raw=True
)

for r in usuarios_dbf:

    ncla = raw_int(r.get("NCLA")) if "raw_int" in globals() else 0

    # raw_int se declara unas líneas más abajo; para mantener este bloque
    # independiente se hace un parseo local cuando todavía no existe.
    if ncla <= 0:
        try:
            valor_ncla = r.get("NCLA")
            if isinstance(valor_ncla, bytes):
                valor_ncla = valor_ncla.decode("latin1", errors="ignore").strip()
            ncla = int(Decimal(str(valor_ncla or "").strip() or "0"))
        except Exception:
            ncla = 0

    if ncla <= 0 or ncla in usuario_por_claing:
        continue

    valor_usuario = r.get("USUARIO")

    if isinstance(valor_usuario, bytes):
        valor_usuario = valor_usuario.decode("latin1", errors="ignore")

    usuario_por_claing[ncla] = str(valor_usuario or "").strip()


for x in ventas:
    x["USUARIO"] = usuario_por_claing.get(
        int(x.get("CLAING") or 0),
        ""
    )


# ============================================================
# CACHE HISTORICA MOVAANT
# ============================================================

if not CACHE_HIST.exists():
    raise SystemExit(
        f"No existe {CACHE_HIST}. "
        "Ejecute primero preparar_cache_historica.py para el período requerido."
    )

with CACHE_HIST.open("rb") as f:
    cache_hist = pickle.load(f)

cache_movaant = cache_hist.get("movaant", {})
faltantes_hist = sorted(arts_vendidos - set(cache_movaant.keys()))

if faltantes_hist:
    muestra = ", ".join(faltantes_hist[:10])
    raise SystemExit(
        "La cache histórica no contiene todos los artículos del período. "
        f"Faltan {len(faltantes_hist)}. Ejemplos: {muestra}. "
        "Ejecute preparar_cache_historica.py nuevamente."
    )

hist = {}
for k in arts_vendidos:
    v = cache_movaant[k]
    if isinstance(v, dict):
        v = v.get("MOVIMIENTO", 0)
    hist[k] = D(v)


# ============================================================
# PEDIDO / TIPO DE PEDIDO
#
# Relación confirmada en ventas.SCT:
# MOVART.TM + MOVART.DOC
#   -> HISVTA.TM + HISVTA.DOC
#   -> HISVTA.PED
#   -> PEDIDOS.PED
#   -> PEDIDOS.VRLL
#
# Z: SOLO LECTURA.
# ============================================================

TIPOS_PEDIDO = {
    "E": "Llamada Entrante",
    "S": "Llamada Saliente",
    "V": "Pedido del Vendedor",
    "W": "WhatsApp",
    "T": "Transfer",
    "C": "Canje",
    "R": "Remito",
    "P": "Pedido Web",
}


def raw_txt(v):

    if v is None:
        return ""

    if isinstance(v, bytes):

        return v.decode(
            "latin1",
            errors="ignore"
        ).strip()

    return str(v).strip()


def raw_int(v):

    s = raw_txt(v)

    if not s:
        return 0

    try:
        return int(
            Decimal(s)
        )
    except Exception:
        return 0


docs_venta = {

    (
        x["TM"],
        x["DOC"]
    )

    for x in ventas
}


doc_a_pedido = {}


hisvta = DBF(
    BASE / "HISVTA.DBF",
    encoding="latin1",
    load=False,
    raw=True
)


for r in hisvta:

    tm = raw_txt(
        r.get("TM")
    )

    doc = raw_int(
        r.get("DOC")
    )

    clave = (
        tm,
        doc
    )

    if clave not in docs_venta:
        continue

    doc_a_pedido[clave] = raw_int(
        r.get("PED")
    )


pedidos_necesarios = {

    ped

    for ped in doc_a_pedido.values()

    if ped > 0
}


pedido_a_vrll = {}


pedidos_dbf = DBF(
    BASE / "PEDIDOS.DBF",
    encoding="latin1",
    load=False,
    raw=True
)


for r in pedidos_dbf:

    ped = raw_int(
        r.get("PED")
    )

    if ped not in pedidos_necesarios:
        continue

    pedido_a_vrll[ped] = raw_txt(
        r.get("VRLL")
    )


for x in ventas:

    clave = (
        x["TM"],
        x["DOC"]
    )

    ped = doc_a_pedido.get(
        clave,
        0
    )

    vrll = pedido_a_vrll.get(
        ped,
        ""
    )

    x["PED"] = ped

    x["VRLL"] = vrll

    if ped <= 0:

        x["TIPO_PEDIDO"] = (
            "Sin pedido"
        )

    elif vrll in TIPOS_PEDIDO:

        x["TIPO_PEDIDO"] = (
            TIPOS_PEDIDO[vrll]
        )

    else:

        x["TIPO_PEDIDO"] = (
            "Sin clasificar"
        )


# ============================================================
# MO180709
# ============================================================

print("3/8 MO180709")

stock_base = defaultdict(
    Decimal
)


for r in abrir("MO180709.DBF"):

    k = key7(
        r.get("ART")
    )

    if k in arts_vendidos:

        stock_base[k] = D(
            r.get("CANT")
        )


# ============================================================
# v_ultcoscs - MOVAANT
#
# La última salida CS histórica se guarda junto con la cache
# de MOVAANT para evitar volver a recorrer millones de registros.
# ============================================================

print("4/8 v_ultcoscs")

cs_movaant = {}
for k in arts_vendidos:
    v = cache_movaant.get(k, {})
    if isinstance(v, dict):
        ult = v.get("ULTCS")
        if ult:
            cs_movaant[k] = {
                "FECHA": ult.get("FECHA"),
                "SEQ": int(ult.get("SEQ", 0)),
                "COSTO": D(ult.get("COSTO", 0)),
            }

wultcoscs = {}

for k in arts_vendidos:
    candidatos = []

    x = cs_movaant.get(k)
    if x and x.get("FECHA"):
        candidatos.append((
            x["FECHA"],
            0,
            x["SEQ"],
            x["COSTO"]
        ))

    for x in cs_movart.get(k, []):
        candidatos.append((
            x["FECHA"],
            1,
            x["SEQ"],
            x["COSTO"]
        ))

    candidatos.sort(key=lambda x: (x[0], x[1], x[2]))

    if candidatos:
        wultcoscs[k] = rnd(candidatos[-1][3], 2)
    else:
        wultcoscs[k] = Decimal("0")


# ============================================================
# PEDCOM
# ============================================================

print("5/8 PEDCOM / ARTCOM")


pedidos = {}


for r in abrir("PEDCOM.DBF"):

    fecha = r.get("FECHA")

    if not fecha:
        continue


    if not (
        2017
        <= fecha.year
        <= WHF.year
    ):
        continue


    if not blank(
        r.get("ELI")
    ):
        continue


    if txt(
        r.get("TM")
    ) != "FC":
        continue


    # WPEDCOM:
    # luego ignora FECHA > WHF
    if fecha > WHF:
        continue


    clave = (

        int(
            D(r.get("ACR"))
        ),

        txt(
            r.get("TM")
        ),

        int(
            D(r.get("DOC"))
        )
    )


    pedidos[clave] = {

        "FECHA": fecha,

        "DTOF1":
            D(r.get("DTOF1")),

        "DTOF2":
            D(r.get("DTOF2")),

        "DTOF3":
            D(r.get("DTOF3"))
    }


# ============================================================
# ARTCOM -> WCOSART
# ============================================================

wcosart = defaultdict(list)

seq_compra = 0


for r in abrir("ARTCOM.DBF"):

    clave = (

        int(
            D(r.get("ACR"))
        ),

        txt(
            r.get("TM")
        ),

        int(
            D(r.get("DOC"))
        )
    )


    ped = pedidos.get(
        clave
    )


    if ped is None:
        continue


    if not blank(
        r.get("ELI")
    ):
        continue


    k = (

        foxstr(
            r.get("FLIA"),
            3
        )

        +

        foxstr(
            r.get("ART"),
            4
        )
    )


    k = key7(k)


    if k not in arts_vendidos:
        continue


    seq_compra += 1


    wvar = D(
        r.get("PRECIO")
    )


    # Exactamente en este orden
    for dto in (

        D(r.get("DTO")),

        ped["DTOF1"],
        ped["DTOF2"],
        ped["DTOF3"]
    ):

        if dto > 0:

            wvar = (

                wvar

                - rnd(
                    wvar
                    * dto
                    / Decimal("100"),
                    2
                )
            )


    if (
        articulos[k]["MUL2"]
        == Decimal("1.020")
    ):

        wvar = rnd(
            wvar
            * Decimal("1.02"),
            2
        )


    cant = D(
        r.get("CANT")
    )

    boni = D(
        r.get("BONI")
    )


    wcosto = rnd(
        wvar * cant,
        2
    )


    if (
        cant + boni
    ) > 0:

        cosfin = rnd(

            wcosto
            / (
                cant
                + boni
            ),

            2
        )

    else:

        cosfin = wcosto


    wcosart[k].append({

        "SEQ":
            seq_compra,

        "FECHA":
            ped["FECHA"],

        "DOC":
            clave[2],

        "CANT":
            cant,

        "BONI":
            boni,

        "COSFIN":
            cosfin
    })


for k in wcosart:

    wcosart[k].sort(

        key=lambda x: (

            x["FECHA"],
            x["DOC"],
            x["SEQ"]
        )
    )


# ============================================================
# WMASIGUAL
#
# copy ... for FECHA >= WDF
# index ART+dtos(FECHA)
# posteriormente SEEK WORKART.ART
# ============================================================

wmasigual = {}


for k, lista in wcosart.items():

    candidatos = [

        x

        for x in lista

        if x["FECHA"] >= WDF
    ]


    if candidatos:

        candidatos.sort(

            key=lambda x: (

                x["FECHA"],
                x["SEQ"]
            )
        )


        wmasigual[k] = (
            candidatos[0]["COSFIN"]
        )


# ============================================================
# STOCK POR DIA
#
# MO180709
# + MOVAANT histórico cacheado
# + MOVART con FECHA < WHFEC
#
# WEQ se reinicia a ARTICULO.EQ
# antes de MOVART.
# ============================================================

def stock_dia(k, dia):

    stock = D(
        stock_base.get(
            k,
            0
        )
    )


    stock += D(
        hist.get(
            k,
            0
        )
    )


    eq = articulos[k]["EQ"]


    if eq <= 0:

        eq = Decimal("1")


    for m in movimientos.get(
        k,
        []
    ):

        if m["FECHA"] >= dia:
            continue


        if m["EQ"] > 0:

            eq = m["EQ"]


        wvar = (

            rnd(
                m["CANT"]
                * eq,
                3
            )

            +

            rnd(
                m["BONI"]
                * eq,
                3
            )
        )


        if m["MM"] == " ":

            wvar = Decimal("0")


        if m["MM"] == "-":

            wvar = -wvar


        stock += wvar


    return stock


# ============================================================
# COSTO ARMOPP DEL DIA
# ============================================================

def costo_dia(k, dia):

    if k not in activos:
        return None


    stock = stock_dia(
        k,
        dia
    )


    # WCOSARTO:
    # FECHA < WHFEC

    previas = [

        x

        for x in wcosart.get(
            k,
            []
        )

        if x["FECHA"] < dia
    ]


    # --------------------------------------------------------
    # PRECIO4
    # --------------------------------------------------------

    precio4 = Decimal("0")


    if stock > 0:

        orden = sorted(

            previas,

            key=lambda x: (

                x["FECHA"],
                x["DOC"],
                x["SEQ"]
            ),

            reverse=True
        )


        wstk = stock

        wimp = Decimal("0")

        whecho = Decimal("0")


        for x in orden:

            if wstk <= 0:
                break


            weste = (

                x["CANT"]
                + x["BONI"]
            )


            if weste >= wstk:

                wimp += rnd(

                    wstk
                    * x["COSFIN"],

                    2
                )

                whecho += wstk

                wstk = Decimal("0")


            else:

                wimp += rnd(

                    weste
                    * x["COSFIN"],

                    2
                )

                wstk -= weste

                whecho += weste


        if whecho > 0:

            precio4 = rnd(

                wimp
                / whecho,

                2
            )


    # --------------------------------------------------------
    # COSREP:
    # WCOSARTF = último COSFIN > 0
    # --------------------------------------------------------

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
                x["SEQ"]
            )
        )


        cosrep = (
            positivos[-1]["COSFIN"]
        )


    # --------------------------------------------------------
    # Si no hay costo compra:
    # último IS anterior al día
    # --------------------------------------------------------

    if cosrep <= 0:

        lista_is = [

            x

            for x in ingresos.get(
                k,
                []
            )

            if x["FECHA"] < dia
        ]


        if lista_is:

            lista_is.sort(

                key=lambda x: (

                    x["FECHA"],
                    x["DOC"],
                    x["SEQ"]
                )
            )


            ultimo = lista_is[-1]


            unidades = (

                ultimo["CANT"]
                + ultimo["BONI"]
            )


            if unidades != 0:

                cosrep = rnd(

                    ultimo["IMP"]
                    / unidades,

                    2
                )


    # --------------------------------------------------------
    # WULTCOSCS
    # --------------------------------------------------------

    ultcs = D(
        wultcoscs.get(
            k,
            0
        )
    )


    if cosrep <= 0:

        cosrep = ultcs


    if precio4 <= 0:

        precio4 = ultcs


    return {

        "COSREP":
            rnd(cosrep, 2),

        "PRECIO4":
            rnd(precio4, 2)
    }


# ============================================================
# ARTTODOS
# ============================================================

print("6/8 ARMOPP")


arttodos = {}


dia = WDF


while dia <= WHF:

    print("   ", dia)


    for k in arts_vendidos:

        c = costo_dia(
            k,
            dia
        )


        if c is not None:

            arttodos[
                (k, dia)
            ] = c


    dia += timedelta(days=1)


# ============================================================
# APLICAR PRECIO4 A WORKART
# ============================================================

print("7/8 Aplicando costos")


detalle = []


for v in ventas:

    x = dict(v)


    c = arttodos.get(

        (
            v["ARTKEY"],
            v["FECHA"]
        )
    )


    # Si encontró ARTTODOS:
    # WTIPOLIS=3 => PRECIO4

    if c is not None:

        x["COSTO"] = rnd(

            c["PRECIO4"]

            * (
                x["CANT"]
                + x["BONI"]
            ),

            2
        )


    # WMASIGUAL SOLO SI COSTO SIGUE 0

    if x["COSTO"] == 0:

        c2 = wmasigual.get(
            x["ARTKEY"]
        )


        if c2 is not None:

            x["COSTO"] = rnd(

                c2

                * (
                    x["CANT"]
                    + x["BONI"]
                ),

                2
            )


    x["UTILIDAD"] = rnd(

        x["IMP"]
        - x["COSTO"],

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

        x["PUTIL"] = (
            Decimal("0")
        )


    detalle.append(x)


# ============================================================
# TOTAL ON ART
# fields CANT,BONI,IMP,COSTO
# ============================================================

print("8/8 Totalizando")


totales = {}


for x in detalle:

    k = x["ARTKEY"]


    if k not in totales:

        totales[k] = {

            "XFLIA":
                x["XFLIA"],

            "XART":
                x["XART"],

            "DET":
                x["DET"],

            "FLIANEW":
                x["FLIANEW"],

            "FAMILIA_DESC":
                fliasnew.get(
                    x["FLIANEW"],
                    ""
                ),

            "CANT":
                Decimal("0"),

            "BONI":
                Decimal("0"),

            "COSTO":
                Decimal("0"),

            "IMP":
                Decimal("0"),

            "IVA":
                x["IVA"]
        }


    t = totales[k]


    t["CANT"] += x["CANT"]

    t["BONI"] += x["BONI"]

    t["COSTO"] += x["COSTO"]

    t["IMP"] += x["IMP"]


resultado = []


for k, t in totales.items():

    t["COSTO"] = rnd(
        t["COSTO"],
        2
    )

    t["IMP"] = rnd(
        t["IMP"],
        2
    )


    t["UTILIDAD"] = rnd(

        t["IMP"]
        - t["COSTO"],

        2
    )


    if t["COSTO"] > 0:

        t["PUTIL"] = rnd(

            (
                t["IMP"]
                / t["COSTO"]
                - Decimal("1")
            )

            * Decimal("100"),

            2
        )

    else:

        t["PUTIL"] = Decimal("0")


    resultado.append(t)


resultado.sort(

    key=lambda x: (

        x["XFLIA"],
        x["XART"]
    )
)


# Este filtro NO cambia COSVEN.
# Sólo toma del resultado los UTILIDAD < 0.

perdidas = [

    x

    for x in resultado

    if x["UTILIDAD"] < 0
]


perdidas.sort(

    key=lambda x:
        x["UTILIDAD"]
)


campos = [

    "XFLIA",
    "XART",
    "DET",

    "FLIANEW",
    "FAMILIA_DESC",

    "CANT",
    "BONI",
    "DTO",
    "CLAING",
    "USUARIO",

    "COSTO",
    "IMP",

    "UTILIDAD",
    "PUTIL",

    "IVA"
]


def guardar(
    archivo,
    datos
):

    with archivo.open(

        "w",

        newline="",

        encoding="utf-8-sig"

    ) as f:

        w = csv.DictWriter(

            f,

            fieldnames=campos,

            delimiter=";"
        )

        w.writeheader()

        w.writerows(datos)


campos_detalle = [

    "XFLIA",
    "XART",
    "DET",

    "FLIANEW",
    "FAMILIA_DESC",

    "FECHA",

    "CLI",
    "NOM",

    "PED",
    "VRLL",
    "TIPO_PEDIDO",

    "TM",
    "DOC",

    "CANT",
    "BONI",

    "COSTO",
    "IMP",

    "UTILIDAD",
    "PUTIL",

    "IVA"
]


detalle_salida = []


for x in detalle:

    fila = {

        "XFLIA":
            x["XFLIA"],

        "XART":
            x["XART"],

        "DET":
            x["DET"],

        "FLIANEW":
            x["FLIANEW"],

        "FAMILIA_DESC":
            fliasnew.get(
                x["FLIANEW"],
                ""
            ),

        "FECHA":
            x["FECHA"],

        "CLI":
            x["CLI"],

        "NOM":
            x["NOM"],

        "PED":
            x["PED"],

        "VRLL":
            x["VRLL"],

        "TIPO_PEDIDO":
            x["TIPO_PEDIDO"],

        "TM":
            x["TM"],

        "DOC":
            x["DOC"],

        "CANT":
            x["CANT"],

        "BONI":
            x["BONI"],

        "DTO":
            x.get("DTO", 0),

        "CLAING":
            x.get("CLAING", 0),

        "USUARIO":
            x.get("USUARIO", ""),

        "COSTO":
            x["COSTO"],

        "IMP":
            x["IMP"],

        "UTILIDAD":
            x["UTILIDAD"],

        "PUTIL":
            x["PUTIL"],

        "IVA":
            x["IVA"]
    }

    detalle_salida.append(
        fila
    )


with SALIDA_DETALLE.open(

    "w",

    newline="",

    encoding="utf-8-sig"

) as f:

    w = csv.DictWriter(

        f,

        fieldnames=campos_detalle,

        delimiter=";"
    )

    w.writeheader()

    w.writerows(
        detalle_salida
    )


guardar(
    SALIDA_TOTAL,
    resultado
)

guardar(
    SALIDA_PERDIDAS,
    perdidas
)


print()
print("=" * 70)

print("COSVEN")

print("=" * 70)

print(
    "Periodo:",
    WDF,
    "-",
    WHF
)

print(
    "Movimientos:",
    len(ventas)
)

print(
    "Articulos totalizados:",
    len(resultado)
)

print(
    "Articulos con utilidad negativa:",
    len(perdidas)
)

print(
    "Total:",
    SALIDA_TOTAL
)

print(
    "Perdidas:",
    SALIDA_PERDIDAS
)

print(
    "Detalle:",
    SALIDA_DETALLE
)


print()
print("10 MAYORES PERDIDAS")


for x in perdidas[:10]:

    print(

        x["XFLIA"],
        x["XART"],

        x["DET"][:35],

        "Venta:",
        x["IMP"],

        "Costo:",
        x["COSTO"],

        "Utilidad:",
        x["UTILIDAD"],

        "%:",
        x["PUTIL"]
    )
print("Detalle:", SALIDA_DETALLE)
