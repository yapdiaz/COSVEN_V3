from pathlib import Path
from io import BytesIO
from datetime import date, datetime, timedelta
import inspect
import sqlite3
import base64
import hashlib
import json
import traceback
import unicodedata
import uuid
import subprocess

import pandas as pd
import streamlit as st

ROOT = Path(r"C:\Paykan\COSVEN")
DATA = ROOT / "data"
ASSETS = ROOT / "assets"
DB_PATH = DATA / "cosven.db"
UPDATE_LOCK = ROOT / "cache" / "actualizacion.lock"
UPDATE_TASK_MANUAL = "Paykan COSVEN Actualizacion Manual"
LAB_CSV = Path(r"C:\editorPaykanVentas\CSV\Laboratorio.csv")

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
            font-size: 1.52rem;
        }}



        /* El detalle usa prácticamente todo el ancho del escritorio. */
        div[data-testid="stDialog"] div[role="dialog"] {{
            width: 98vw !important;
            max-width: 98vw !important;
            padding-left: .65rem !important;
            padding-right: .65rem !important;
        }}

        div[data-testid="stDialog"] [data-testid="stDataFrame"] {{
            width: 100% !important;
            max-width: 100% !important;
        }}

        /* Tarjetas KPI principales: fondos suaves, mejor contraste y lectura */
        .st-key-kpi_resumen [data-testid="stMetric"] {{
            border-radius: 14px;
            padding: 1rem 1.05rem;
            box-shadow: 0 5px 18px rgba(16,21,121,.05);
            min-height: 112px;
        }}

        .st-key-kpi_resumen [data-testid="stMetricValue"] {{
            font-size: 1.10rem !important;
            line-height: 1.10;
            white-space: nowrap !important;
            overflow: visible !important;
        }}

        .st-key-kpi_resumen [data-testid="stMetricLabel"] {{
            font-size: .88rem !important;
        }}

        /* Bordes más visibles en filtros y controles */
        [data-testid="stTextInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
            border: 1px solid #C9D2E3 !important;
            border-radius: 10px !important;
            box-shadow: none !important;
        }}

        [data-testid="stTextInput"] input:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within {{
            border-color: #A8B7D9 !important;
            box-shadow: 0 0 0 1px #A8B7D9 !important;
        }}

        [data-baseweb="tag"] {{
            background: #EEF2FF !important;
            border: 1px solid #CBD5F5 !important;
            border-radius: 8px !important;
        }}

        [data-baseweb="tag"] span,
        [data-baseweb="tag"] svg {{
            color: #101579 !important;
            fill: #101579 !important;
        }}

        /* Más altura visible para Farmacias, Tipo de pedido y Laboratorios */
        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] > div {{
            min-height: 220px !important;
            max-height: 220px !important;
            overflow-y: auto !important;
            align-items: flex-start !important;
            align-content: flex-start !important;
            padding-top: .45rem !important;
            padding-bottom: .45rem !important;
        }}

        [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] {{
            min-height: 220px !important;
        }}

        .st-key-kpi_resumen [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"] {{
            background: #EEF8F2;
            border: 1px solid #D7ECDD;
        }}

        .st-key-kpi_resumen [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] {{
            background: #FFF1F2;
            border: 1px solid #F5DADD;
        }}

        .st-key-kpi_resumen [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] {{
            background: #EDF5FF;
            border: 1px solid #D7E7FA;
        }}

        .st-key-kpi_resumen [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] {{
            background: #F4F0FF;
            border: 1px solid #E4DCF8;
        }}

        .st-key-kpi_resumen [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(5) [data-testid="stMetric"] {{
            background: #FFF8E8;
            border: 1px solid #F2E4BE;
        }}

        .st-key-kpi_resumen [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(6) [data-testid="stMetric"] {{
            background: #FFF2EE;
            border: 1px solid #F0DDD5;
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

        /* Mantener el popup amplio también en resoluciones intermedias. */
        div[data-testid="stDialog"] div[role="dialog"] {{
            width: 98vw !important;
            max-width: 98vw !important;
        }}

        div[data-testid="stDialog"] [data-testid="stDataFrame"] {{
            min-height: 520px;
        }}

        .support-box {{
            background: #FFF8E8;
            border: 1px solid #F3D58B;
            border-left: 4px solid #D99A00;
            border-radius: 12px;
            padding: 1rem 1.15rem;
            color: #4A3A10;
            line-height: 1.55;
            margin: .6rem 0 1rem 0;
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


LOG_DIR = ROOT / "logs"
ERROR_LOG = LOG_DIR / "dashboard_errores.log"


def session_ref():
    if "cosven_session_ref" not in st.session_state:
        st.session_state["cosven_session_ref"] = uuid.uuid4().hex[:8].upper()
    return st.session_state["cosven_session_ref"]


def registrar_error(codigo, seccion, exc, contexto=None):
    """Guarda el detalle técnico para TI. Nunca se muestra el traceback al usuario."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write("\n" + "=" * 88 + "\n")
            f.write(f"Fecha: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"Código: {codigo}\n")
            f.write(f"Sesión: {session_ref()}\n")
            f.write(f"Sección: {seccion}\n")
            estado = {
                "desde": st.session_state.get("cosven_desde"),
                "hasta": st.session_state.get("cosven_hasta"),
                "solo_perdidas": st.session_state.get("filtro_solo_perdidas"),
                "clientes_excluidos": st.session_state.get("filtro_excluir_clientes"),
                "tipos_pedido": st.session_state.get("filtro_tipos_pedido"),
                "tipo_producto": st.session_state.get("filtro_tipo_producto"),
                "buscar": st.session_state.get("filtro_buscar"),
            }
            f.write("Filtros: " + json.dumps(estado, ensure_ascii=False, default=str) + "\n")
            if contexto:
                f.write("Contexto: " + json.dumps(contexto, ensure_ascii=False, default=str) + "\n")
            f.write(f"Error: {type(exc).__name__}: {exc}\n")
            f.write(traceback.format_exc())
            f.write("\n")
    except Exception:
        # El registro de un error nunca debe provocar otro error visible.
        pass


def aviso_usuario(titulo, explicacion, accion, codigo, tipo="info"):
    texto = (
        f"**{titulo}**\n\n"
        f"{explicacion}\n\n"
        f"**Qué puede hacer:** {accion}\n\n"
        f"Referencia para TI: `{codigo}`"
    )
    if tipo == "error":
        st.error(texto)
    elif tipo == "warning":
        st.warning(texto)
    else:
        st.info(texto)


def error_interno(codigo, seccion, exc, contexto=None):
    registrar_error(codigo, seccion, exc, contexto)
    aviso_usuario(
        "No fue posible completar esta consulta.",
        "Ocurrió un problema interno mientras se procesaban los datos del informe. "
        "No es necesario cambiar los filtros para intentar corregirlo.",
        "Vuelva a intentar. Si el mensaje continúa, comuníquese con TI e indique la referencia que aparece abajo.",
        codigo,
        tipo="error",
    )


def meta():
    if not DB_PATH.exists():
        return {}
    with ro_connect() as con:
        try:
            return dict(con.execute("SELECT clave, valor FROM metadata").fetchall())
        except sqlite3.Error:
            return {}


def iniciar_actualizacion_manual():
    """Solicita al Programador de tareas la actualización manual.
    La tarea usa las credenciales configuradas por TI para acceder al UNC.
    """
    try:
        if UPDATE_LOCK.exists():
            return False, "Ya hay una actualización en curso."

        p = subprocess.run(
            [
                "schtasks.exe",
                "/Run",
                "/TN",
                UPDATE_TASK_MANUAL,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        if p.returncode != 0:
            return (
                False,
                "La actualización manual todavía no está configurada en el Programador de tareas.",
            )

        return True, "Actualización iniciada."

    except Exception as exc:
        registrar_error(
            "COSVEN-U003",
            "Inicio de actualización manual",
            exc,
        )
        return False, "No fue posible iniciar la actualización manual."


def rango_disponible():
    with ro_connect() as con:
        x = con.execute("SELECT MIN(fecha), MAX(fecha) FROM cosven_detalle").fetchone()
    if not x or not x[0]:
        return None, None
    return date.fromisoformat(x[0]), date.fromisoformat(x[1])


def ultima_fecha_con_movimientos(hasta_objetivo):
    """Último día que realmente tiene movimientos, sin pasar la fecha objetivo."""
    with ro_connect() as con:
        x = con.execute(
            "SELECT MAX(fecha) FROM cosven_detalle WHERE fecha <= ?",
            (hasta_objetivo.isoformat(),),
        ).fetchone()

    if not x or not x[0]:
        return None

    return date.fromisoformat(x[0])


def cargar_rango(desde, hasta):
    with ro_connect() as con:
        columnas_db = {
            str(r[1]).lower()
            for r in con.execute("PRAGMA table_info(cosven_detalle)").fetchall()
        }

        dto_sql = "descuento AS DTO" if "descuento" in columnas_db else "0 AS DTO"
        usuario_sql = "usuario AS USUARIO" if "usuario" in columnas_db else "'' AS USUARIO"

        sql = f"""
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
                {dto_sql},
                {usuario_sql},
                costo AS COSTO,
                venta AS IMP,
                iva AS IVA
            FROM cosven_detalle
            WHERE fecha BETWEEN ? AND ?
        """

        df = pd.read_sql_query(sql, con, params=(desde.isoformat(), hasta.isoformat()))

    if not df.empty:
        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")
        for c in ["XFLIA", "XART", "CLI", "PED", "DOC", "CANT", "BONI", "DTO", "COSTO", "IMP", "IVA"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        for c in ["DET", "FAMILIA_DESC", "NOM", "VRLL", "TM"]:
            if c in df.columns:
                df[c] = df[c].fillna("").astype(str)
        df["TIPO_PEDIDO"] = (
            df["TIPO_PEDIDO"].fillna("").astype(str).str.strip().replace("", "Sin pedido")
        )
        # La utilidad visible se calcula siempre a partir de Venta y Costo.
        # No dependemos de totales previamente guardados.
        df["UTILIDAD"] = df["IMP"] - df["COSTO"]
        df["PUTIL"] = 0.0
        ok = df["COSTO"] > 0
        df.loc[ok, "PUTIL"] = (df.loc[ok, "IMP"] / df.loc[ok, "COSTO"] - 1) * 100
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
                SELECT DISTINCT
                    CASE
                        WHEN TRIM(COALESCE(tipo_pedido,'')) = '' THEN 'Sin pedido'
                        ELSE TRIM(tipo_pedido)
                    END AS tipo_pedido
                FROM cosven_detalle
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

def cargar_laboratorios():
    """Carga el catálogo externo FLIA -> laboratorio/proveedor sin alterar datos COSVEN."""
    if not LAB_CSV.exists():
        return pd.DataFrame(columns=["FLIA", "DET"]), "no_existe"

    ultimo_error = None
    for enc in ("utf-8-sig", "utf-8", "latin1", "cp1252"):
        try:
            lab = pd.read_csv(LAB_CSV, encoding=enc)
            break
        except Exception as exc:
            ultimo_error = exc
    else:
        raise ultimo_error

    # El CSV actual trae una primera columna de índice sin nombre; no se utiliza.
    requeridas = {"FLIA", "DET"}
    if not requeridas.issubset(set(lab.columns)):
        faltan = sorted(requeridas - set(lab.columns))
        raise ValueError(f"Laboratorio.csv no contiene las columnas requeridas: {', '.join(faltan)}")

    lab = lab[["FLIA", "DET"]].copy()
    lab["FLIA"] = pd.to_numeric(lab["FLIA"], errors="coerce")
    lab["DET"] = lab["DET"].fillna("").astype(str).str.strip()
    lab = lab[lab["FLIA"].notna() & lab["DET"].ne("")]
    lab["FLIA"] = lab["FLIA"].astype(int)

    # Si el archivo tuviera una familia repetida, conservar la primera denominación
    # no vacía tal como aparece en el catálogo fuente.
    lab = lab.drop_duplicates(subset=["FLIA"], keep="first")
    return lab.reset_index(drop=True), "ok"


def normalizar_busqueda(valor):
    """Texto normalizado para búsquedas por nombre sin depender de mayúsculas o acentos."""
    s = str(valor or "").strip().lower()
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(ch)
    )


def reset_farmacias():
    """Vuelve a incluir todas las farmacias marcadas/desmarcadas durante la sesión."""
    for k in list(st.session_state.keys()):
        if str(k).startswith("farmacia_incluida_"):
            st.session_state[k] = True


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
    columnas = [
        "XFLIA", "XART", "DET", "FLIANEW", "FAMILIA_DESC", "IVA",
        "CANT", "BONI", "IMP", "COSTO", "UTILIDAD", "PUTIL"
    ]
    if df.empty:
        return pd.DataFrame(columns=columnas)
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


def detalle_dataframe(det):
    detv = det.rename(columns={
        "FECHA": "Fecha",
        "CLI": "Cliente",
        "NOM": "Nombre cliente",
        "PED": "Pedido",
        "TIPO_PEDIDO": "Tipo pedido",
        "USUARIO": "Usuario pedido",
        "TM": "TM",
        "DOC": "Documento",
        "CANT": "Cantidad",
        "BONI": "Bonificación",
        "DTO": "Descuento",
        "IMP": "Venta",
        "COSTO": "Costo",
        "UTILIDAD": "Utilidad",
        "PUTIL": "% Utilidad",
    })

    cols_pantalla = [
        "Fecha", "Cliente", "Nombre cliente", "Pedido", "Tipo pedido",
        "TM", "Documento", "Cantidad", "Bonificación", "Descuento",
        "Venta", "Costo", "Utilidad", "% Utilidad", "Usuario pedido"
    ]

    # Se mantienen las exportaciones existentes sin cambios, por pedido del usuario.
    cols_exportacion = [
        "Fecha", "Cliente", "Nombre cliente", "Pedido", "Tipo pedido",
        "TM", "Documento", "Cantidad", "Bonificación", "Venta", "Costo",
        "Utilidad", "% Utilidad"
    ]

    return detv, cols_pantalla, cols_exportacion


def render_detalle_contenido(det, fsel, asel, desc, desde, hasta):
    try:
        if det.empty:
            aviso_usuario(
                "El artículo seleccionado no tiene movimientos con los filtros actuales.",
                "El producto existe en el resultado, pero no quedaron operaciones disponibles para mostrar en el detalle.",
                "Cierre esta ventana y revise los filtros de fecha, farmacia o tipo de pedido.",
                "COSVEN-F005",
            )
            return

        st.markdown(
            f'<div class="selected-product">{fsel:03d}-{asel:04d} &nbsp;|&nbsp; {desc}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"Período consultado: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}. "
            "El detalle respeta los mismos filtros aplicados al resultado principal."
        )

        # Las notas de crédito (TM=NC) permanecen visibles en el detalle,
        # pero no participan en los KPI de rentabilidad.
        es_nc_det = det["TM"].fillna("").astype(str).str.strip().str.upper().eq("NC")
        det_rentabilidad = det[~es_nc_det].copy()

        dv = float(det_rentabilidad["IMP"].sum())
        dc = float(det_rentabilidad["COSTO"].sum())
        du = dv - dc
        dp = ((dv / dc) - 1) * 100 if dc > 0 else 0.0

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Movimientos", f"{len(det):,}")
        k2.metric("Venta", money(dv))
        k3.metric("Costo", money(dc))
        k4.metric("Utilidad", money(du))
        k5.metric("% Utilidad", pct(dp))

        if es_nc_det.any():
            st.caption(
                "Las notas de crédito se muestran como referencia, pero no afectan la rentabilidad del artículo, ya que corresponden a ajustes de operaciones anteriores. "
                "Las NC permanecen visibles en el detalle para conservar la trazabilidad."
            )

        detv, det_cols, det_cols_export = detalle_dataframe(det)
        st.dataframe(
            detv[det_cols],
            width="stretch",
            height=560,
            hide_index=True,
            row_height=36,
            column_config={
                "Fecha": st.column_config.DateColumn(width=76, format="DD/MM/YYYY"),
                "Cliente": st.column_config.NumberColumn(width=52, format="%d"),
                "Nombre cliente": st.column_config.TextColumn(width=150),
                "Pedido": st.column_config.NumberColumn(width=64, format="%d"),
                "Tipo pedido": st.column_config.TextColumn(width=100),
                "Usuario pedido": st.column_config.TextColumn(width=92),
                "TM": st.column_config.TextColumn(width=34),
                "Documento": st.column_config.NumberColumn(width=68, format="%d"),
                "Cantidad": st.column_config.NumberColumn(width=56, format="%.2f"),
                "Bonificación": st.column_config.NumberColumn(width=62, format="%.2f"),
                "Descuento": st.column_config.NumberColumn(width=66, format="%.2f %%"),
                "Venta": st.column_config.NumberColumn(width=82, format="$ %.2f"),
                "Costo": st.column_config.NumberColumn(width=82, format="$ %.2f"),
                "Utilidad": st.column_config.NumberColumn(width=84, format="$ %.2f"),
                "% Utilidad": st.column_config.NumberColumn(width=62, format="%.2f %%"),
            },
        )

        st.write("")
        d1, d2 = st.columns(2)
        csv_det = detv[det_cols_export].to_csv(index=False, sep=";").encode("utf-8-sig")
        d1.download_button(
            "Descargar detalle CSV",
            data=csv_det,
            file_name=f"cosven_detalle_{fsel:03d}_{asel:04d}_{desde:%Y%m%d}_{hasta:%Y%m%d}.csv",
            mime="text/csv",
            key=f"csv_det_{fsel}_{asel}_{desde}_{hasta}",
        )
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            detv[det_cols_export].to_excel(writer, sheet_name="Detalle", index=False)
        d2.download_button(
            "Descargar detalle Excel",
            data=buffer.getvalue(),
            file_name=f"cosven_detalle_{fsel:03d}_{asel:04d}_{desde:%Y%m%d}_{hasta:%Y%m%d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"xlsx_det_{fsel}_{asel}_{desde}_{hasta}",
        )
    except Exception as exc:
        error_interno(
            "COSVEN-R004",
            "Detalle de ventas",
            exc,
            {"familia": fsel, "articulo": asel, "desde": desde, "hasta": hasta},
        )


def abrir_detalle_modal(det, fsel, asel, desc, desde, hasta):
    if not hasattr(st, "dialog"):
        aviso_usuario(
            "La ventana de detalle no está disponible en esta instalación.",
            "La versión de Streamlit instalada no admite el popup grande definido para consultar las ventas.",
            "Comuníquese con TI e indique la referencia para actualizar el componente del dashboard.",
            "COSVEN-U001",
            tipo="warning",
        )
        return

    @st.dialog("Detalle de ventas del artículo", width="large")
    def _dialogo():
        render_detalle_contenido(det, fsel, asel, desc, desde, hasta)

    _dialogo()


def render_app():
    # ------------------------------------------------------------
    # Validación de base local
    # ------------------------------------------------------------
    if not DB_PATH.exists():
        aviso_usuario(
            "El informe todavía no tiene datos disponibles.",
            "La base local de consulta no fue inicializada o no está accesible en este momento.",
            "Comuníquese con TI e indique la referencia para que verifiquen la inicialización del informe.",
            "COSVEN-D003",
            tipo="error",
        )
        st.stop()

    try:
        min_fecha, max_fecha = rango_disponible()
    except Exception as exc:
        error_interno("COSVEN-R002", "Lectura de base local", exc)
        st.stop()

    if min_fecha is None:
        aviso_usuario(
            "El informe no tiene movimientos para consultar.",
            "La base local existe, pero todavía no contiene información COSVEN utilizable.",
            "Comuníquese con TI e indique la referencia para verificar la última actualización.",
            "COSVEN-D004",
            tipo="error",
        )
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
    # Fecha inicial inteligente:
    # - intenta mostrar ayer;
    # - si ayer no tiene movimientos disponibles, muestra el último
    #   día con movimientos anterior a ayer.
    # - si la pestaña queda abierta de un día para otro, actualiza el
    #   valor automático sólo si el usuario no había cambiado el rango.
    # ------------------------------------------------------------
    hoy = date.today()
    ayer = hoy - timedelta(days=1)

    fecha_auto = ultima_fecha_con_movimientos(ayer)
    if fecha_auto is None:
        fecha_auto = min_fecha

    dia_sesion_anterior = st.session_state.get("cosven_dia_sesion")
    fecha_auto_anterior = st.session_state.get("cosven_fecha_auto")

    if "cosven_desde" not in st.session_state or "cosven_hasta" not in st.session_state:
        st.session_state.cosven_desde = fecha_auto
        st.session_state.cosven_hasta = fecha_auto
        st.session_state.cosven_fecha_auto = fecha_auto
        st.session_state.cosven_dia_sesion = hoy

    elif dia_sesion_anterior != hoy:
        # Si el usuario seguía viendo exactamente la fecha automática anterior,
        # se mueve automáticamente al último día disponible.
        if (
            fecha_auto_anterior is not None
            and st.session_state.cosven_desde == fecha_auto_anterior
            and st.session_state.cosven_hasta == fecha_auto_anterior
        ):
            st.session_state.cosven_desde = fecha_auto
            st.session_state.cosven_hasta = fecha_auto

        st.session_state.cosven_fecha_auto = fecha_auto
        st.session_state.cosven_dia_sesion = hoy

    st.markdown(
        """
        <div class="section-eyebrow">Período</div>
        <div class="section-title">Fecha de consulta</div>
        <div class="section-note">Por defecto se muestra el último día con movimientos disponible hasta ayer. Si necesita más información, amplíe el rango.</div>
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
        # st.caption(f"Histórico disponible: {min_fecha:%d/%m/%Y} al {max_fecha:%d/%m/%Y}")

    if desde > hasta:
        aviso_usuario(
            "El rango de fechas no es válido.",
            f"La fecha Desde ({desde:%d/%m/%Y}) es posterior a la fecha Hasta ({hasta:%d/%m/%Y}).",
            "Corrija uno de los dos calendarios y vuelva a consultar.",
            "COSVEN-F001",
            tipo="warning",
        )
        st.stop()

    try:
        df = cargar_rango(desde, hasta)
    except Exception as exc:
        error_interno(
            "COSVEN-R003",
            "Carga del período",
            exc,
            {"desde": desde, "hasta": hasta},
        )
        st.stop()

    # ------------------------------------------------------------
    # Actualización de datos
    # ------------------------------------------------------------
    info_actual = meta()

    with st.sidebar.expander("Actualización de datos", expanded=False):
        estado_actual = info_actual.get("actualizacion_estado", "")
        origen_actual = info_actual.get("actualizacion_origen", "")
        datos_hasta = info_actual.get("datos_hasta", info_actual.get("ultimo_hasta", ""))

        try:
            datos_hasta_txt = date.fromisoformat(datos_hasta).strftime("%d/%m/%Y")
        except Exception:
            datos_hasta_txt = "sin dato"

        st.caption(f"Última actualización: {ultima_txt}")
        st.caption(f"Datos procesados hasta: {datos_hasta_txt}")
        st.caption(f"Último día con movimientos: {max_fecha:%d/%m/%Y}")

        if UPDATE_LOCK.exists() or estado_actual == "EN_CURSO":
            st.info("Actualización en curso. No se iniciará otra al mismo tiempo.")
        elif estado_actual == "ERROR":
            st.warning(
                "La última actualización terminó con un error. "
                "TI puede revisar el archivo de log de actualización."
            )
        elif estado_actual == "OK" and origen_actual:
            st.caption(f"Última ejecución: {origen_actual}")

        if st.button(
            "Actualizar datos ahora",
            key="actualizar_datos_manual",
            width="stretch",
            disabled=UPDATE_LOCK.exists(),
        ):
            ok, mensaje = iniciar_actualizacion_manual()
            if ok:
                st.success(
                    "Actualización iniciada. Puede continuar usando el informe. "
                    "Al finalizar, los nuevos datos quedarán disponibles en la siguiente actualización de pantalla."
                )
            else:
                st.warning(mensaje)

        st.caption(
            "Automático: 05:00 (cierre hasta ayer) y 13:00 (incluye el día en curso)."
        )

    # ------------------------------------------------------------
    # Filtros
    # ------------------------------------------------------------
    st.sidebar.markdown("## Filtros")
    st.sidebar.caption(f"Período: {desde:%d/%m/%Y} — {hasta:%d/%m/%Y}")

    solo_perdidas = st.sidebar.checkbox("Mostrar solo artículos con pérdida", value=True, key="filtro_solo_perdidas")

    if df.empty:
        rango_txt = f"{desde:%d/%m/%Y}" if desde == hasta else f"{desde:%d/%m/%Y} al {hasta:%d/%m/%Y}"
        if desde > max_fecha:
            aviso_usuario(
                "La información de esa fecha todavía no está disponible.",
                f"No hay datos procesados para {rango_txt}. El último día disponible es {max_fecha:%d/%m/%Y} "
                f"y la última actualización local fue {ultima_txt}.",
                f"Pruebe con una fecha disponible. El informe abre automáticamente en el último día con movimientos ({max_fecha:%d/%m/%Y}) cuando el día anterior todavía no está disponible. Si esperaba información más reciente, TI debe revisar la actualización automática.",
                "COSVEN-D002",
                tipo="warning",
            )
        else:
            aviso_usuario(
                "No se encontraron ventas para el período seleccionado.",
                f"La base local no contiene movimientos COSVEN entre {rango_txt}.",
                "Revise las fechas seleccionadas o amplíe el rango de consulta.",
                "COSVEN-D001",
            )
        st.stop()

    if desde < min_fecha or hasta > max_fecha:
        st.warning(
            f"El rango solicitado incluye fechas fuera del histórico local. "
            f"La información disponible actualmente va de {min_fecha:%d/%m/%Y} a {max_fecha:%d/%m/%Y}. "
            "Los resultados corresponden únicamente a las operaciones disponibles dentro de ese intervalo."
        )

    # Catálogos globales: permanecen estables aunque el usuario cambie el rango.
    try:
        clientes, all_tipos, familias = cargar_catalogos()
    except Exception as exc:
        error_interno("COSVEN-R005", "Carga de filtros", exc)
        st.stop()

    try:
        laboratorios, estado_laboratorios = cargar_laboratorios()
    except Exception as exc:
        registrar_error("COSVEN-R006", "Catálogo de laboratorios", exc)
        laboratorios = pd.DataFrame(columns=["FLIA", "DET"])
        estado_laboratorios = "error"

    # Farmacias / clientes: todas incluidas por defecto y ordenadas alfabéticamente.
    cliente_nombre = {
        int(r.CLI): (str(r.NOM).strip() or f"Cliente {int(r.CLI)}")
        for r in clientes.itertuples()
    }

    cliente_opts_periodo = [
        int(x)
        for x in df["CLI"].dropna().astype(int).unique().tolist()
        if int(x) in cliente_nombre
    ]
    cliente_opts_periodo = sorted(
        cliente_opts_periodo,
        key=lambda cli: (normalizar_busqueda(cliente_nombre.get(cli, "")), cli)
    )

    st.sidebar.markdown("### Farmacias")
    st.sidebar.caption(
        "Todas las farmacias están incluidas por defecto. Si no desea considerar alguna, búsquela y retírela de la selección."
    )

    clientes_key = f"filtro_farmacias_{desde:%Y%m%d}_{hasta:%Y%m%d}"
    clientes_sel = st.sidebar.multiselect(
        "Farmacias incluidas",
        options=cliente_opts_periodo,
        default=cliente_opts_periodo,
        key=clientes_key,
        placeholder="Buscar y seleccionar farmacias",
        format_func=lambda cli: f"{cliente_nombre.get(cli, '')} ({cli})",
    )

    # Tipo de pedido: todos incluidos por defecto.
    tipos_periodo = sorted(
        x for x in df["TIPO_PEDIDO"].dropna().astype(str).unique().tolist()
        if str(x).strip()
    )

    st.sidebar.markdown("### Tipo de pedido")
    st.sidebar.caption(
        "Todos están incluidos por defecto. Desmarque los tipos que no quiera considerar."
    )

    tipos_key = f"filtro_tipos_pedido_{desde:%Y%m%d}_{hasta:%Y%m%d}"
    tipos_sel = st.sidebar.multiselect(
        "Tipos de pedido incluidos",
        options=tipos_periodo,
        default=tipos_periodo,
        key=tipos_key,
        placeholder="Seleccionar tipos",
        label_visibility="collapsed",
    )

    # Laboratorio / proveedor: FLIA de COSVEN se relaciona con FLIA de Laboratorio.csv.
    st.sidebar.markdown("### Laboratorio")

    laboratorios_sel = []
    labs_periodo = []
    lab_nombre = {}

    if estado_laboratorios == "ok" and not laboratorios.empty:
        lab_nombre = {
            int(r.FLIA): str(r.DET).strip()
            for r in laboratorios.itertuples()
        }

        familias_periodo = {
            int(x) for x in df["XFLIA"].dropna().astype(int).unique().tolist()
            if int(x) != 121
        }

        labs_periodo = [
            flia for flia in lab_nombre.keys()
            if flia in familias_periodo
        ]
        labs_periodo = sorted(
            labs_periodo,
            key=lambda flia: (normalizar_busqueda(lab_nombre.get(flia, "")), flia)
        )

        st.sidebar.caption(
            "Todos están incluidos por defecto y ordenados alfabéticamente. Busque por nombre y retire únicamente los que no desea considerar."
        )

        labs_key = f"filtro_laboratorios_{desde:%Y%m%d}_{hasta:%Y%m%d}"
        laboratorios_sel = st.sidebar.multiselect(
            "Laboratorios incluidos",
            options=labs_periodo,
            default=labs_periodo,
            key=labs_key,
            placeholder="Buscar laboratorio",
            format_func=lambda flia: lab_nombre.get(flia, ""),
        )
    elif estado_laboratorios == "no_existe":
        st.sidebar.warning(
            "No se encontró el catálogo de laboratorios. El filtro queda temporalmente deshabilitado. Referencia: COSVEN-D005"
        )
    else:
        st.sidebar.warning(
            "No fue posible leer el catálogo de laboratorios. El filtro queda temporalmente deshabilitado. Referencia: COSVEN-R006"
        )

    # Tipo de producto: evita repetir el código de laboratorio como si fuera otra familia.
    # FAMILIA_DESC contiene categorías como MEDICAMENTO / TOCADOR.
    tipos_producto = sorted({
        str(x).strip()
        for x in df["FAMILIA_DESC"].dropna().astype(str).tolist()
        if str(x).strip()
    }, key=normalizar_busqueda)

    tipo_producto_sel = st.sidebar.selectbox(
        "Tipo de producto",
        ["Todos"] + tipos_producto,
        key="filtro_tipo_producto",
    )

    buscar = st.sidebar.text_input("Buscar artículo", placeholder="Código o descripción", key="filtro_buscar")

    # ------------------------------------------------------------
    # Aplicar filtros de negocio SOBRE EL DETALLE y recién después totalizar
    # ------------------------------------------------------------
    filtrado_base = df.copy()

    if cliente_opts_periodo:
        if not clientes_sel:
            aviso_usuario(
                "No hay farmacias incluidas en el análisis.",
                "Se retiraron todas las farmacias disponibles para el período seleccionado.",
                "Vuelva a incluir al menos una farmacia para poder consultar la información.",
                "COSVEN-F006",
            )
            st.stop()
        filtrado_base = filtrado_base[filtrado_base["CLI"].isin(clientes_sel)]

    if tipos_periodo:
        if tipos_sel:
            filtrado_base = filtrado_base[filtrado_base["TIPO_PEDIDO"].isin(tipos_sel)]
        else:
            aviso_usuario(
                "No hay tipos de pedido seleccionados.",
                "El período contiene ventas, pero se desmarcaron todos los tipos de pedido.",
                "Seleccione al menos un tipo de pedido o vuelva a dejar todos marcados.",
                "COSVEN-F003",
            )
            st.stop()

    # Familia 121 contiene movimientos de ajuste/NC que no representan medicamentos normales.
    # Se conserva su total por separado y no se distribuye artificialmente entre productos.
    ajustes_nc = filtrado_base[filtrado_base["XFLIA"].astype(int) == 121].copy()
    filtrado = filtrado_base[filtrado_base["XFLIA"].astype(int) != 121].copy()

    if labs_periodo:
        if laboratorios_sel:
            filtrado = filtrado[filtrado["XFLIA"].astype(int).isin([int(x) for x in laboratorios_sel])]
        else:
            aviso_usuario(
                "No hay laboratorios incluidos en el análisis.",
                "Se retiraron todos los laboratorios disponibles para el período seleccionado.",
                "Vuelva a incluir al menos un laboratorio para poder consultar la información.",
                "COSVEN-F007",
            )
            st.stop()

    if tipo_producto_sel != "Todos":
        filtrado = filtrado[
            filtrado["FAMILIA_DESC"].fillna("").astype(str).str.strip() == tipo_producto_sel
        ]

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

    if filtrado.empty:
        aviso_usuario(
            "Los filtros seleccionados no dejan operaciones para mostrar.",
            "El período sí contiene movimientos, pero la combinación actual de farmacias, tipo de pedido, laboratorio, familia o búsqueda de artículo deja la consulta sin registros de medicamentos.",
            "Revise los filtros de la izquierda y quite o modifique alguno de ellos.",
            "COSVEN-F002",
        )
        st.stop()

    # Las notas de crédito (TM=NC) se conservan en el detalle de cada artículo,
    # pero no participan en el ranking ni en los KPI de rentabilidad.
    es_nc = filtrado["TM"].fillna("").astype(str).str.strip().str.upper().eq("NC")
    filtrado_rentabilidad = filtrado[~es_nc].copy()

    if filtrado_rentabilidad.empty:
        aviso_usuario(
            "No hay ventas computables para calcular rentabilidad.",
            "Los filtros seleccionados dejan únicamente notas de crédito (TM=NC) u otros movimientos sin venta computable.",
            "Amplíe o modifique los filtros para consultar operaciones de venta. Las notas de crédito se mantienen disponibles como trazabilidad en el detalle cuando existe una venta asociada.",
            "COSVEN-F008",
        )
        st.stop()

    resumen = agregar_por_articulo(filtrado_rentabilidad)

    # KPIs siempre responden a fecha/cliente/tipo/familia/artículo.
    # Las NC no alteran Venta, Costo, Utilidad ni % Utilidad.
    # El switch "solo pérdida" es únicamente de presentación de la tabla.
    venta_total = float(filtrado_rentabilidad["IMP"].sum())
    costo_total = float(filtrado_rentabilidad["COSTO"].sum())
    utilidad_total = venta_total - costo_total
    putil_total = ((venta_total / costo_total) - 1) * 100 if costo_total > 0 else 0.0
    neg = resumen[resumen["UTILIDAD"] < 0] if not resumen.empty else resumen
    cant_neg = len(neg)
    perdida_acum = abs(float(neg["UTILIDAD"].sum())) if not neg.empty else 0.0

    st.write("")
    with st.container(key="kpi_resumen"):
        cols = st.columns(6)
        cols[0].metric("Venta", money(venta_total))
        cols[1].metric("Costo", money(costo_total))
        cols[2].metric("Utilidad", money(utilidad_total))
        cols[3].metric("% Utilidad", pct(putil_total))
        cols[4].metric("Artículos con pérdida", f"{cant_neg:,}")
        cols[5].metric("Pérdida acumulada", money(perdida_acum))

    if not ajustes_nc.empty:
        ajuste_venta = float(ajustes_nc["IMP"].sum())
        ajuste_costo = float(ajustes_nc["COSTO"].sum())
        ajuste_utilidad = ajuste_venta - ajuste_costo
        st.caption(
            f"Ajustes / Notas de crédito fuera del ranking de medicamentos: "
            f"{len(ajustes_nc):,} movimientos | Venta: {money(ajuste_venta)} | "
            f"Costo: {money(ajuste_costo)} | Utilidad: {money(ajuste_utilidad)}. "
            "Estos movimientos no se distribuyen entre artículos ni laboratorios."
        )

    # ------------------------------------------------------------
    # Resultados
    # ------------------------------------------------------------
    st.write("")
    st.markdown(
        """
        <div class="section-eyebrow">Resultados</div>
        <div class="section-title">Resultado por artículo</div>
        <div class="section-note">Haga clic sobre una fila para abrir el detalle de ventas en una ventana amplia. Las columnas se muestran en formato compacto para facilitar la lectura sin perder la consulta actual.</div>
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
        if solo_perdidas and not resumen.empty:
            aviso_usuario(
                "No hay artículos con pérdida para esta selección.",
                "Existen ventas con los filtros actuales, pero ningún artículo tiene utilidad negativa en el resultado totalizado.",
                "Desmarque 'Mostrar solo artículos con pérdida' si desea ver también los artículos con utilidad cero o positiva.",
                "COSVEN-F004",
            )
        else:
            aviso_usuario(
                "No hay artículos para mostrar.",
                "La combinación actual de filtros no produce resultados por artículo.",
                "Revise los filtros de la consulta.",
                "COSVEN-F002",
            )
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
        "% Utilidad", "Venta", "Costo", "Utilidad", "Cantidad", "Bonificación"
    ]

    # Anchos expresados en píxeles para evitar que columnas queden fuera
    # de la vista en una pantalla de escritorio estándar.
    # Las columnas descriptivas reciben más espacio y las numéricas se compactan.
    config = {
        "Familia": st.column_config.NumberColumn(width=58, format="%d"),
        "Artículo": st.column_config.NumberColumn(width=64, format="%d"),
        "Descripción": st.column_config.TextColumn(width=235),
        "Descripción familia": st.column_config.TextColumn(width=145),
        "% Utilidad": st.column_config.NumberColumn(width=78, format="%.2f %%"),
        "Venta": st.column_config.NumberColumn(width=102, format="$ %.2f"),
        "Costo": st.column_config.NumberColumn(width=102, format="$ %.2f"),
        "Utilidad": st.column_config.NumberColumn(width=102, format="$ %.2f"),
        "Cantidad": st.column_config.NumberColumn(width=72, format="%.2f"),
        "Bonificación": st.column_config.NumberColumn(width=82, format="%.2f"),
    }

    selected_key = None
    abrir_automatico = False
    supports_selection = "on_select" in inspect.signature(st.dataframe).parameters

    # Una clave distinta por conjunto de filtros evita que una selección vieja
    # termine apuntando a otra fila cuando cambia la consulta.
    filtro_payload = {
        "desde": desde.isoformat(),
        "hasta": hasta.isoformat(),
        "farmacias_incluidas": sorted(int(x) for x in clientes_sel),
        "tipos": list(tipos_sel),
        "laboratorios": sorted(int(x) for x in laboratorios_sel) if labs_periodo else [],
        "tipo_producto": str(tipo_producto_sel),
        "buscar": buscar.strip().lower(),
        "solo_perdidas": bool(solo_perdidas),
    }
    filtro_sig = hashlib.md5(
        json.dumps(filtro_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]

    table_key = f"resultado_articulos_{filtro_sig}"

    if supports_selection:
        event = st.dataframe(
            vista[cols_tabla],
            width="stretch",
            height=560,
            hide_index=True,
            row_height=38,
            column_config=config,
            on_select="rerun",
            selection_mode="single-row",
            key=table_key,
        )
        rows = getattr(getattr(event, "selection", None), "rows", [])
        if rows:
            idx = rows[0]
            if 0 <= idx < len(mostrar):
                r = mostrar.iloc[idx]
                selected_key = (int(r["XFLIA"]), int(r["XART"]))
                st.session_state["articulo_seleccionado"] = selected_key
                firma_sel = f"{filtro_sig}:{selected_key[0]}:{selected_key[1]}"
                if st.session_state.get("ultimo_modal_automatico") != firma_sel:
                    st.session_state["ultimo_modal_automatico"] = firma_sel
                    abrir_automatico = True
    else:
        st.dataframe(
            vista[cols_tabla],
            width="stretch",
            height=560,
            hide_index=True,
            row_height=38,
            column_config=config,
        )
        aviso_usuario(
            "La selección por clic no está disponible en esta instalación.",
            "La versión de Streamlit instalada no permite seleccionar directamente una fila de la tabla.",
            "Comuníquese con TI e indique la referencia para actualizar el componente del dashboard.",
            "COSVEN-U002",
            tipo="warning",
        )

    if selected_key is None:
        selected_key = st.session_state.get("articulo_seleccionado")

    valid_keys = set(zip(mostrar["XFLIA"].astype(int), mostrar["XART"].astype(int)))
    if selected_key not in valid_keys:
        selected_key = None
        st.session_state.pop("articulo_seleccionado", None)

    if selected_key is None:
        st.caption("Seleccione una fila para consultar el detalle de ventas del artículo.")
    else:
        fsel, asel = selected_key
        art_rows = mostrar[
            (mostrar["XFLIA"].astype(int) == fsel)
            & (mostrar["XART"].astype(int) == asel)
        ]
        desc = str(art_rows.iloc[0]["DET"]) if not art_rows.empty else ""

        det = filtrado[
            (filtrado["XFLIA"].astype(int) == fsel)
            & (filtrado["XART"].astype(int) == asel)
        ].copy().sort_values(["FECHA", "TM", "DOC"])

        csel1, csel2 = st.columns([.82, .18], vertical_alignment="center")
        with csel1:
            st.markdown(
                f'<div class="selected-product">Seleccionado: {fsel:03d}-{asel:04d} &nbsp;|&nbsp; {desc}</div>',
                unsafe_allow_html=True,
            )
        with csel2:
            abrir_manual = st.button(
                "Abrir detalle",
                width="stretch",
                key=f"abrir_detalle_{filtro_sig}_{fsel}_{asel}",
            )

        if abrir_automatico or abrir_manual:
            abrir_detalle_modal(det, fsel, asel, desc, desde, hasta)

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
    # Ayuda breve para usuario final
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
        ayuda_html = (
            '<div class="natural-box">'
            '<strong>¿Qué muestra?</strong><br>'
            'Permite analizar las ventas del período seleccionado e identificar artículos con pérdida o baja rentabilidad. '
            'Al ingresar, muestra automáticamente el <strong>día anterior</strong>; el período puede cambiarse con los calendarios Desde y Hasta.'
            '<br><br>'
            '<strong>Filtros disponibles</strong><br>'
            'La consulta puede ajustarse por <strong>Farmacias</strong>, <strong>Tipo de pedido</strong>, '
            '<strong>Laboratorio / Proveedor</strong>, <strong>Tipo de producto</strong> y <strong>Artículo</strong>. '
            'Los resultados se recalculan según la selección realizada.'
            '<br><br>'
            '<strong>¿Qué muestran los resultados?</strong><br>'
            'La tabla resume cantidad, bonificación, venta, costo, utilidad y porcentaje de utilidad por artículo. '
            'Las notas de crédito (TM=NC) se mantienen visibles en el detalle para trazabilidad, pero no participan en el cálculo de rentabilidad. '
            'Los movimientos de ajuste identificados por el sistema se presentan por separado para no mezclarlos con la rentabilidad normal de los productos.'
            '<br><br>'
            '<strong>¿Cómo veo el detalle?</strong><br>'
            'Al seleccionar una fila se abre una ventana amplia con las operaciones que forman el resultado: '
            'fecha, cliente, pedido, tipo de pedido, documento, cantidades, venta, costo y utilidad.'
            '<br><br>'
            '<strong>Actualización y seguridad</strong><br>'
            'El informe trabaja con información local actualizada desde Paykan. '
            'Los archivos operativos se consultan únicamente en modo lectura; esta pantalla no modifica los datos del sistema.'
            '</div>'
        )
        st.markdown(ayuda_html, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="paykan-footer">
            <strong>Paykan</strong> · Informe interno de costo de ventas por artículo
        </div>
        """,
        unsafe_allow_html=True,
    )



try:
    render_app()
except Exception as exc:
    # Última barrera: nunca mostrar traceback o rutas internas al usuario final.
    error_interno("COSVEN-R001", "Ejecución general del dashboard", exc)
