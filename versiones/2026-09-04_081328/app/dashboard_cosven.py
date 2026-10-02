from pathlib import Path
from io import BytesIO
from datetime import date, datetime, timedelta
import inspect
import sqlite3
import base64

import pandas as pd
import streamlit as st

ROOT = Path(r"C:\Paykan\COSVEN")
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
DB_PATH = DATA / "cosven.db"

LOGO = ASSETS / "logo_paykan.svg"
HERO = ASSETS / "hero_logistica.webp"
DEPOSITO = ASSETS / "deposito_paykan.webp"

AZUL = "#101579"
AZUL_OSCURO = "#090D68"
CELESTE = "#35C8F0"
TEXTO = "#14172B"
GRIS = "#667085"
BORDE = "#E6E9F2"
FONDO_SUAVE = "#F7F9FC"

st.set_page_config(
    page_title="Paykan | Costo de Ventas por Artículo",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
        .block-container {{
            max-width: 1580px;
            padding-top: 1rem;
            padding-bottom: 2.5rem;
        }}

        [data-testid="stToolbar"],
        [data-testid="stAppDeployButton"],
        #MainMenu,
        footer {{ display: none !important; }}

        header[data-testid="stHeader"] {{ background: transparent; }}

        [data-testid="stSidebar"] {{
            background: {FONDO_SUAVE};
            border-right: 1px solid {BORDE};
        }}

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {{
            font-size: 0.98rem;
        }}

        h1, h2, h3 {{
            color: {TEXTO};
            letter-spacing: -0.02em;
        }}

        .paykan-kicker {{
            color: {AZUL};
            font-size: .9rem;
            font-weight: 750;
            letter-spacing: .06em;
            margin-bottom: .35rem;
        }}

        .paykan-title {{
            color: {TEXTO};
            font-size: 2.45rem;
            line-height: 1.05;
            font-weight: 780;
            letter-spacing: -.045em;
            margin: 0;
        }}

        .paykan-subtitle {{
            color: {GRIS};
            font-size: 1.05rem;
            line-height: 1.55;
            margin-top: .8rem;
            max-width: 800px;
        }}

        .update-chip {{
            display: inline-block;
            margin-top: .7rem;
            padding: .46rem .78rem;
            background: #F0F4FF;
            color: {AZUL};
            border: 1px solid #DCE4FF;
            border-radius: 999px;
            font-weight: 650;
            font-size: .86rem;
        }}

        [data-testid="stMetric"] {{
            background: white;
            border: 1px solid {BORDE};
            border-radius: 14px;
            padding: 1.0rem 1.1rem;
            box-shadow: 0 5px 18px rgba(16,21,121,.04);
        }}

        [data-testid="stMetricLabel"] {{
            color: {GRIS};
            font-size: .94rem;
        }}

        [data-testid="stMetricValue"] {{
            color: {AZUL_OSCURO};
            font-weight: 750;
            font-size: 1.65rem;
        }}

        .section-eyebrow {{
            color: {AZUL};
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: .25rem;
        }}

        .section-title {{
            color: {TEXTO};
            font-size: 1.5rem;
            font-weight: 750;
            margin-bottom: .35rem;
        }}

        .section-note {{
            color: {GRIS};
            font-size: .98rem;
            line-height: 1.5;
            margin-bottom: 1rem;
        }}

        .natural-box {{
            background: linear-gradient(135deg,#F7FAFF 0%,#FFFFFF 100%);
            border: 1px solid {BORDE};
            border-left: 4px solid {CELESTE};
            border-radius: 12px;
            padding: 1.15rem 1.3rem;
            color: {TEXTO};
            font-size: 1rem;
            line-height: 1.7;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDE};
            border-radius: 12px;
            overflow: hidden;
        }}

        .selected-product {{
            background: #F7F9FF;
            border: 1px solid #DDE4FF;
            border-radius: 12px;
            padding: .9rem 1.05rem;
            margin: .4rem 0 1rem 0;
            color: {AZUL_OSCURO};
            font-size: 1.08rem;
            font-weight: 700;
        }}

        .paykan-footer {{
            margin-top: 2.4rem;
            background: {AZUL_OSCURO};
            color: white;
            border-radius: 14px;
            padding: 1.15rem 1.5rem;
            font-size: .84rem;
        }}

        .paykan-footer strong {{ color: white; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def ro_connect():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def meta():
    if not DB_PATH.exists():
        return {}
    with ro_connect() as con:
        try:
            return dict(con.execute("SELECT clave, valor FROM metadata").fetchall())
        except sqlite3.Error:
            return {}


def rango_disponible():
    with ro_connect() as con:
        x = con.execute("SELECT MIN(fecha), MAX(fecha) FROM cosven_detalle").fetchone()
    if not x or not x[0]:
        return None, None
    return date.fromisoformat(x[0]), date.fromisoformat(x[1])


def cargar_rango(desde, hasta):
    sql = """
        SELECT
            familia AS XFLIA,
            articulo AS XART,
            descripcion AS DET,
            familia_new AS FLIANEW,
            familia_desc AS FAMILIA_DESC,
            fecha AS FECHA,
            cliente AS CLI,
            nombre_cliente AS NOM,
            pedido AS PED,
            vrll AS VRLL,
            tipo_pedido AS TIPO_PEDIDO,
            tm AS TM,
            documento AS DOC,
            cantidad AS CANT,
            bonificacion AS BONI,
            costo AS COSTO,
            venta AS IMP,
            utilidad AS UTILIDAD,
            putil AS PUTIL,
            iva AS IVA
        FROM cosven_detalle
        WHERE fecha BETWEEN ? AND ?
    """
    with ro_connect() as con:
        df = pd.read_sql_query(sql, con, params=(desde.isoformat(), hasta.isoformat()))
    if not df.empty:
        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
    return df



def cargar_catalogos():
    """Catálogos estables para que los filtros no cambien de opciones al mover fechas."""
    with ro_connect() as con:
        clientes = pd.read_sql_query(
            """
            SELECT cliente AS CLI, MAX(nombre_cliente) AS NOM
            FROM cosven_detalle
            WHERE cliente IS NOT NULL AND cliente > 0
            GROUP BY cliente
            ORDER BY NOM, CLI
            """,
            con,
        )
        tipos = [
            r[0]
            for r in con.execute(
                """
                SELECT DISTINCT tipo_pedido
                FROM cosven_detalle
                WHERE TRIM(COALESCE(tipo_pedido,'')) <> ''
                ORDER BY tipo_pedido
                """
            ).fetchall()
        ]
        familias = pd.read_sql_query(
            """
            SELECT familia AS XFLIA, MAX(familia_desc) AS FAMILIA_DESC
            FROM cosven_detalle
            GROUP BY familia
            ORDER BY familia
            """,
            con,
        )
    return clientes, tipos, familias

def money(v):
    return f"$ {v:,.2f}"


def pct(v):
    return f"{v:,.2f} %"


def img_circle(path, size=230):
    if not path.exists():
        return ""
    mime = "image/webp" if path.suffix.lower() == ".webp" else "image/png"
    raw = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;">
      <img src="data:{mime};base64,{raw}" style="width:{size}px;height:{size}px;object-fit:cover;border-radius:50%;box-shadow:0 10px 28px rgba(9,13,104,.12);" />
    </div>
    """


def agregar_por_articulo(df):
    if df.empty:
        return pd.DataFrame()
    claves = ["XFLIA", "XART", "DET", "FLIANEW", "FAMILIA_DESC", "IVA"]
    agg = (
        df.groupby(claves, dropna=False, as_index=False)[["CANT", "BONI", "IMP", "COSTO"]]
        .sum()
    )
    agg["UTILIDAD"] = agg["IMP"] - agg["COSTO"]
    agg["PUTIL"] = 0.0
    ok = agg["COSTO"] > 0
    agg.loc[ok, "PUTIL"] = (agg.loc[ok, "IMP"] / agg.loc[ok, "COSTO"] - 1) * 100
    return agg


# ------------------------------------------------------------
# Validación de base local
# ------------------------------------------------------------
if not DB_PATH.exists():
    st.error("La base histórica local todavía no fue inicializada.")
    st.code(r"C:\Paykan\COSVEN\inicializar_2026.bat", language=None)
    st.stop()

min_fecha, max_fecha = rango_disponible()
if min_fecha is None:
    st.error("La base local existe pero no contiene movimientos COSVEN.")
    st.stop()

info = meta()
ultima = info.get("ultima_actualizacion", "")
try:
    ultima_txt = datetime.fromisoformat(ultima).strftime("%d/%m/%Y %H:%M")
except Exception:
    ultima_txt = "sin dato"

# ------------------------------------------------------------
# Encabezado Paykan
# ------------------------------------------------------------
head1, head2 = st.columns([1.15, .85], vertical_alignment="center")
with head1:
    if LOGO.exists():
        st.image(str(LOGO), width=145)
    st.markdown(
        """
        <div class="paykan-kicker">INFORME DE RENTABILIDAD</div>
        <div class="paykan-title">Costo de Ventas por Artículo</div>
        <div class="paykan-subtitle">
            Consulta de resultados por producto con trazabilidad hasta la venta individual.
            La pantalla abre siempre con la información del día anterior.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="update-chip">Última actualización local: {ultima_txt}</span>',
        unsafe_allow_html=True,
    )
with head2:
    if HERO.exists():
        st.image(str(HERO), width=430)

st.write("")

# ------------------------------------------------------------
# Fechas: SIEMPRE ayer al cargar una nueva sesión
# ------------------------------------------------------------
ayer = date.today() - timedelta(days=1)
if "cosven_desde" not in st.session_state:
    st.session_state.cosven_desde = ayer
if "cosven_hasta" not in st.session_state:
    st.session_state.cosven_hasta = ayer

st.markdown(
    """
    <div class="section-eyebrow">Período</div>
    <div class="section-title">Fecha de consulta</div>
    <div class="section-note">Por defecto se muestra el día anterior. Si necesitás más información, ampliá el rango.</div>
    """,
    unsafe_allow_html=True,
)

d1, d2, d3 = st.columns([.23, .23, .54])
with d1:
    desde = st.date_input("Desde", key="cosven_desde", format="DD/MM/YYYY")
with d2:
    hasta = st.date_input("Hasta", key="cosven_hasta", format="DD/MM/YYYY")
with d3:
    st.write("")
    st.caption(f"Histórico disponible: {min_fecha:%d/%m/%Y} al {max_fecha:%d/%m/%Y}")

if desde > hasta:
    st.error("La fecha Desde no puede ser posterior a Hasta.")
    st.stop()

# Permitimos elegir fechas sin data para que el comportamiento sea transparente.
df = cargar_rango(desde, hasta)

# ------------------------------------------------------------
# Filtros
# ------------------------------------------------------------
st.sidebar.markdown("## Filtros")
st.sidebar.caption(f"Período: {desde:%d/%m/%Y} — {hasta:%d/%m/%Y}")

solo_perdidas = st.sidebar.checkbox("Mostrar solo artículos con pérdida", value=True)

if df.empty:
    extra = ""
    if hasta > max_fecha:
        extra = f" Último día disponible en la base local: {max_fecha:%d/%m/%Y}."
    st.info(
        f"No hay datos locales para {desde:%d/%m/%Y}" +
        (f" al {hasta:%d/%m/%Y}" if hasta != desde else "") +
        ". La vista inicial continúa siendo siempre el día anterior." + extra
    )
    st.stop()

# Catálogos globales: permanecen estables aunque el usuario cambie el rango.
clientes, all_tipos, familias = cargar_catalogos()

# Clientes / farmacias a excluir
cliente_nombre = {
    int(r.CLI): (str(r.NOM).strip() or f"Cliente {int(r.CLI)}")
    for r in clientes.itertuples()
}
cliente_opts = list(cliente_nombre.keys())
excluir_clientes = st.sidebar.multiselect(
    "Excluir farmacias / clientes",
    options=cliente_opts,
    default=[],
    format_func=lambda x: f"{x} - {cliente_nombre.get(x, '')}",
    placeholder="Ninguno excluido",
)

# Tipo de pedido exacto registrado
tipos_sel = st.sidebar.multiselect(
    "Tipo de pedido",
    options=all_tipos,
    default=all_tipos,
    placeholder="Seleccionar tipos",
)

# Familia
fam_labels = {
    int(r.XFLIA): (str(r.FAMILIA_DESC).strip() or "Sin descripción")
    for r in familias.itertuples()
}
fam_opts = ["Todas"] + [int(x) for x in familias["XFLIA"].tolist()]
familia_sel = st.sidebar.selectbox(
    "Familia",
    fam_opts,
    format_func=lambda x: "Todas" if x == "Todas" else f"{x} - {fam_labels.get(x, '')}",
)

buscar = st.sidebar.text_input("Buscar artículo", placeholder="Código o descripción")

# ------------------------------------------------------------
# Aplicar filtros de negocio SOBRE EL DETALLE y recién después totalizar
# ------------------------------------------------------------
filtrado = df.copy()

if excluir_clientes:
    filtrado = filtrado[~filtrado["CLI"].isin(excluir_clientes)]

if all_tipos:
    if tipos_sel:
        filtrado = filtrado[filtrado["TIPO_PEDIDO"].isin(tipos_sel)]
    else:
        filtrado = filtrado.iloc[0:0]

if familia_sel != "Todas":
    filtrado = filtrado[filtrado["XFLIA"].astype(int) == int(familia_sel)]

if buscar.strip():
    q = buscar.strip().lower()
    codigos = (
        filtrado["XFLIA"].astype(int).astype(str).str.zfill(3)
        + "-"
        + filtrado["XART"].astype(int).astype(str).str.zfill(4)
    )
    mask = (
        filtrado["DET"].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        | codigos.str.lower().str.contains(q, regex=False)
        | filtrado["XART"].astype(int).astype(str).str.contains(q, regex=False)
    )
    filtrado = filtrado[mask]

resumen = agregar_por_articulo(filtrado)

# KPIs siempre responden a fecha/cliente/tipo/familia/artículo.
# El switch "solo pérdida" es únicamente de presentación de la tabla.
venta_total = float(filtrado["IMP"].sum()) if not filtrado.empty else 0.0
costo_total = float(filtrado["COSTO"].sum()) if not filtrado.empty else 0.0
utilidad_total = venta_total - costo_total
putil_total = ((venta_total / costo_total) - 1) * 100 if costo_total > 0 else 0.0
neg = resumen[resumen["UTILIDAD"] < 0] if not resumen.empty else resumen
cant_neg = len(neg)
perdida_acum = abs(float(neg["UTILIDAD"].sum())) if not neg.empty else 0.0

st.write("")
cols = st.columns(6)
cols[0].metric("Venta", money(venta_total))
cols[1].metric("Costo", money(costo_total))
cols[2].metric("Utilidad", money(utilidad_total))
cols[3].metric("% Utilidad", pct(putil_total))
cols[4].metric("Artículos con pérdida", f"{cant_neg:,}")
cols[5].metric("Pérdida acumulada", money(perdida_acum))

# ------------------------------------------------------------
# Resultados
# ------------------------------------------------------------
st.write("")
st.markdown(
    """
    <div class="section-eyebrow">Resultados</div>
    <div class="section-title">Resultado por artículo</div>
    <div class="section-note">Hacé clic sobre una fila para abrir debajo el detalle de ventas del producto.</div>
    """,
    unsafe_allow_html=True,
)

mostrar = resumen.copy()
if solo_perdidas:
    mostrar = mostrar[mostrar["UTILIDAD"] < 0]
    mostrar = mostrar.sort_values(["UTILIDAD", "XFLIA", "XART"])
else:
    mostrar = mostrar.sort_values(["XFLIA", "XART"])
mostrar = mostrar.reset_index(drop=True)

if mostrar.empty:
    st.info("No hay artículos que cumplan los filtros seleccionados.")
    st.stop()

vista = mostrar.rename(columns={
    "XFLIA": "Familia",
    "XART": "Artículo",
    "DET": "Descripción",
    "FAMILIA_DESC": "Descripción familia",
    "CANT": "Cantidad",
    "BONI": "Bonificación",
    "IMP": "Venta",
    "COSTO": "Costo",
    "UTILIDAD": "Utilidad",
    "PUTIL": "% Utilidad",
})

cols_tabla = [
    "Familia", "Artículo", "Descripción", "Descripción familia",
    "Cantidad", "Bonificación", "Venta", "Costo", "Utilidad", "% Utilidad"
]

config = {
    "Familia": st.column_config.NumberColumn(width="small", format="%d"),
    "Artículo": st.column_config.NumberColumn(width="small", format="%d"),
    "Descripción": st.column_config.TextColumn(width="large"),
    "Descripción familia": st.column_config.TextColumn(width="medium"),
    "Cantidad": st.column_config.NumberColumn(width="small", format="%.2f"),
    "Bonificación": st.column_config.NumberColumn(width="small", format="%.2f"),
    "Venta": st.column_config.NumberColumn(width="medium", format="$ %.2f"),
    "Costo": st.column_config.NumberColumn(width="medium", format="$ %.2f"),
    "Utilidad": st.column_config.NumberColumn(width="medium", format="$ %.2f"),
    "% Utilidad": st.column_config.NumberColumn(width="small", format="%.2f %%"),
}

selected_key = None
supports_selection = "on_select" in inspect.signature(st.dataframe).parameters

if supports_selection:
    event = st.dataframe(
        vista[cols_tabla],
        width="stretch",
        height=520,
        hide_index=True,
        row_height=42,
        column_config=config,
        on_select="rerun",
        selection_mode="single-row",
        key="resultado_articulos",
    )
    rows = getattr(getattr(event, "selection", None), "rows", [])
    if rows:
        idx = rows[0]
        if 0 <= idx < len(mostrar):
            r = mostrar.iloc[idx]
            selected_key = (int(r["XFLIA"]), int(r["XART"]))
            st.session_state["articulo_seleccionado"] = selected_key
else:
    st.dataframe(
        vista[cols_tabla],
        width="stretch",
        height=520,
        hide_index=True,
        row_height=42,
        column_config=config,
    )
    st.caption("Esta versión de Streamlit no admite selección por clic. Se habilita un selector de compatibilidad.")
    opciones = [
        (int(r.XFLIA), int(r.XART), str(r.DET))
        for r in mostrar.itertuples()
    ]
    x = st.selectbox(
        "Artículo para ver detalle",
        options=opciones,
        format_func=lambda z: f"{z[0]:03d}-{z[1]:04d} | {z[2]}",
    )
    if x:
        selected_key = (x[0], x[1])
        st.session_state["articulo_seleccionado"] = selected_key

if selected_key is None:
    selected_key = st.session_state.get("articulo_seleccionado")

# Invalidar selección si ya no existe por cambio de filtros
valid_keys = set(zip(mostrar["XFLIA"].astype(int), mostrar["XART"].astype(int)))
if selected_key not in valid_keys:
    selected_key = None
    st.session_state.pop("articulo_seleccionado", None)

# ------------------------------------------------------------
# Detalle al hacer clic
# ------------------------------------------------------------
st.write("")
st.markdown(
    """
    <div class="section-eyebrow">Trazabilidad</div>
    <div class="section-title">Detalle de ventas del artículo</div>
    """,
    unsafe_allow_html=True,
)

if selected_key is None:
    st.info("Seleccioná un artículo en la tabla de resultados para ver sus movimientos.")
else:
    fsel, asel = selected_key
    art_rows = mostrar[
        (mostrar["XFLIA"].astype(int) == fsel)
        & (mostrar["XART"].astype(int) == asel)
    ]
    desc = str(art_rows.iloc[0]["DET"]) if not art_rows.empty else ""
    st.markdown(
        f'<div class="selected-product">{fsel:03d}-{asel:04d} &nbsp;|&nbsp; {desc}</div>',
        unsafe_allow_html=True,
    )

    det = filtrado[
        (filtrado["XFLIA"].astype(int) == fsel)
        & (filtrado["XART"].astype(int) == asel)
    ].copy().sort_values(["FECHA", "TM", "DOC"])

    dv = float(det["IMP"].sum())
    dc = float(det["COSTO"].sum())
    du = dv - dc
    dp = ((dv / dc) - 1) * 100 if dc > 0 else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Movimientos", f"{len(det):,}")
    k2.metric("Venta", money(dv))
    k3.metric("Costo", money(dc))
    k4.metric("Utilidad", money(du))
    k5.metric("% Utilidad", pct(dp))

    detv = det.rename(columns={
        "FECHA": "Fecha",
        "CLI": "Cliente",
        "NOM": "Nombre cliente",
        "PED": "Pedido",
        "TIPO_PEDIDO": "Tipo pedido",
        "TM": "TM",
        "DOC": "Documento",
        "CANT": "Cantidad",
        "BONI": "Bonificación",
        "IMP": "Venta",
        "COSTO": "Costo",
        "UTILIDAD": "Utilidad",
        "PUTIL": "% Utilidad",
    })
    det_cols = [
        "Fecha", "Cliente", "Nombre cliente", "Pedido", "Tipo pedido",
        "TM", "Documento", "Cantidad", "Bonificación", "Venta", "Costo",
        "Utilidad", "% Utilidad"
    ]
    st.dataframe(
        detv[det_cols],
        width="stretch",
        height=430,
        hide_index=True,
        row_height=40,
        column_config={
            "Fecha": st.column_config.DateColumn(width="small", format="DD/MM/YYYY"),
            "Cliente": st.column_config.NumberColumn(width="small", format="%d"),
            "Nombre cliente": st.column_config.TextColumn(width="large"),
            "Pedido": st.column_config.NumberColumn(width="small", format="%d"),
            "Tipo pedido": st.column_config.TextColumn(width="medium"),
            "Documento": st.column_config.NumberColumn(width="small", format="%d"),
            "Venta": st.column_config.NumberColumn(width="medium", format="$ %.2f"),
            "Costo": st.column_config.NumberColumn(width="medium", format="$ %.2f"),
            "Utilidad": st.column_config.NumberColumn(width="medium", format="$ %.2f"),
            "% Utilidad": st.column_config.NumberColumn(width="small", format="%.2f %%"),
        },
    )

# ------------------------------------------------------------
# Exportación
# ------------------------------------------------------------
st.write("")
with st.expander("Descargar resultados filtrados"):
    csv_data = vista[cols_tabla].to_csv(index=False, sep=";").encode("utf-8-sig")
    e1, e2 = st.columns(2)
    e1.download_button(
        "Descargar CSV",
        data=csv_data,
        file_name=f"cosven_{desde:%Y%m%d}_{hasta:%Y%m%d}.csv",
        mime="text/csv",
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        vista[cols_tabla].to_excel(writer, sheet_name="COSVEN", index=False)
    e2.download_button(
        "Descargar Excel",
        data=buffer.getvalue(),
        file_name=f"cosven_{desde:%Y%m%d}_{hasta:%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ------------------------------------------------------------
# Explicación natural incorporada
# ------------------------------------------------------------
st.write("")
st.markdown(
    """
    <div class="section-eyebrow">Ayuda</div>
    <div class="section-title">Qué hace este informe y cómo funciona</div>
    """,
    unsafe_allow_html=True,
)

h1, h2 = st.columns([.28, .72], vertical_alignment="center")
with h1:
    html = img_circle(DEPOSITO, 235)
    if html:
        st.markdown(html, unsafe_allow_html=True)
with h2:
    st.markdown(
        """
        <div class="natural-box">
            <strong>¿Qué hace?</strong><br>
            Analiza las ventas del período seleccionado y permite identificar los artículos
            cuyo resultado fue negativo. La pantalla abre siempre con el <strong>día anterior</strong>.
            Si se necesita más información, el usuario puede ampliar las fechas con los calendarios Desde y Hasta.<br><br>

            <strong>¿Cómo se calcula?</strong><br>
            Cada operación ya tiene determinado su costo histórico siguiendo la lógica COSVEN de Paykan.
            El dashboard primero aplica los filtros elegidos —fecha, farmacias o clientes excluidos,
            tipo de pedido, familia y artículo— y recién después vuelve a totalizar.
            La utilidad se calcula como <strong>Venta − Costo</strong> y el porcentaje como
            <strong>(Venta / Costo − 1) × 100</strong> cuando el costo es mayor que cero.<br><br>

            <strong>¿Qué pasa si excluyo una farmacia o cambio el tipo de pedido?</strong><br>
            Esas operaciones dejan de participar en el resultado mostrado. Se recalculan la venta,
            el costo, la utilidad, el porcentaje, la cantidad de artículos con pérdida y la tabla de resultados.<br><br>

            <strong>¿Cómo veo el origen del resultado?</strong><br>
            Haciendo clic sobre un producto se muestran debajo sus operaciones individuales con fecha,
            cliente, pedido, tipo de pedido, documento, cantidades, venta, costo y utilidad.
            Los movimientos sin pedido asociado se identifican como <strong>Sin pedido</strong>.<br><br>

            <strong>Actualización de datos</strong><br>
            Los meses cerrados quedan almacenados localmente. La actualización automática reconstruye
            solamente el mes que contiene el día anterior, porque ese es el período que todavía puede recibir ajustes.
            Los DBF operativos se consultan únicamente en modo lectura.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="paykan-footer">
        <strong>Paykan</strong> · Informe interno de costo de ventas por artículo
    </div>
    """,
    unsafe_allow_html=True,
)
