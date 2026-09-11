
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "V1.3"
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "regatas_tesoreria.db"
LOGO_PATH = BASE_DIR / "logo_regatas_oficial.png"

BLUE = "#123B63"
BLUE_2 = "#1E5A8A"
ORANGE = "#F4B183"
ORANGE_LIGHT = "#FCE4D6"
GREEN = "#2E7D32"
YELLOW = "#D6A100"
RED = "#C62828"
GRAY = "#6B7280"

st.set_page_config(page_title="Regatas · Tesorería", page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🔷", layout="wide")

st.markdown(
    f"""
    <style>
    html, body, [class*="css"] {{ font-family: Calibri, Arial, sans-serif; }}
    .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1480px; }}
    .regatas-header {{
        background: linear-gradient(90deg, {BLUE}, {BLUE_2});
        border-radius: 14px; padding: 18px 22px; color: white;
        margin-bottom: 14px; box-shadow: 0 4px 14px rgba(0,0,0,.08);
    }}
    .regatas-header h1 {{ color: white; font-size: 2rem; margin:0; }}
    .regatas-header p {{ color: white; margin:7px 0 0 0; opacity:.93; }}
    .section-title {{
        background:{BLUE}; color:white; padding:9px 14px; border-radius:9px;
        font-weight:700; margin:12px 0 10px 0; font-size:1.05rem;
    }}
    .subtle-note {{
        background:{ORANGE_LIGHT}; border-left:5px solid {ORANGE}; padding:10px 13px;
        border-radius:8px; color:#5A493E; margin:8px 0 12px 0;
    }}
    .kpi-card {{
        background:white; border:1px solid #DDE4EC; border-top:4px solid {BLUE};
        border-radius:12px; padding:12px 14px; min-height:116px;
        box-shadow:0 3px 12px rgba(15,23,42,.05);
    }}
    .kpi-card .name {{ font-size:.86rem; color:#506174; margin-bottom:4px; }}
    .kpi-card .value {{ font-size:1.45rem; font-weight:700; color:#14324A; }}
    .kpi-card .detail {{ font-size:.78rem; color:#6B7280; margin-top:5px; }}
    .status-green {{ color:{GREEN}; font-weight:700; }}
    .status-yellow {{ color:{YELLOW}; font-weight:700; }}
    .status-red {{ color:{RED}; font-weight:700; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- DB ----------------
def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def execute(sql, params=()):
    with conn() as c:
        c.execute(sql, params)
        c.commit()

def fetch_df(sql, params=()):
    with conn() as c:
        return pd.read_sql_query(sql, c, params=params)

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS weekly_finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT UNIQUE NOT NULL,
            tenencias_pesos REAL DEFAULT 0,
            obligaciones_pesos REAL DEFAULT 0,
            sueldos REAL DEFAULT 0,
            f931 REAL DEFAULT 0,
            fondo_reserva_pesos REAL DEFAULT 0,
            usd_brutos REAL DEFAULT 0,
            usd_afectados REAL DEFAULT 0,
            usd_venta_inmueble REAL DEFAULT 0,
            tipo_cambio REAL DEFAULT 0,
            ingresos_semana REAL DEFAULT 0,
            cobranzas_cuota REAL DEFAULT 0,
            facturacion_exigible REAL DEFAULT 0,
            deuda_vencida REAL DEFAULT 0,
            gastos_capitania REAL DEFAULT 0,
            gastos_extraordinarios REAL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            fuente TEXT DEFAULT 'Manual',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS monthly_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT UNIQUE NOT NULL,
            ingresos_totales REAL DEFAULT 0,
            ingresos_gr REAL DEFAULT 0,
            total_general REAL DEFAULT 0,
            especificos REAL DEFAULT 0,
            socios_pagadores INTEGER DEFAULT 0,
            morosidad_pct REAL DEFAULT NULL,
            morosos_reales INTEGER DEFAULT NULL,
            deuda_morosa_real REAL DEFAULT NULL,
            ajuste_cuota_pct REAL DEFAULT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            deporte TEXT NOT NULL,
            ingresos REAL DEFAULT 0,
            egresos_directos REAL DEFAULT 0,
            gastos_indirectos REAL DEFAULT 0,
            saldo_cuenta REAL DEFAULT 0,
            socios INTEGER DEFAULT 0,
            cuota_promedio REAL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            UNIQUE(fecha, deporte)
        );

        CREATE TABLE IF NOT EXISTS capitania (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            mes TEXT NOT NULL,
            proveedor TEXT DEFAULT '',
            concepto TEXT DEFAULT '',
            categoria TEXT DEFAULT '',
            beneficiario TEXT DEFAULT 'General',
            monto REAL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            UNIQUE(fecha, proveedor, concepto, monto)
        );

        CREATE TABLE IF NOT EXISTS capitania_identificada (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            proveedor TEXT DEFAULT '',
            concepto TEXT DEFAULT '',
            categoria TEXT DEFAULT '',
            beneficiario_original TEXT DEFAULT '',
            deporte_normalizado TEXT DEFAULT '',
            estado_match TEXT DEFAULT 'Revisar',
            monto REAL DEFAULT 0,
            observaciones TEXT DEFAULT '',
            UNIQUE(fecha, proveedor, concepto, monto)
        );

        CREATE TABLE IF NOT EXISTS sports_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deporte TEXT UNIQUE NOT NULL,
            activo INTEGER DEFAULT 1,
            origen TEXT DEFAULT 'Histórico',
            observaciones TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            cuenta TEXT NOT NULL,
            moneda TEXT NOT NULL,
            saldo REAL DEFAULT 0,
            tipo_cambio REAL DEFAULT 0,
            afectado INTEGER DEFAULT 0,
            categoria TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            UNIQUE(fecha, cuenta, moneda)
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            concepto TEXT NOT NULL,
            monto REAL DEFAULT 0,
            moneda TEXT DEFAULT 'ARS',
            centro_costo TEXT DEFAULT '',
            responsable TEXT DEFAULT '',
            observaciones TEXT DEFAULT ''
        );
        """)
        c.commit()
    seed_if_empty()

def seed_if_empty():
    if fetch_df("SELECT COUNT(*) n FROM monthly_members").iloc[0]["n"] == 0:
        rows = [
            ("2026-05",483_900_000,359_800_000,406_700_000,77_200_000,7260,16.15,3.00),
            ("2026-06",496_600_000,368_300_000,416_200_000,80_400_000,7216,15.40,3.00),
            ("2026-07",505_300_000,376_900_000,425_900_000,79_400_000,7199,15.57,2.50),
            ("2026-08",518_300_000,376_500_000,429_500_000,88_800_000,7181,15.52,None),
            ("2026-09",533_200_000,387_200_000,443_900_000,89_200_000,7233,14.72,None),
        ]
        with conn() as c:
            c.executemany("""INSERT INTO monthly_members
                (mes,ingresos_totales,ingresos_gr,total_general,especificos,socios_pagadores,morosidad_pct,ajuste_cuota_pct)
                VALUES (?,?,?,?,?,?,?,?)""", rows)

    if fetch_df("SELECT COUNT(*) n FROM weekly_finance").iloc[0]["n"] == 0:
        rows = [
            ("2026-03-30",540_165_175,349_563_293,347_401,0,0,0),
            ("2026-04-27",509_823_601,336_081_687,351_082,0,0,0),
            ("2026-05-25",496_785_604,356_136_311,370_432,0,0,0),
            ("2026-06-29",186_905_308,359_381_199,360_378,0,0,0),
            ("2026-07-27",316_017_336,498_685_172,369_091,0,0,0),
            ("2026-08-25",369_599_722,550_467_769,367_059,230_000,32_250.73,1480),
            ("2026-09-01",109_544_104.51,362_850_338.97,367_450,230_000,32_250.73,1480),
            ("2026-09-08",122_400_000,347_300_000,367_450,230_000,32_250.73,1480),
        ]
        with conn() as c:
            c.executemany("""INSERT INTO weekly_finance
                (fecha,tenencias_pesos,obligaciones_pesos,usd_brutos,usd_venta_inmueble,usd_afectados,tipo_cambio,fuente)
                VALUES (?,?,?,?,?,?,?,'Histórico integrado')""", rows)

    if fetch_df("SELECT COUNT(*) n FROM sports").iloc[0]["n"] == 0:
        rows = [
            ("2026-09-01","Básquet Formativo",22_619_566.95),
            ("2026-09-01","Básquet Femenino",-7_358_331.66),
            ("2026-09-01","Caleta",26_298_726.70),
            ("2026-09-01","Fútbol Femenino",10_881_442.57),
            ("2026-09-01","Fútbol Infantil",41_216_940.15),
            ("2026-09-01","Fútbol Inferiores 121",-36_436_127.95),
            ("2026-09-01","Futsal",3_643_999),
            ("2026-09-01","Gimnasia Artística",3_303_802.23),
            ("2026-09-01","Handball",16_307_730.34),
            ("2026-09-01","Hockey",4_655_866.15),
            ("2026-09-01","Karate",575_658.87),
            ("2026-09-01","Natación",0),
            ("2026-09-01","Pádel",1_966_499.59),
            ("2026-09-01","Remo",2_319_945.51),
            ("2026-09-01","Rugby",42_537_857.75),
            ("2026-09-01","Tenis",87_866_080.40),
            ("2026-09-01","Vóley",30_624_225.41),
            ("2026-09-01","Campamento Isla",14_771_559),
            ("2026-09-01","Yachting",1_431_149.96),
        ]
        with conn() as c:
            c.executemany("""INSERT INTO sports (fecha,deporte,saldo_cuenta) VALUES (?,?,?)""", rows)

    if fetch_df("SELECT COUNT(*) n FROM capitania").iloc[0]["n"] == 0:
        beneficiarios = [
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Natación / pileta",27_812_302,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Hockey",11_277_647,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Tenis",10_131_000,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Básquet",9_956_290,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Gimnasio / pesas / Remo",9_014_382,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Gimnasio / pesas",6_992_146,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Yachting / náutica",4_865_657,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Rugby",2_483_714,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Remo",303_790,"Total identificado en informe contable"),
            ("2026-06-30","2026-06","Histórico integrado","Gastos deportivos identificados","Deporte","Karate",302_000,"Total identificado en informe contable"),
        ]
        monthly = [
            ("2025-08-31","2025-08","Histórico integrado","Gasto mensual Capitanía","General","General",62_630_775,"Ciclo cerrado"),
            ("2025-09-30","2025-09","Histórico integrado","Gasto mensual Capitanía","General","General",47_151_677,"Ciclo cerrado"),
            ("2025-10-31","2025-10","Histórico integrado","Gasto mensual Capitanía","General","General",53_288_162,"Ciclo cerrado"),
            ("2025-11-30","2025-11","Histórico integrado","Gasto mensual Capitanía","General","General",56_125_313,"Ciclo cerrado"),
            ("2025-12-31","2025-12","Histórico integrado","Gasto mensual Capitanía","General","General",43_668_444,"Ciclo cerrado"),
            ("2026-01-31","2026-01","Histórico integrado","Gasto mensual Capitanía","General","General",71_887_306,"Ciclo cerrado"),
            ("2026-02-28","2026-02","Histórico integrado","Gasto mensual Capitanía","General","General",57_481_140,"Ciclo cerrado"),
            ("2026-03-31","2026-03","Histórico integrado","Gasto mensual Capitanía","General","General",32_141_911,"Ciclo actual"),
            ("2026-04-30","2026-04","Histórico integrado","Gasto mensual Capitanía","General","General",37_500_927,"Ciclo actual"),
            ("2026-05-31","2026-05","Histórico integrado","Gasto mensual Capitanía","General","General",44_603_637,"Ciclo actual"),
            ("2026-06-30","2026-06","Histórico integrado","Gasto mensual Capitanía","General","General",45_281_812,"Ciclo actual"),
        ]
        with conn() as c:
            c.executemany("""INSERT OR IGNORE INTO capitania
                (fecha,mes,proveedor,concepto,categoria,beneficiario,monto,observaciones)
                VALUES (?,?,?,?,?,?,?,?)""", monthly + beneficiarios)


    # Maestro de deportes: unión de cuentas históricas conocidas.
    if fetch_df("SELECT COUNT(*) n FROM sports_master").iloc[0]["n"] == 0:
        deportes = [
            "Básquet Femenino","Básquet Formativo","Caleta","Campamento Isla",
            "Fútbol Femenino","Fútbol Infantil","Fútbol Inferiores 121","Futsal",
            "Gimnasia Artística","Handball","Hockey","Karate","Natación","Pádel",
            "Remo","Rugby","Tenis","Vóley","Yachting"
        ]
        with conn() as c:
            c.executemany("INSERT OR IGNORE INTO sports_master(deporte,origen) VALUES(?,'Informe contable / cuentas')",
                          [(d,) for d in deportes])

    # Movimientos de Capitanía con identificación deportiva clara encontrados en el informe contable.
    if fetch_df("SELECT COUNT(*) n FROM capitania_identificada").iloc[0]["n"] == 0:
        movs = [
            ("2026-01-08","ORIHUELA JORGE EDGARDO","compra de cuatriciclo tenis","Equipamiento","Tenis","Tenis","Coincide",9270000,""),
            ("2026-05-28","WAINMANN ARIEL HERNAN","compra de pisos de goma p/ gimnasio y sala de remo","Equipamiento","Gimnasio / pesas / Remo","Gimnasio / pesas / Remo","Ambiguo",9014382,"Revisar distribución entre gimnasio y Remo"),
            ("2025-10-09","MASCARDI PLASTICOS SAU","compra de sillas para pileta - capitanía","Equipamiento","Natación / pileta","Natación","Coincide",7811400,""),
            ("2026-02-20","JOSSO ROMINA VANESA","compra fenólicos p/ cancha básquet","Equipamiento","Básquet","Básquet (sin subcuenta)","Ambiguo",5407840,"Definir Formativo/Femenino"),
            ("2026-01-08","COSITFER DE LOS ARROYOS S.A.","compra de sombrillas playa y pileta","Equipamiento","Natación / pileta","Natación","Coincide",4450140,""),
            ("2026-06-18","SOSA GUERCI MIRKO","trabajos iluminación cancha de hockey","Electricidad / iluminación","Hockey","Hockey","Coincide",3952744,""),
            ("2025-11-10","PULSERAS ROSARIO","pulseras p/ pileta","Otros","Natación / pileta","Natación","Coincide",3872000,""),
            ("2026-05-06","GAMELAN FITNESS","compra elementos de gym. paga la reserva de gym","Equipamiento","Gimnasio / pesas","Gimnasio / pesas","Sin cuenta",3497732,""),
            ("2026-06-05","SOSA GUERCI MIRKO","mantenimiento iluminación en cancha hockey","Electricidad / iluminación","Hockey","Hockey","Coincide",3436400,""),
            ("2025-09-05","OTROS MATERIAL FLOTANTE","cancelación bote - Capitanía","Equipamiento","Yachting / náutica","Yachting","Coincide",2606816,""),
            ("2025-10-21","MASTRANGELO S.A.","obra iluminación isla. Rugby","Electricidad / iluminación","Rugby","Rugby","Coincide",2483714,""),
            ("2026-03-03","SOSA GUERCI MIRKO","compra lámparas para cambio en isla y hockey","Electricidad / iluminación","Hockey","Hockey","Coincide",2333115,""),
            ("2025-11-10","TAPICERIA VELAZQUEZ","cobertores de las jirafas del gim ppal","Otros","Básquet","Básquet (sin subcuenta)","Ambiguo",2150050,"Definir Formativo/Femenino"),
            ("2025-10-24","CASA BOFFA HNAS. S.A.","pago sombrillones - pileta","Equipamiento","Natación / pileta","Natación","Coincide",2040000,""),
            ("2026-01-13","ROBERTO PINASCO Y ROBERTO ORIH","compra de ventiladores gimnasio","Equipamiento","Gimnasio / pesas","Gimnasio / pesas","Sin cuenta",1762500,""),
            ("2026-02-03","HERNAN PIVA","materiales p/ mantenimiento de pileta","Otros","Natación / pileta","Natación","Coincide",1570200,""),
            ("2026-01-31","Piva","mantenimiento de pileta","Otros","Natación / pileta","Natación","Coincide",1570200,""),
            ("2025-12-22","VILLARRAZA EDUARDO","estudio de iluminación cancha de hockey","Electricidad / iluminación","Hockey","Hockey","Coincide",1555388,""),
            ("2026-04-01","FONDO DE RESERVA YACHTING","50% horas trabajadas grand prix - marinería","Personal","Yachting / náutica","Yachting","Coincide",1475989,""),
            ("2026-02-04","MANERO OMAR (ALQUIMIA)","compra de cloro 2 piletas","Limpieza / químicos","Natación / pileta","Natación","Coincide",1322200,""),
            ("2026-02-26","TAPICERIA VELAZQUEZ","retapizar jirafas de cancha de básquet","Otros","Básquet","Básquet (sin subcuenta)","Ambiguo",1307000,"Definir Formativo/Femenino"),
            ("2026-03-06","NOBA COLOR PINTURERIAS","compra pinturas varias p/ gimnasio","Pinturas","Gimnasio / pesas","Gimnasio / pesas","Sin cuenta",1208559,""),
            ("2025-09-10","DISI DISTRIBUIDORA SIDERURGICA","compra de hierros p/ prado y puerta p/pileta - Capitanía","Ferretería","Natación / pileta","Natación","Coincide",962173,""),
            ("2026-01-23","PEDRAZZOLI, DEL FRADE & CIA S.","elementos para la pileta","Otros","Natación / pileta","Natación","Coincide",943899,""),
            ("2026-03-02","HERNAN PIVA","insumos de pileta","Otros","Natación / pileta","Natación","Coincide",817800,""),
            ("2025-12-09","MANTENIMIENTO PILETA","reparación bomba pileta","Mantenimiento","Natación / pileta","Natación","Coincide",721160,""),
            ("2026-01-05","CASA BOFFA HNAS. S.A.","mediasombra de tenis","Equipamiento","Tenis","Tenis","Coincide",660000,""),
            ("2026-05-26","TAPICERIA VELAZQUEZ","tapizado de jirafas de básquet","Otros","Básquet","Básquet (sin subcuenta)","Ambiguo",540500,"Definir Formativo/Femenino"),
            ("2025-12-03","HERNAN PIVA","insumo de pileta","Otros","Natación / pileta","Natación","Coincide",529400,""),
            ("2025-09-16","MANTENIMIENTO PILETA","compras varias realizadas x Capitanía","Otros","Natación / pileta","Natación","Coincide",432279,""),
            ("2026-04-15","MANTENIMIENTO BUCANERO","pago hs. extras","Personal","Yachting / náutica","Yachting","Coincide",79865,""),
            ("2026-03-09","M & S DISTRIBUIDOR","compra de fenólicos","Otros","Básquet","Básquet (sin subcuenta)","Ambiguo",140000,"Definir Formativo/Femenino"),
        ]
        with conn() as c:
            c.executemany("""INSERT OR IGNORE INTO capitania_identificada
                (fecha,proveedor,concepto,categoria,beneficiario_original,deporte_normalizado,estado_match,monto,observaciones)
                VALUES(?,?,?,?,?,?,?,?,?)""", movs)


init_db()

# ---------------- helpers ----------------

# Selector mensual reutilizable.
# Devuelve el DataFrame filtrado; "Todos" permite ver el historial completo.
def filtro_mes(df, fecha_col, key, label="Mes"):
    if df is None or df.empty or fecha_col not in df.columns:
        return df
    out = df.copy()
    fechas = pd.to_datetime(out[fecha_col], errors="coerce")
    meses = sorted(fechas.dropna().dt.strftime("%Y-%m").unique().tolist(), reverse=True)
    opciones = ["Todos"] + meses
    elegido = st.selectbox(label, opciones, index=0, key=key)
    if elegido != "Todos":
        out = out[fechas.dt.strftime("%Y-%m") == elegido].copy()
    return out

def normalizar_deporte(nombre):
    """Normaliza nombres provenientes de cuentas y descripciones de Capitanía."""
    if nombre is None or pd.isna(nombre):
        return ""
    s = str(nombre).strip().lower()
    reemplazos = {
        "natación / pileta":"Natación",
        "natacion / pileta":"Natación",
        "pileta":"Natación",
        "natación":"Natación",
        "natacion":"Natación",
        "hockey":"Hockey",
        "tenis":"Tenis",
        "rugby":"Rugby",
        "remo":"Remo",
        "karate":"Karate",
        "yachting / náutica":"Yachting",
        "yachting / nautica":"Yachting",
        "náutica":"Yachting",
        "nautica":"Yachting",
        "yachting":"Yachting",
        "vóley":"Vóley",
        "voley":"Vóley",
        "handball":"Handball",
        "pádel":"Pádel",
        "padel":"Pádel",
        "futsal":"Futsal",
        "caleta":"Caleta",
        "campamento isla":"Campamento Isla",
        "fútbol femenino":"Fútbol Femenino",
        "futbol femenino":"Fútbol Femenino",
        "fútbol infantil":"Fútbol Infantil",
        "futbol infantil":"Fútbol Infantil",
        "fútbol inferiores 121":"Fútbol Inferiores 121",
        "futbol inferiores 121":"Fútbol Inferiores 121",
        "gimnasia artística":"Gimnasia Artística",
        "gimnasia artistica":"Gimnasia Artística",
        "básquet formativo":"Básquet Formativo",
        "basquet formativo":"Básquet Formativo",
        "básquet femenino":"Básquet Femenino",
        "basquet femenino":"Básquet Femenino",
    }
    if s in reemplazos:
        return reemplazos[s]
    # Casos ambiguos: se conservan para revisión manual.
    if "basquet" in s or "básquet" in s:
        return "Básquet (sin subcuenta)"
    if "gimnasio" in s or "pesas" in s:
        if "remo" in s:
            return "Gimnasio / pesas / Remo"
        return "Gimnasio / pesas"
    return str(nombre).strip()

def estado_match_deporte(nombre_normalizado, deportes_validos):
    if nombre_normalizado in deportes_validos:
        return "Coincide"
    if nombre_normalizado in ["Básquet (sin subcuenta)", "Gimnasio / pesas", "Gimnasio / pesas / Remo"]:
        return "Ambiguo"
    return "Sin cuenta"




def ars(v):
    if v is None or pd.isna(v): return "—"
    sign = "-" if float(v) < 0 else ""
    x = abs(float(v))
    if x >= 1_000_000:
        return f"{sign}$ {x/1_000_000:,.1f} M".replace(",", "X").replace(".", ",").replace("X",".")
    return f"{sign}$ {x:,.0f}".replace(",", ".")

def usd_fmt(v):
    if v is None or pd.isna(v): return "—"
    return f"USD {float(v):,.0f}".replace(",", ".")

def pct(v, d=1):
    if v is None or pd.isna(v): return "—"
    return f"{float(v):.{d}f}%".replace(".", ",")

def ratio(v):
    if v is None or pd.isna(v): return "—"
    return f"{float(v):.2f}x".replace(".", ",")

def section(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

def card(name,value,detail="",status_text=None,status_class="status-yellow"):
    status = f'<div class="{status_class}" style="margin-top:6px;font-size:.82rem">{status_text}</div>' if status_text else ""
    st.markdown(f"""<div class="kpi-card"><div class="name">{name}</div><div class="value">{value}</div>
    <div class="detail">{detail}</div>{status}</div>""", unsafe_allow_html=True)

def latest_week():
    d=fetch_df("SELECT * FROM weekly_finance ORDER BY fecha DESC LIMIT 1")
    return None if d.empty else d.iloc[0]

def metrics():
    w=latest_week()
    m=fetch_df("SELECT * FROM monthly_members ORDER BY mes DESC LIMIT 1")
    m=None if m.empty else m.iloc[0]
    ten=float(w["tenencias_pesos"] or 0); obl=float(w["obligaciones_pesos"] or 0)
    disp=ten-obl; cov=ten/obl if obl else np.nan
    ubr=float(w["usd_brutos"] or 0); uaf=float(w["usd_afectados"] or 0); uvi=float(w["usd_venta_inmueble"] or 0); fx=float(w["tipo_cambio"] or 0)
    ufree=max(ubr-uaf-uvi,0); uars=ufree*fx; pos=disp+uars
    if float(w["facturacion_exigible"] or 0)>0:
        cob=float(w["cobranzas_cuota"])/float(w["facturacion_exigible"])*100
        mora=float(w["deuda_vencida"])/float(w["facturacion_exigible"])*100
    else:
        cob=np.nan
        mora=float(m["morosidad_pct"]) if m is not None and pd.notna(m["morosidad_pct"]) else np.nan
    ticket=float(m["ingresos_gr"])/float(m["socios_pagadores"]) if m is not None and float(m["socios_pagadores"] or 0)>0 else np.nan
    labor=float(w["sueldos"] or 0)+float(w["f931"] or 0)
    ingresos=float(m["ingresos_totales"]) if m is not None else 0
    lab_ratio=labor/ingresos*100 if ingresos>0 and labor>0 else np.nan
    return dict(fecha=w["fecha"],ten=ten,obl=obl,disp=disp,cov=cov,ubr=ubr,uaf=uaf,uvi=uvi,ufree=ufree,uars=uars,pos=pos,
                cob=cob,mora=mora,socios=int(m["socios_pagadores"]) if m is not None else 0,ticket=ticket,lab_ratio=lab_ratio)

def semaforo(kind,val):
    if val is None or pd.isna(val): return ("⚪ N/D","status-yellow")
    if kind=="disp": return ("🟢 Positiva","status-green") if val>=0 else ("🔴 Negativa","status-red")
    if kind=="cov":
        if val>=1.2:return("🟢 Normal","status-green")
        if val>=1.0:return("🟡 Atención","status-yellow")
        return("🔴 Crítico","status-red")
    if kind=="mora":
        if val<10:return("🟢 Baja","status-green")
        if val<=15:return("🟡 Atención","status-yellow")
        return("🔴 Alta","status-red")
    if kind=="cob":
        if val>=95:return("🟢 Objetivo","status-green")
        if val>=90:return("🟡 Atención","status-yellow")
        return("🔴 Baja","status-red")
    if kind=="pos": return ("🟢 Cubierta","status-green") if val>=0 else ("🔴 Déficit","status-red")
    return ("⚪ Informativo","status-yellow")

def norm_cols(df):
    df=df.copy()
    df.columns=[str(c).strip().lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n").replace(" ","_").replace("/","_").replace("%","pct") for c in df.columns]
    return df

# ---------------- header ----------------
logo_col, title_col = st.columns([1, 7])
with logo_col:
    st.image(str(LOGO_PATH), width=125) if LOGO_PATH.exists() else st.markdown("### CRSN")
with title_col:
    st.markdown(f"""<div class="regatas-header"><h1>Club de Regatas San Nicolás · Tesorería</h1>
    <p>{APP_VERSION} · Control financiero · Capitanía por ejercicio · Conciliación cuentas deportivas · Selector mensual · Pesos · Dólares</p></div>""",unsafe_allow_html=True)

menu=st.sidebar.radio("Módulo",[
    "Tablero semanal","Carga manual","Importar archivos","Socios y morosidad","Pesos y dólares",
    "Capitanía","Deportes","Movimientos / desvíos","Base de datos y exportación"
])
st.sidebar.markdown("---")
st.sidebar.caption("Base inicial construida con la información histórica suministrada hasta septiembre de 2026.")

# ---------------- dashboard ----------------
if menu=="Tablero semanal":
    k=metrics()
    section("TABLERO SEMANAL · SITUACIÓN ACTUAL")
    st.markdown(f'<div class="subtle-note">Corte actual: <b>{k["fecha"]}</b>. Comparar siempre con semana anterior y explicar las cinco mayores variaciones.</div>',unsafe_allow_html=True)

    c=st.columns(6)
    items=[
        ("Disponibilidad $",ars(k["disp"]),"Tenencias – Obligaciones",*semaforo("disp",k["disp"])),
        ("Cobertura",ratio(k["cov"]),"Tenencias / Obligaciones",*semaforo("cov",k["cov"])),
        ("Caja ampliada ajustada",ars(k["pos"]),"Excluye venta extraordinaria",*semaforo("pos",k["pos"])),
        ("Morosidad",pct(k["mora"],2),"Último dato disponible",*semaforo("mora",k["mora"])),
        ("Socios pagadores",f'{k["socios"]:,}'.replace(",","."),"Último mes cargado",None,"status-yellow"),
        ("Ingreso Gr./pagador",ars(k["ticket"]),"Ingreso general / pagadores",None,"status-yellow"),
    ]
    for col,it in zip(c,items):
        with col: card(it[0],it[1],it[2],it[3],it[4])

    c=st.columns(6)
    items=[
        ("USD brutos",usd_fmt(k["ubr"]),"Stock nominal",None,"status-yellow"),
        ("USD afectados",usd_fmt(k["uaf"]),"Fondos afectados",None,"status-yellow"),
        ("Venta inmueble",usd_fmt(k["uvi"]),"Reserva patrimonial",None,"status-yellow"),
        ("USD libres ajustados",usd_fmt(k["ufree"]),"Brutos – afectados – venta",None,"status-yellow"),
        ("Costo laboral / ingresos",pct(k["lab_ratio"],1),"Sueldos + F.931 / ingresos",None,"status-yellow"),
        ("Cobrabilidad",pct(k["cob"],1),"Cobrado / facturado",*semaforo("cob",k["cob"])),
    ]
    for col,it in zip(c,items):
        with col: card(it[0],it[1],it[2],it[3],it[4])

    section("EVOLUCIÓN DE LIQUIDEZ")
    wf=fetch_df("SELECT * FROM weekly_finance ORDER BY fecha")
    wf["fecha"]=pd.to_datetime(wf["fecha"])
    wf["disponibilidad"]=wf["tenencias_pesos"]-wf["obligaciones_pesos"]
    wf["cobertura"]=np.where(wf["obligaciones_pesos"]>0,wf["tenencias_pesos"]/wf["obligaciones_pesos"],np.nan)
    a,b=st.columns(2)
    f=go.Figure()
    for name,col in [("Tenencias $","tenencias_pesos"),("Obligaciones $","obligaciones_pesos"),("Disponibilidad $","disponibilidad")]:
        f.add_trace(go.Scatter(x=wf["fecha"],y=wf[col]/1e6,name=name,mode="lines+markers"))
    f.update_layout(title="Tenencias, obligaciones y disponibilidad",yaxis_title="$ millones",height=390,legend_orientation="h")
    a.plotly_chart(f,use_container_width=True)
    f2=px.line(wf,x="fecha",y="cobertura",markers=True,title="Cobertura de obligaciones")
    f2.add_hline(y=1.0,line_dash="dash"); f2.add_hline(y=1.2,line_dash="dot")
    f2.update_layout(yaxis_title="x",height=390)
    b.plotly_chart(f2,use_container_width=True)

    section("CUOTA, SOCIOS Y MOROSIDAD")
    mm=fetch_df("SELECT * FROM monthly_members ORDER BY mes")
    mm["mes_dt"]=pd.to_datetime(mm["mes"]+"-01")
    mm["ticket"]=np.where(mm["socios_pagadores"]>0,mm["ingresos_gr"]/mm["socios_pagadores"],np.nan)
    a,b=st.columns(2)
    f=go.Figure()
    f.add_trace(go.Bar(x=mm["mes_dt"],y=mm["ingresos_gr"]/1e6,name="Ingresos Gr."))
    f.add_trace(go.Scatter(x=mm["mes_dt"],y=mm["ingresos_totales"]/1e6,name="Ingresos totales",mode="lines+markers"))
    f.update_layout(title="Ingresos mensuales",yaxis_title="$ millones",height=380,legend_orientation="h")
    a.plotly_chart(f,use_container_width=True)
    f2=go.Figure()
    f2.add_trace(go.Scatter(x=mm["mes_dt"],y=mm["morosidad_pct"],name="Morosidad %",mode="lines+markers"))
    f2.add_trace(go.Scatter(x=mm["mes_dt"],y=mm["ticket"]/1000,name="Ingreso/pagador ($ mil)",mode="lines+markers"))
    f2.update_layout(title="Morosidad e ingreso por socio",height=380,legend_orientation="h")
    b.plotly_chart(f2,use_container_width=True)

    section("SEMÁFORO DEPORTIVO")
    sp=fetch_df("""SELECT s.* FROM sports s JOIN (SELECT deporte,MAX(fecha) fecha FROM sports GROUP BY deporte)x
                   ON s.deporte=x.deporte AND s.fecha=x.fecha ORDER BY saldo_cuenta""")
    sp["situacion"]=np.where(sp["saldo_cuenta"]<0,"🔴 Déficit",np.where(sp["saldo_cuenta"]<5_000_000,"🟡 Bajo","🟢 Positivo"))
    view=sp[["deporte","saldo_cuenta","situacion"]].rename(columns={"deporte":"Deporte","saldo_cuenta":"Saldo","situacion":"Situación"})
    st.dataframe(view,use_container_width=True,hide_index=True,column_config={"Saldo":st.column_config.NumberColumn(format="$ %.0f")})

elif menu=="Carga manual":
    section("CIERRE SEMANAL · CARGA MANUAL")
    with st.form("week"):
        a,b,c=st.columns(3)
        fecha=a.date_input("Fecha de corte",value=date.today())
        ten=b.number_input("Tenencias $",min_value=0.0,step=1_000_000.0)
        obl=c.number_input("Obligaciones $",min_value=0.0,step=1_000_000.0)
        a,b,c=st.columns(3)
        su=a.number_input("Sueldos",min_value=0.0,step=1_000_000.0)
        f931=b.number_input("F.931",min_value=0.0,step=1_000_000.0)
        fondo=c.number_input("Fondo Reserva $",min_value=0.0,step=1_000_000.0)
        a,b,c,d=st.columns(4)
        ubr=a.number_input("USD brutos",min_value=0.0,step=1000.0)
        uaf=b.number_input("USD afectados",min_value=0.0,step=1000.0)
        uvi=c.number_input("USD patrimoniales / venta inmueble",min_value=0.0,step=1000.0)
        fx=d.number_input("Tipo de cambio",min_value=0.0,step=10.0)
        a,b,c=st.columns(3)
        fact=a.number_input("Facturación cuota exigible",min_value=0.0,step=1_000_000.0)
        cob=b.number_input("Cobranzas cuota",min_value=0.0,step=1_000_000.0)
        deuda=c.number_input("Deuda vencida",min_value=0.0,step=1_000_000.0)
        a,b,c=st.columns(3)
        ing=a.number_input("Ingresos semana",min_value=0.0,step=1_000_000.0)
        cap=b.number_input("Gastos Capitanía",min_value=0.0,step=500_000.0)
        ext=c.number_input("Gastos extraordinarios",min_value=0.0,step=500_000.0)
        obs=st.text_area("Observaciones")
        ok=st.form_submit_button("Guardar / actualizar",type="primary",use_container_width=True)
    if ok:
        execute("""INSERT INTO weekly_finance
        (fecha,tenencias_pesos,obligaciones_pesos,sueldos,f931,fondo_reserva_pesos,usd_brutos,usd_afectados,
         usd_venta_inmueble,tipo_cambio,ingresos_semana,cobranzas_cuota,facturacion_exigible,deuda_vencida,
         gastos_capitania,gastos_extraordinarios,observaciones,fuente)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Manual')
        ON CONFLICT(fecha) DO UPDATE SET
         tenencias_pesos=excluded.tenencias_pesos,obligaciones_pesos=excluded.obligaciones_pesos,
         sueldos=excluded.sueldos,f931=excluded.f931,fondo_reserva_pesos=excluded.fondo_reserva_pesos,
         usd_brutos=excluded.usd_brutos,usd_afectados=excluded.usd_afectados,usd_venta_inmueble=excluded.usd_venta_inmueble,
         tipo_cambio=excluded.tipo_cambio,ingresos_semana=excluded.ingresos_semana,cobranzas_cuota=excluded.cobranzas_cuota,
         facturacion_exigible=excluded.facturacion_exigible,deuda_vencida=excluded.deuda_vencida,
         gastos_capitania=excluded.gastos_capitania,gastos_extraordinarios=excluded.gastos_extraordinarios,
         observaciones=excluded.observaciones,fuente='Manual'""",
         (fecha.isoformat(),ten,obl,su,f931,fondo,ubr,uaf,uvi,fx,ing,cob,fact,deuda,cap,ext,obs))
        st.success("Cierre semanal guardado.")

    section("SOCIOS / CUOTA · CARGA MENSUAL")
    with st.form("month"):
        a,b,c=st.columns(3)
        mesd=a.date_input("Mes",value=date.today().replace(day=1),key="m")
        it=b.number_input("Ingresos totales",min_value=0.0,step=1_000_000.0)
        igr=c.number_input("Ingresos Gr.",min_value=0.0,step=1_000_000.0)
        a,b,c=st.columns(3)
        tg=a.number_input("Total general",min_value=0.0,step=1_000_000.0)
        esp=b.number_input("Específicos",min_value=0.0,step=1_000_000.0)
        socios=c.number_input("Socios pagadores",min_value=0,step=1)
        a,b,c=st.columns(3)
        mora=a.number_input("Morosidad %",min_value=0.0,max_value=100.0,step=0.1)
        morre=b.number_input("Morosos reales",min_value=0,step=1)
        deure=c.number_input("Monto moroso real",min_value=0.0,step=1_000_000.0)
        ajuste=st.number_input("Ajuste de cuota aplicado %",min_value=-100.0,max_value=500.0,step=0.1)
        ok=st.form_submit_button("Guardar / actualizar mes",type="primary",use_container_width=True)
    if ok:
        mes=mesd.strftime("%Y-%m")
        execute("""INSERT INTO monthly_members
        (mes,ingresos_totales,ingresos_gr,total_general,especificos,socios_pagadores,morosidad_pct,morosos_reales,deuda_morosa_real,ajuste_cuota_pct)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(mes) DO UPDATE SET ingresos_totales=excluded.ingresos_totales,ingresos_gr=excluded.ingresos_gr,
        total_general=excluded.total_general,especificos=excluded.especificos,socios_pagadores=excluded.socios_pagadores,
        morosidad_pct=excluded.morosidad_pct,morosos_reales=excluded.morosos_reales,deuda_morosa_real=excluded.deuda_morosa_real,
        ajuste_cuota_pct=excluded.ajuste_cuota_pct""",
        (mes,it,igr,tg,esp,int(socios),mora,int(morre) if morre else None,deure if deure else None,ajuste if ajuste else None))
        st.success("Mes guardado.")

elif menu=="Importar archivos":
    section("IMPORTAR CSV / XLSX")
    tipo=st.selectbox("Tipo",["Cierres semanales","Socios e ingresos mensuales","Capitanía","Cuadro deportes / cuentas","Deportes","Cuentas bancarias / moneda"])
    up=st.file_uploader("Archivo",type=["csv","xlsx","xls"])
    if up:
        try:
            df=pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
            df=norm_cols(df)
            st.dataframe(df.head(50),use_container_width=True)
            if st.button("Importar",type="primary"):
                if tipo=="Cierres semanales":
                    req=["fecha","tenencias_pesos","obligaciones_pesos"]
                    if not all(x in df.columns for x in req): st.error(f"Requiere {req}")
                    else:
                        for _,r in df.iterrows():
                            f=pd.to_datetime(r["fecha"]).date().isoformat()
                            execute("""INSERT INTO weekly_finance
                            (fecha,tenencias_pesos,obligaciones_pesos,sueldos,f931,fondo_reserva_pesos,usd_brutos,usd_afectados,usd_venta_inmueble,
                             tipo_cambio,cobranzas_cuota,facturacion_exigible,deuda_vencida,gastos_capitania,gastos_extraordinarios,fuente)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'Archivo')
                            ON CONFLICT(fecha) DO UPDATE SET
                             tenencias_pesos=excluded.tenencias_pesos,obligaciones_pesos=excluded.obligaciones_pesos,
                             sueldos=excluded.sueldos,f931=excluded.f931,fondo_reserva_pesos=excluded.fondo_reserva_pesos,
                             usd_brutos=excluded.usd_brutos,usd_afectados=excluded.usd_afectados,usd_venta_inmueble=excluded.usd_venta_inmueble,
                             tipo_cambio=excluded.tipo_cambio,cobranzas_cuota=excluded.cobranzas_cuota,facturacion_exigible=excluded.facturacion_exigible,
                             deuda_vencida=excluded.deuda_vencida,gastos_capitania=excluded.gastos_capitania,
                             gastos_extraordinarios=excluded.gastos_extraordinarios,fuente='Archivo'""",
                            (f,float(r.get("tenencias_pesos",0) or 0),float(r.get("obligaciones_pesos",0) or 0),
                             float(r.get("sueldos",0) or 0),float(r.get("f931",0) or 0),float(r.get("fondo_reserva_pesos",0) or 0),
                             float(r.get("usd_brutos",0) or 0),float(r.get("usd_afectados",0) or 0),float(r.get("usd_venta_inmueble",0) or 0),
                             float(r.get("tipo_cambio",0) or 0),float(r.get("cobranzas_cuota",0) or 0),float(r.get("facturacion_exigible",0) or 0),
                             float(r.get("deuda_vencida",0) or 0),float(r.get("gastos_capitania",0) or 0),float(r.get("gastos_extraordinarios",0) or 0)))
                        st.success(f"{len(df)} filas importadas.")
                elif tipo=="Socios e ingresos mensuales":
                    req=["mes","ingresos_totales","ingresos_gr","socios_pagadores"]
                    if not all(x in df.columns for x in req): st.error(f"Requiere {req}")
                    else:
                        for _,r in df.iterrows():
                            execute("""INSERT INTO monthly_members
                            (mes,ingresos_totales,ingresos_gr,total_general,especificos,socios_pagadores,morosidad_pct,morosos_reales,deuda_morosa_real,ajuste_cuota_pct)
                            VALUES(?,?,?,?,?,?,?,?,?,?)
                            ON CONFLICT(mes) DO UPDATE SET ingresos_totales=excluded.ingresos_totales,ingresos_gr=excluded.ingresos_gr,
                            total_general=excluded.total_general,especificos=excluded.especificos,socios_pagadores=excluded.socios_pagadores,
                            morosidad_pct=excluded.morosidad_pct,morosos_reales=excluded.morosos_reales,deuda_morosa_real=excluded.deuda_morosa_real,
                            ajuste_cuota_pct=excluded.ajuste_cuota_pct""",
                            (str(r["mes"])[:7],float(r.get("ingresos_totales",0) or 0),float(r.get("ingresos_gr",0) or 0),
                             float(r.get("total_general",0) or 0),float(r.get("especificos",0) or 0),int(r.get("socios_pagadores",0) or 0),
                             float(r["morosidad_pct"]) if pd.notna(r.get("morosidad_pct")) else None,
                             int(r["morosos_reales"]) if pd.notna(r.get("morosos_reales")) else None,
                             float(r["deuda_morosa_real"]) if pd.notna(r.get("deuda_morosa_real")) else None,
                             float(r["ajuste_cuota_pct"]) if pd.notna(r.get("ajuste_cuota_pct")) else None))
                        st.success(f"{len(df)} meses importados.")
                elif tipo=="Capitanía":
                    req=["fecha","monto"]
                    if not all(x in df.columns for x in req):
                        st.error(f"Requiere {req}. Recomendadas: proveedor, concepto, categoria, beneficiario, observaciones.")
                    else:
                        for _,r in df.iterrows():
                            f=pd.to_datetime(r["fecha"]).date().isoformat()
                            mes=pd.to_datetime(r["fecha"]).strftime("%Y-%m")
                            execute("""INSERT OR REPLACE INTO capitania
                            (fecha,mes,proveedor,concepto,categoria,beneficiario,monto,observaciones)
                            VALUES(?,?,?,?,?,?,?,?)""",
                            (f,mes,str(r.get("proveedor","") or ""),str(r.get("concepto","") or ""),
                             str(r.get("categoria","") or ""),str(r.get("beneficiario","General") or "General"),
                             float(r.get("monto",0) or 0),str(r.get("observaciones","") or "")))
                        st.success(f"{len(df)} movimientos de Capitanía importados.")
                elif tipo=="Cuadro deportes / cuentas":
                    st.info("La importación detecta nombres de disciplinas y saldos en archivos históricos. Luego se reconcilian con Capitanía.")
                    # Busca columnas con nombres similares a deporte / cuenta / actividad y saldo / importe.
                    cols = list(df.columns)
                    col_dep = next((c for c in cols if any(k in c for k in ["deporte","actividad","disciplina","cuenta","concepto"])), cols[0] if cols else None)
                    col_saldo = next((c for c in cols if any(k in c for k in ["saldo","importe","monto","total"])), None)
                    if col_dep is None:
                        st.error("No se pudo identificar una columna de deporte/cuenta.")
                    else:
                        importados=0
                        for _,r in df.iterrows():
                            raw=str(r.get(col_dep,"") or "").strip()
                            if not raw or raw.lower() in ["nan","total","totales"]:
                                continue
                            dep=normalizar_deporte(raw)
                            execute("INSERT OR IGNORE INTO sports_master(deporte,origen) VALUES(?,?)",(dep,"Archivo cuadro deportes"))
                            if col_saldo is not None and pd.notna(r.get(col_saldo)):
                                try:
                                    saldo=float(r.get(col_saldo))
                                    execute("""INSERT OR REPLACE INTO sports
                                    (fecha,deporte,saldo_cuenta,observaciones)
                                    VALUES(?,?,?,?)""",
                                    (date.today().isoformat(),dep,saldo,"Importado desde cuadro deportes/cuentas"))
                                except Exception:
                                    pass
                            importados += 1
                        st.success(f"{importados} filas procesadas. Revisar el módulo Deportes para ver coincidencias.")
                elif tipo=="Deportes":
                    req=["fecha","deporte"]
                    if not all(x in df.columns for x in req): st.error(f"Requiere {req}")
                    else:
                        for _,r in df.iterrows():
                            f=pd.to_datetime(r["fecha"]).date().isoformat()
                            execute("""INSERT INTO sports(fecha,deporte,ingresos,egresos_directos,gastos_indirectos,saldo_cuenta,socios,cuota_promedio,observaciones)
                            VALUES(?,?,?,?,?,?,?,?,?)
                            ON CONFLICT(fecha,deporte) DO UPDATE SET ingresos=excluded.ingresos,egresos_directos=excluded.egresos_directos,
                            gastos_indirectos=excluded.gastos_indirectos,saldo_cuenta=excluded.saldo_cuenta,socios=excluded.socios,
                            cuota_promedio=excluded.cuota_promedio,observaciones=excluded.observaciones""",
                            (f,str(r["deporte"]),float(r.get("ingresos",0) or 0),float(r.get("egresos_directos",0) or 0),
                             float(r.get("gastos_indirectos",0) or 0),float(r.get("saldo_cuenta",0) or 0),int(r.get("socios",0) or 0),
                             float(r.get("cuota_promedio",0) or 0),str(r.get("observaciones","") or "")))
                        st.success(f"{len(df)} registros deportivos importados.")
                else:
                    req=["fecha","cuenta","moneda","saldo"]
                    if not all(x in df.columns for x in req): st.error(f"Requiere {req}")
                    else:
                        for _,r in df.iterrows():
                            f=pd.to_datetime(r["fecha"]).date().isoformat()
                            execute("""INSERT INTO accounts(fecha,cuenta,moneda,saldo,tipo_cambio,afectado,categoria,observaciones)
                            VALUES(?,?,?,?,?,?,?,?)
                            ON CONFLICT(fecha,cuenta,moneda) DO UPDATE SET saldo=excluded.saldo,tipo_cambio=excluded.tipo_cambio,
                            afectado=excluded.afectado,categoria=excluded.categoria,observaciones=excluded.observaciones""",
                            (f,str(r["cuenta"]),str(r["moneda"]).upper(),float(r["saldo"] or 0),float(r.get("tipo_cambio",0) or 0),
                             int(r.get("afectado",0) or 0),str(r.get("categoria","") or ""),str(r.get("observaciones","") or "")))
                        st.success(f"{len(df)} cuentas importadas.")
        except Exception as e: st.exception(e)

    section("DESCARGAR PLANTILLAS")
    templates={
        "cierres":pd.DataFrame(columns=["fecha","tenencias_pesos","obligaciones_pesos","sueldos","f931","fondo_reserva_pesos","usd_brutos","usd_afectados","usd_venta_inmueble","tipo_cambio","cobranzas_cuota","facturacion_exigible","deuda_vencida","gastos_capitania","gastos_extraordinarios"]),
        "socios":pd.DataFrame(columns=["mes","ingresos_totales","ingresos_gr","total_general","especificos","socios_pagadores","morosidad_pct","morosos_reales","deuda_morosa_real","ajuste_cuota_pct"]),
        "capitania":pd.DataFrame(columns=["fecha","proveedor","concepto","categoria","beneficiario","monto","observaciones"]),
        "deportes":pd.DataFrame(columns=["fecha","deporte","ingresos","egresos_directos","gastos_indirectos","saldo_cuenta","socios","cuota_promedio","observaciones"]),
        "cuentas":pd.DataFrame(columns=["fecha","cuenta","moneda","saldo","tipo_cambio","afectado","categoria","observaciones"])
    }
    cols=st.columns(5)
    for col,(name,t) in zip(cols,templates.items()):
        col.download_button(name.title(),t.to_csv(index=False).encode("utf-8-sig"),f"plantilla_{name}.csv","text/csv")

elif menu=="Socios y morosidad":
    section("SOCIOS · CUOTA · MOROSIDAD")
    mm=fetch_df("SELECT * FROM monthly_members ORDER BY mes")
    mm["ticket"]=np.where(mm["socios_pagadores"]>0,mm["ingresos_gr"]/mm["socios_pagadores"],np.nan)
    mm["padron_equiv"]=np.where(mm["morosidad_pct"].notna(),mm["socios_pagadores"]/(1-mm["morosidad_pct"]/100),np.nan)
    mm["morosos_equiv"]=mm["padron_equiv"]-mm["socios_pagadores"]
    mm["mora_proxy"]=mm["morosos_equiv"]*mm["ticket"]
    st.dataframe(mm,use_container_width=True,hide_index=True)
    a,b=st.columns(2)
    a.plotly_chart(px.line(mm,x="mes",y="ticket",markers=True,title="Ingreso por socio pagador"),use_container_width=True)
    f=px.line(mm,x="mes",y="morosidad_pct",markers=True,title="Morosidad a un mes"); f.add_hline(y=15,line_dash="dash")
    b.plotly_chart(f,use_container_width=True)
    st.info("Cuando se cargan morosos reales y deuda morosa real, esos valores reemplazan el proxy para la gestión.")

elif menu=="Pesos y dólares":
    section("PESOS Y DÓLARES · FLUJO DE CAMBIO")
    wf=fetch_df("SELECT * FROM weekly_finance ORDER BY fecha")
    wf["disp"]=wf["tenencias_pesos"]-wf["obligaciones_pesos"]
    wf["usd_libres"]=(wf["usd_brutos"]-wf["usd_afectados"]-wf["usd_venta_inmueble"]).clip(lower=0)
    wf["usd_libres_ars"]=wf["usd_libres"]*wf["tipo_cambio"]
    wf["pos_ajustada"]=wf["disp"]+wf["usd_libres_ars"]
    f=go.Figure()
    f.add_trace(go.Scatter(x=wf["fecha"],y=wf["usd_brutos"],name="USD brutos",mode="lines+markers"))
    f.add_trace(go.Scatter(x=wf["fecha"],y=wf["usd_libres"],name="USD libres ajustados",mode="lines+markers"))
    f.update_layout(title="Stock de USD",yaxis_title="USD",legend_orientation="h")
    st.plotly_chart(f,use_container_width=True)
    a,b=st.columns(2)
    f2=go.Figure()
    f2.add_trace(go.Bar(x=wf["fecha"],y=wf["disp"]/1e6,name="Disponibilidad $"))
    f2.add_trace(go.Scatter(x=wf["fecha"],y=wf["pos_ajustada"]/1e6,name="Posición ampliada ajustada",mode="lines+markers"))
    f2.update_layout(title="Pesos operativos vs USD ajustados",yaxis_title="$ millones",height=390,legend_orientation="h")
    a.plotly_chart(f2,use_container_width=True)
    b.plotly_chart(px.line(wf,x="fecha",y="tipo_cambio",markers=True,title="Tipo de cambio utilizado"),use_container_width=True)
    section("DETALLE POR CUENTA")
    ac=fetch_df("SELECT * FROM accounts ORDER BY fecha DESC, moneda, cuenta")
    if ac.empty: st.info("Cargar o importar detalle por banco/cuenta.")
    else: st.dataframe(ac,use_container_width=True,hide_index=True)

elif menu=="Capitanía":
    section("CAPITANÍA · GASTOS Y DISTRIBUCIÓN POR DEPORTE")

    cap_total = fetch_df("SELECT * FROM capitania ORDER BY fecha")
    cap_det = fetch_df("SELECT * FROM capitania_identificada ORDER BY fecha")
    cap_total = filtro_mes(cap_total,"fecha","mes_capitania","Mes a visualizar")
    cap_det = filtro_mes(cap_det,"fecha","mes_capitania_det","Detalle identificado: mes")

    if cap_total.empty:
        st.info("Todavía no hay datos mensuales de Capitanía.")
    else:
        cap_total["fecha_dt"]=pd.to_datetime(cap_total["fecha"])
        mensual = cap_total[
            (cap_total["beneficiario"]=="General") &
            (cap_total["concepto"]=="Gasto mensual Capitanía")
        ].copy()
        mensual["mes_dt"]=pd.to_datetime(mensual["mes"]+"-01")
        mensual=mensual.sort_values("mes_dt")

        # Ejercicios: período 1 hasta febrero inclusive; período 2 desde marzo.
        p1 = mensual[mensual["mes_dt"] < pd.Timestamp("2026-03-01")].copy()
        p2 = mensual[mensual["mes_dt"] >= pd.Timestamp("2026-03-01")].copy()
        p1["acumulado_ejercicio"]=p1["monto"].cumsum()
        p2["acumulado_ejercicio"]=p2["monto"].cumsum()

        total=float(mensual["monto"].sum())
        total_p1=float(p1["monto"].sum())
        total_p2=float(p2["monto"].sum())
        ultimo=float(mensual.iloc[-1]["monto"]) if not mensual.empty else 0

        asignado = cap_det.groupby(["deporte_normalizado","estado_match"],as_index=False)["monto"].sum().sort_values("monto",ascending=False) if not cap_det.empty else pd.DataFrame()
        total_asignado=float(asignado["monto"].sum()) if not asignado.empty else 0
        deportes_match=int((asignado["estado_match"]=="Coincide").sum()) if not asignado.empty else 0

        c1,c2,c3,c4,c5,c6=st.columns(6)
        with c1: card("Gasto total acumulado",ars(total),"Desde inicio de información")
        with c2: card("Acumulado inicio–Feb 2026",ars(total_p1),"Ejercicio / período cerrado")
        with c3: card("Acumulado Mar 2026–actual",ars(total_p2),"Ejercicio actual")
        with c4: card("Último mes cargado",ars(ultimo),mensual.iloc[-1]["mes"] if not mensual.empty else "")
        with c5: card("Gasto asignado a deportes",ars(total_asignado),"Movimientos con identificación")
        with c6: card("Coincidencias exactas",str(deportes_match),"Con cuenta deportiva")

        a,b=st.columns([1.35,1])
        with a:
            f=go.Figure()
            f.add_trace(go.Bar(x=mensual["mes"],y=mensual["monto"]/1e6,name="Gasto mensual"))
            if not p1.empty:
                f.add_trace(go.Scatter(x=p1["mes"],y=p1["acumulado_ejercicio"]/1e6,name="Acumulado ejercicio 1",mode="lines+markers"))
            if not p2.empty:
                f.add_trace(go.Scatter(x=p2["mes"],y=p2["acumulado_ejercicio"]/1e6,name="Acumulado ejercicio 2",mode="lines+markers"))
            f.add_vline(x="2026-03",line_dash="dash",line_color="#F28C28")
            f.update_layout(title="Gasto mensual y acumulado por ejercicio",yaxis_title="$ millones",height=430,legend_orientation="h")
            st.plotly_chart(f,use_container_width=True)

        with b:
            if not asignado.empty:
                f2=px.bar(asignado.sort_values("monto"),x="monto",y="deporte_normalizado",orientation="h",
                          color="estado_match",title="Gasto de Capitanía identificado por deporte")
                f2.update_layout(xaxis_title="$",yaxis_title="",height=430,legend_title="Coincidencia")
                st.plotly_chart(f2,use_container_width=True)

        section("COMPARATIVO ENTRE EJERCICIOS")
        comp=pd.DataFrame([
            ["Inicio información – Feb 2026",total_p1, total_p1/total*100 if total else 0],
            ["Mar 2026 – Actual",total_p2, total_p2/total*100 if total else 0],
            ["TOTAL",total,100.0 if total else 0],
        ],columns=["Período","Gasto acumulado","Participación %"])
        st.dataframe(comp,use_container_width=True,hide_index=True,
                     column_config={"Gasto acumulado":st.column_config.NumberColumn(format="$ %.0f"),
                                    "Participación %":st.column_config.NumberColumn(format="%.1f %%")})

    section("RECONCILIACIÓN CAPITANÍA ↔ CUENTAS DEPORTIVAS")
    master=fetch_df("SELECT deporte FROM sports_master WHERE activo=1 ORDER BY deporte")
    saldos=fetch_df("""SELECT s.deporte,s.fecha,s.saldo_cuenta
                       FROM sports s
                       JOIN (SELECT deporte,MAX(fecha) fecha FROM sports GROUP BY deporte) u
                       ON s.deporte=u.deporte AND s.fecha=u.fecha""")
    if not cap_det.empty:
        imp=cap_det.groupby(["deporte_normalizado","estado_match"],as_index=False)["monto"].sum()
    else:
        imp=pd.DataFrame(columns=["deporte_normalizado","estado_match","monto"])

    if not master.empty:
        recon=master.rename(columns={"deporte":"Deporte"}).copy()
        recon=recon.merge(saldos.rename(columns={"deporte":"Deporte","saldo_cuenta":"Saldo cuenta","fecha":"Último corte"}),on="Deporte",how="left")
        recon=recon.merge(imp[imp["estado_match"]=="Coincide"][["deporte_normalizado","monto"]].rename(columns={"deporte_normalizado":"Deporte","monto":"Capitanía asignada"}),on="Deporte",how="left")
        recon["Capitanía asignada"]=recon["Capitanía asignada"].fillna(0)
        recon["Saldo ajustado gerencial"]=recon["Saldo cuenta"].fillna(0)-recon["Capitanía asignada"]
        recon["Estado"]=np.where(recon["Saldo cuenta"].isna(),"⚪ Sin saldo cargado",
                           np.where(recon["Saldo ajustado gerencial"]<0,"🔴 Déficit ajustado","🟢 Positivo ajustado"))
        st.dataframe(recon,use_container_width=True,hide_index=True,
                     column_config={
                         "Saldo cuenta":st.column_config.NumberColumn(format="$ %.0f"),
                         "Capitanía asignada":st.column_config.NumberColumn(format="$ %.0f"),
                         "Saldo ajustado gerencial":st.column_config.NumberColumn(format="$ %.0f")
                     })

    ambiguos = imp[imp["estado_match"]!="Coincide"].copy() if not imp.empty else pd.DataFrame()
    if not ambiguos.empty:
        st.warning("Existen imputaciones de Capitanía que no pueden asociarse automáticamente a una cuenta deportiva.")
        st.dataframe(ambiguos,use_container_width=True,hide_index=True,
                     column_config={"monto":st.column_config.NumberColumn(format="$ %.0f")})

    section("DETALLE DE GASTOS IDENTIFICADOS EN CAPITANÍA")
    if cap_det.empty:
        st.info("No hay movimientos identificados para el filtro seleccionado.")
    else:
        st.dataframe(cap_det[["fecha","proveedor","concepto","categoria","beneficiario_original","deporte_normalizado","estado_match","monto","observaciones"]]
                     .sort_values("fecha",ascending=False),
                     use_container_width=True,hide_index=True,
                     column_config={"monto":st.column_config.NumberColumn("Monto",format="$ %.0f")})
        st.caption("La imputación es gerencial: debe validarse contra factura, orden de compra y centro de costo antes de una reclasificación contable.")

    section("CARGA MANUAL DE CAPITANÍA")
    with st.form("capitania_form"):
        a,b,c=st.columns(3)
        fd=a.date_input("Fecha",value=date.today(),key="cap_date")
        proveedor=b.text_input("Proveedor")
        categoria=c.selectbox("Categoría",[
            "Mantenimiento general","Obras / construcción","Electricidad / iluminación",
            "Equipamiento / mobiliario","Limpieza / químicos","Maquinaria / rodados",
            "Personal / ropa / horas extra","Ferretería / repuestos","Deporte","Otros"
        ])
        concepto=st.text_input("Concepto / descripción")
        a,b=st.columns(2)
        beneficiario=a.text_input("Beneficiario / deporte",value="General")
        monto=b.number_input("Monto",min_value=0.0,step=100_000.0)
        obs=st.text_area("Observaciones",key="cap_obs")
        ok=st.form_submit_button("Guardar movimiento de Capitanía",type="primary",use_container_width=True)

    if ok and monto>0:
        execute("""INSERT OR REPLACE INTO capitania
        (fecha,mes,proveedor,concepto,categoria,beneficiario,monto,observaciones)
        VALUES(?,?,?,?,?,?,?,?)""",
        (fd.isoformat(),fd.strftime("%Y-%m"),proveedor.strip(),concepto.strip(),categoria,
         beneficiario.strip() or "General",monto,obs.strip()))
        dep_norm=normalizar_deporte(beneficiario)
        deportes_validos=set(fetch_df("SELECT deporte FROM sports_master WHERE activo=1")["deporte"].tolist())
        match=estado_match_deporte(dep_norm,deportes_validos)
        if beneficiario.strip().lower()!="general":
            execute("""INSERT OR REPLACE INTO capitania_identificada
            (fecha,proveedor,concepto,categoria,beneficiario_original,deporte_normalizado,estado_match,monto,observaciones)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (fd.isoformat(),proveedor.strip(),concepto.strip(),categoria,beneficiario.strip(),dep_norm,match,monto,obs.strip()))
        st.success("Movimiento de Capitanía guardado y conciliado.")

elif menu=="Deportes":
    section("DEPORTES · CUENTAS, CAPITANÍA Y RESULTADO AJUSTADO")

    # Catálogo consolidado: cuentas + maestro + gastos de Capitanía.
    master=fetch_df("SELECT deporte,origen,activo,observaciones FROM sports_master WHERE activo=1 ORDER BY deporte")
    if not master.empty:
        st.caption(f"Catálogo consolidado: {len(master)} deportes/áreas activas.")
        with st.expander("Ver catálogo completo de deportes",expanded=False):
            st.dataframe(master,use_container_width=True,hide_index=True)

    sp=fetch_df("SELECT * FROM sports ORDER BY fecha DESC,deporte")
    latest_date=sp["fecha"].max()
    latest=sp[sp["fecha"]==latest_date].copy()
    latest["resultado_economico"]=latest["ingresos"]-latest["egresos_directos"]-latest["gastos_indirectos"]
    cap_imp=fetch_df("SELECT deporte_normalizado,SUM(monto) monto FROM capitania_identificada WHERE estado_match='Coincide' GROUP BY deporte_normalizado")
    latest=latest.merge(cap_imp.rename(columns={"deporte_normalizado":"deporte","monto":"capitania_asignada"}),on="deporte",how="left")
    latest["capitania_asignada"]=latest["capitania_asignada"].fillna(0)
    latest["saldo_ajustado_capitania"]=latest["saldo_cuenta"]-latest["capitania_asignada"]

    latest["cobertura_pct"]=np.where(latest["egresos_directos"]+latest["gastos_indirectos"]>0,latest["ingresos"]/(latest["egresos_directos"]+latest["gastos_indirectos"])*100,np.nan)
    f=px.bar(latest.sort_values("saldo_ajustado_capitania"),x="saldo_ajustado_capitania",y="deporte",orientation="h",title=f"Saldo por deporte ajustado por Capitanía · {latest_date}")
    f.update_layout(height=max(450,28*len(latest)),xaxis_title="$",yaxis_title="")
    st.plotly_chart(f,use_container_width=True)
    st.dataframe(latest,use_container_width=True,hide_index=True)
    section("CARGA MANUAL DE DEPORTE")
    with st.form("sport"):
        a,b,c=st.columns(3)
        fd=a.date_input("Fecha",value=date.today(),key="sd"); dep=b.text_input("Deporte"); soc=c.number_input("Socios",min_value=0,step=1)
        a,b,c=st.columns(3)
        ing=a.number_input("Ingresos propios",min_value=0.0,step=500_000.0); eg=b.number_input("Egresos directos",min_value=0.0,step=500_000.0); ind=c.number_input("Gastos indirectos / Capitanía",min_value=0.0,step=500_000.0)
        a,b=st.columns(2)
        sal=a.number_input("Saldo de cuenta",step=500_000.0); cuota=b.number_input("Cuota promedio",min_value=0.0,step=1000.0)
        obs=st.text_area("Observaciones",key="so")
        ok=st.form_submit_button("Guardar deporte",type="primary")
    if ok and dep.strip():
        execute("""INSERT INTO sports(fecha,deporte,ingresos,egresos_directos,gastos_indirectos,saldo_cuenta,socios,cuota_promedio,observaciones)
        VALUES(?,?,?,?,?,?,?,?,?)
        ON CONFLICT(fecha,deporte) DO UPDATE SET ingresos=excluded.ingresos,egresos_directos=excluded.egresos_directos,
        gastos_indirectos=excluded.gastos_indirectos,saldo_cuenta=excluded.saldo_cuenta,socios=excluded.socios,cuota_promedio=excluded.cuota_promedio,observaciones=excluded.observaciones""",
        (fd.isoformat(),dep.strip(),ing,eg,ind,sal,int(soc),cuota,obs))
        st.success("Registro guardado.")

elif menu=="Movimientos / desvíos":
    section("MOVIMIENTOS RELEVANTES")
    st.markdown('<div class="subtle-note">Umbral propuesto: explicar todo movimiento no recurrente superior a <b>máx. $10 M o 2% del ingreso mensual</b>.</div>',unsafe_allow_html=True)
    with st.form("event"):
        a,b,c=st.columns(3)
        fd=a.date_input("Fecha",value=date.today(),key="ed")
        tipo=b.selectbox("Tipo",["Cobranza","Pago","Sueldo","F.931","SAC","Compra USD","Venta USD","Inversión","Deporte","Capitanía","Otro"])
        mon=c.selectbox("Moneda",["ARS","USD"])
        con=st.text_input("Concepto")
        a,b,c=st.columns(3)
        monto=a.number_input("Monto",min_value=0.0,step=100_000.0); centro=b.text_input("Centro de costo"); resp=c.text_input("Responsable")
        obs=st.text_area("Observaciones",key="eo")
        ok=st.form_submit_button("Registrar",type="primary")
    if ok and con.strip():
        execute("INSERT INTO events(fecha,tipo,concepto,monto,moneda,centro_costo,responsable,observaciones) VALUES(?,?,?,?,?,?,?,?)",(fd.isoformat(),tipo,con,monto,mon,centro,resp,obs))
        st.success("Movimiento registrado.")
    st.dataframe(fetch_df("SELECT * FROM events ORDER BY fecha DESC,id DESC"),use_container_width=True,hide_index=True)

else:
    section("EXPORTACIÓN Y RESPALDO")
    tables={
        "cierres_semanales":fetch_df("SELECT * FROM weekly_finance ORDER BY fecha"),
        "socios_mensual":fetch_df("SELECT * FROM monthly_members ORDER BY mes"),
        "capitania":fetch_df("SELECT * FROM capitania ORDER BY fecha"),
        "capitania_identificada":fetch_df("SELECT * FROM capitania_identificada ORDER BY fecha"),
        "maestro_deportes":fetch_df("SELECT * FROM sports_master ORDER BY deporte"),
        "deportes":fetch_df("SELECT * FROM sports ORDER BY fecha,deporte"),
        "cuentas":fetch_df("SELECT * FROM accounts ORDER BY fecha,moneda,cuenta"),
        "movimientos":fetch_df("SELECT * FROM events ORDER BY fecha,id"),
    }
    for name,df in tables.items():
        st.download_button(f"Descargar {name}.csv",df.to_csv(index=False).encode("utf-8-sig"),f"{name}.csv","text/csv",key=name)
    if DB_PATH.exists():
        st.download_button("Descargar respaldo SQLite",DB_PATH.read_bytes(),"regatas_tesoreria_backup.db","application/octet-stream",use_container_width=True)
    section("DEFINICIÓN DE KPI")
    defs=pd.DataFrame([
        ["Disponibilidad $","Tenencias $ - Obligaciones $","Liquidez inmediata"],
        ["Cobertura","Tenencias $ / Obligaciones $","Objetivo sugerido ≥1,20x"],
        ["Caja ampliada ajustada","Disponibilidad $ + USD libres ajustados × TC","Excluye USD afectados y venta patrimonial"],
        ["Cobrabilidad","Cobranzas cuota / Facturación exigible","Objetivo sugerido ≥95%"],
        ["Morosidad","Deuda vencida / Facturación exigible","Alerta >15%"],
        ["Ingreso por socio","Ingresos Gr. / Socios pagadores","Comparar con ajuste de cuota / UTEDyC"],
        ["Costo laboral / ingresos","(Sueldos + F.931) / Ingresos","Separar efecto SAC"],
        ["Capitanía / ingresos","Gasto mensual Capitanía / Ingresos totales","Peso de estructura operativa"],
        ["Cobertura deporte","Ingresos / (gastos directos + indirectos)","Autosustentabilidad"],
        ["Fondo de Reserva","Fondos a favor - fondos en contra","Separar recursos afectados"],
        ["Gastos extraordinarios","Pagos no recurrentes > umbral","Explicación obligatoria"],
    ],columns=["KPI","Fórmula","Uso"])
    st.dataframe(defs,use_container_width=True,hide_index=True)
