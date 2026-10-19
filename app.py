import json
import os
from datetime import date, timedelta

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# ============================================================
# PORT TRACKER // FUTURE MARITIME INTELLIGENCE INTERFACE
# Replace your existing app.py with this file.
# ============================================================

st.set_page_config(
    page_title="PORT TRACKER // Maritime Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

DAILY_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/"
    "arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
)
GULF_COUNTRIES = ["ARE", "QAT", "IRQ", "IRN", "KWT", "BHR", "SAU", "OMN"]
DATA_DIR = "data" if os.path.exists("data/port_summary.csv") else "app_data/data"


# --------------------------- CSS / visual system ---------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
  --bg: #050b14;
  --panel: #0a1422;
  --panel2: #0e1d2d;
  --line: rgba(105, 185, 218, .19);
  --cyan: #45f0df;
  --blue: #59aaff;
  --violet: #9c8cff;
  --red: #ff6f83;
  --green: #5bf0b5;
  --text: #eaf4ff;
  --muted: #7f9ab2;
}

.stApp {
  color: var(--text);
  background:
    radial-gradient(ellipse at 50% -20%, rgba(23, 112, 150, .20), transparent 42%),
    radial-gradient(ellipse at 100% 45%, rgba(67, 73, 165, .09), transparent 32%),
    var(--bg);
  font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: rgba(5,11,20,.82); backdrop-filter: blur(18px); }
.block-container { max-width: 1900px; padding-top: 1.25rem; padding-bottom: 3rem; }
h1,h2,h3,h4 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text) !important; letter-spacing: -.035em; }
p, label, .stMarkdown { color: var(--text); }
[data-testid="stCaptionContainer"] { color: var(--muted) !important; }

@keyframes enter { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
@keyframes scan { 0% { transform:translateX(-130%); } 100% { transform:translateX(420%); } }
@keyframes pulse { 0%,100% { box-shadow:0 0 0 0 rgba(69,240,223,0); } 50% { box-shadow:0 0 22px 1px rgba(69,240,223,.08); } }
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:.35; } }

.topbar {
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  padding: 8px 2px 17px; border-bottom:1px solid var(--line); margin-bottom:20px;
  animation: enter .45s ease both;
}
.brand { display:flex; align-items:center; gap:13px; }
.brand-mark {
  width:43px; height:43px; border-radius:13px; display:flex; align-items:center; justify-content:center;
  color:var(--cyan); font-size:23px; font-weight:700;
  background:linear-gradient(135deg,rgba(69,240,223,.14),rgba(89,170,255,.13));
  border:1px solid rgba(69,240,223,.34); box-shadow:0 0 24px rgba(69,240,223,.08);
}
.brand-name { font-family:'Space Grotesk',sans-serif; font-size:1.14rem; letter-spacing:.08em; font-weight:700; }
.brand-sub { font-family:'DM Mono',monospace; color:var(--muted); font-size:.65rem; letter-spacing:.12em; margin-top:3px; }
.top-right { font-family:'DM Mono',monospace; color:var(--muted); font-size:.7rem; text-align:right; letter-spacing:.07em; line-height:1.9; }
.live-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--cyan); margin-right:7px; animation:blink 1.8s ease infinite; }

.hero {
  position:relative; overflow:hidden; border:1px solid rgba(69,240,223,.20); border-radius:18px;
  background:linear-gradient(110deg,rgba(11,28,45,.98),rgba(8,18,33,.95));
  padding:24px 27px; margin-bottom:16px; animation:enter .5s ease both;
}
.hero:after { content:""; position:absolute; left:0; bottom:0; height:2px; width:22%; background:linear-gradient(90deg,transparent,var(--cyan),transparent); animation:scan 8s linear infinite; }
.eyebrow { font-family:'DM Mono',monospace; color:var(--cyan); font-size:.68rem; letter-spacing:.18em; margin-bottom:10px; }
.hero-title { font-family:'Space Grotesk',sans-serif; font-weight:700; letter-spacing:-.055em; font-size:clamp(1.7rem,3vw,2.7rem); line-height:1.08; }
.hero-title span { color:var(--cyan); }
.hero-copy { color:#93abc1; font-size:.88rem; line-height:1.7; margin-top:10px; max-width:850px; }
.system-pill { display:inline-flex; gap:8px; align-items:center; margin-top:14px; padding:6px 10px; border-radius:6px; border:1px solid rgba(69,240,223,.24); color:#8bf7e9; background:rgba(69,240,223,.055); font: .63rem 'DM Mono',monospace; letter-spacing:.08em; }

.section-line { display:flex; justify-content:space-between; align-items:end; gap:10px; margin:22px 0 10px; }
.section-title { font-family:'Space Grotesk',sans-serif; font-size:1rem; font-weight:700; letter-spacing:.01em; }
.section-meta { color:var(--muted); font: .65rem 'DM Mono',monospace; letter-spacing:.07em; text-align:right; }

[data-testid="stMetric"] {
  background:linear-gradient(145deg,rgba(13,31,49,.97),rgba(8,19,32,.96));
  border:1px solid var(--line); border-radius:13px; padding:14px 16px; min-height:103px;
  animation:enter .5s ease both; transition:transform .2s ease,border-color .2s ease,box-shadow .2s ease;
}
[data-testid="stMetric"]:hover { transform:translateY(-3px); border-color:rgba(69,240,223,.48); box-shadow:0 8px 28px rgba(0,0,0,.25); }
[data-testid="stMetricLabel"] { color:var(--muted) !important; font: .68rem 'DM Mono',monospace !important; letter-spacing:.06em; text-transform:uppercase; }
[data-testid="stMetricValue"] { color:var(--text) !important; font:700 clamp(1.4rem,2vw,1.9rem) 'Space Grotesk',sans-serif !important; }
[data-testid="stMetricDelta"] { font-size:.73rem !important; }

.map-shell { border:1px solid rgba(69,240,223,.24); border-radius:15px; overflow:hidden; background:#07111d; box-shadow:0 12px 45px rgba(0,0,0,.2); }
.map-caption { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:11px 15px; border-bottom:1px solid var(--line); background:rgba(10,25,40,.96); }
.map-caption-title { font: .73rem 'DM Mono',monospace; color:#d8e9f7; letter-spacing:.1em; }
.map-caption-note { font: .64rem 'DM Mono',monospace; color:var(--muted); }
.legend { display:flex; gap:15px; flex-wrap:wrap; font: .67rem 'DM Mono',monospace; color:#a5bdd0; }
.legend span { display:flex; align-items:center; gap:6px; }
.dot { width:7px; height:7px; display:inline-block; border-radius:50%; }
.panel { background:linear-gradient(145deg,rgba(12,28,45,.97),rgba(7,18,31,.97)); border:1px solid var(--line); border-radius:14px; padding:16px; }
.panel-title { font: .75rem 'DM Mono',monospace; color:#d8e9f7; letter-spacing:.09em; margin-bottom:4px; }
.panel-sub { color:var(--muted); font-size:.77rem; line-height:1.55; margin-bottom:13px; }
.mono { font-family:'DM Mono',monospace; }
.stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { color:var(--muted); padding:10px 14px; background:transparent; border-radius:8px 8px 0 0; transition:all .18s ease; }
.stTabs [aria-selected="true"] { color:var(--cyan) !important; background:rgba(69,240,223,.07) !important; }
.stButton>button,.stDownloadButton>button { border:1px solid rgba(69,240,223,.32); border-radius:9px; color:var(--text); background:rgba(69,240,223,.08); transition:all .2s ease; }
.stButton>button:hover,.stDownloadButton>button:hover { transform:translateY(-2px); border-color:var(--cyan); color:white; background:rgba(69,240,223,.15); }
[data-baseweb="select"]>div,[data-baseweb="input"]>div { background:#0a1928; border-color:var(--line); border-radius:9px; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#091522,#060d17); border-right:1px solid var(--line); }
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:var(--text) !important; }
[data-testid="stDataFrame"],[data-testid="stTable"] { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
hr { border-color:var(--line); }
.footer { margin-top:28px; border-top:1px solid var(--line); padding-top:14px; color:var(--muted); font:.66rem 'DM Mono',monospace; line-height:1.9; }
@media(max-width:700px) { .top-right { display:none; } .hero { padding:19px; } .section-line { align-items:start; flex-direction:column; } .section-meta { text-align:left; } }
@media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; } }
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------- Data functions ---------------------------

@st.cache_data(show_spinner=False)
def load_data(data_dir):
    summary_path = os.path.join(data_dir, "port_summary.csv")
    monthly_path = os.path.join(data_dir, "country_monthly.csv")
    info_path = os.path.join(data_dir, "data_info.json")
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Missing {summary_path}")
    ports = pd.read_csv(summary_path)
    monthly = pd.read_csv(monthly_path) if os.path.exists(monthly_path) else pd.DataFrame()
    info = {}
    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)
    if "month_start" in monthly.columns:
        monthly["month_start"] = pd.to_datetime(monthly["month_start"], errors="coerce")
    return ports, monthly, info


@st.cache_data(ttl=3600, show_spinner=False)
def port_daily(portid, since):
    rows, offset, page_size = [], 0, 1000
    while True:
        params = {
            "where": f"portid = '{portid}' AND date >= '{since}'",
            "outFields": "date,portcalls",
            "returnGeometry": "false",
            "orderByFields": "date ASC",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "f": "json",
        }
        try:
            response = requests.get(DAILY_URL, params=params, timeout=25)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            break
        features = payload.get("features", [])
        if not features:
            break
        for feature in features:
            attrs = feature.get("attributes", {})
            raw_date = attrs.get("date")
            if raw_date is None:
                continue
            parsed = pd.to_datetime(raw_date, unit="ms", errors="coerce") if isinstance(raw_date, (int, float)) else pd.to_datetime(raw_date, errors="coerce")
            rows.append({"date": parsed, "portcalls": pd.to_numeric(attrs.get("portcalls"), errors="coerce")})
        if len(features) < page_size:
            break
        offset += page_size
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.dropna(subset=["date"]).sort_values("date")
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df


def find_col(df, candidates):
    return next((c for c in candidates if c in df.columns), None)


def num(df, col):
    return pd.to_numeric(df[col], errors="coerce").fillna(0) if col else pd.Series(0, index=df.index, dtype=float)


def label(v):
    return "Unknown" if pd.isna(v) or str(v).strip() == "" else str(v)


# --------------------------- Load data ---------------------------

try:
    ports, monthly, info = load_data(DATA_DIR)
except Exception as exc:
    st.error(f"Could not load Port Tracker data: {exc}")
    st.info("Keep port_summary.csv in data/ or app_data/data/. country_monthly.csv and data_info.json are optional.")
    st.stop()

if ports.empty:
    st.warning("port_summary.csv is empty.")
    st.stop()

id_col = find_col(ports, ["portid", "port_id", "id"])
name_col = find_col(ports, ["port_name", "name", "port", "portname"])
country_col = find_col(ports, ["country", "country_name"])
iso_col = find_col(ports, ["iso3", "country_iso3", "iso_a3"])
continent_col = find_col(ports, ["continent"])
lat_col = find_col(ports, ["latitude", "lat", "y"])
lon_col = find_col(ports, ["longitude", "lon", "lng", "x"])

if not id_col:
    st.error("Your CSV needs a port ID column, such as portid or port_id.")
    st.stop()

ports[id_col] = ports[id_col].astype(str)
ports["_name"] = ports[name_col].map(label) if name_col else ports[id_col]
ports["_country"] = ports[country_col].map(label) if country_col else "Unknown"
ports["_continent"] = ports[continent_col].map(label) if continent_col else "Unknown"
ports["_iso3"] = ports[iso_col].astype(str).str.upper() if iso_col else ""

# Determine which comparison columns are available.
available_windows = [
    days for days in (28, 90)
    if f"base_{days}" in ports.columns and f"recent_{days}" in ports.columns
]
if not available_windows:
    st.error("No comparison columns found. Expected base_28/recent_28 or base_90/recent_90 in port_summary.csv.")
    st.stop()

# --------------------------- Header ---------------------------

st.markdown(
    """
    <div class="topbar">
      <div class="brand">
        <div class="brand-mark">⌁</div>
        <div>
          <div class="brand-name">PORT TRACKER<span style="color:#45f0df"> /</span></div>
          <div class="brand-sub">MARITIME INTELLIGENCE SYSTEM</div>
        </div>
      </div>
      <div class="top-right">
        <span class="live-dot"></span>DATA SYSTEM READY<br>
        HISTORICAL ACTIVITY MODE
      </div>
    </div>
    <div class="hero">
      <div class="eyebrow">GLOBAL MARITIME SITUATIONAL AWARENESS</div>
      <div class="hero-title">The world moves.<br><span>Track the signals.</span></div>
      <div class="hero-copy">
        A geographic view of port activity, traffic changes, and regional patterns.
        Explore where calls are rising or falling, then drill into individual port histories.
      </div>
      <span class="system-pill">◉ HISTORICAL DATA · NOT A LIVE VESSEL TRACKER</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------- Sidebar controls ---------------------------

with st.sidebar:
    st.markdown(
        "<div style='font: .68rem DM Mono,monospace;letter-spacing:.15em;color:#45f0df;'>CONTROL DECK</div>",
        unsafe_allow_html=True,
    )
    st.markdown("## Display settings")
    window = st.select_slider("Comparison period", options=available_windows, value=available_windows[-1], format_func=lambda n: f"{n} DAYS")
    ports[f"_base"] = num(ports, f"base_{window}")
    ports["_recent"] = num(ports, f"recent_{window}")
    ports["_change"] = ports["_recent"] - ports["_base"]
    ports["_pct"] = ports.apply(lambda r: r["_change"] / r["_base"] * 100 if r["_base"] else None, axis=1)

    max_base = max(100, int(ports["_base"].max()) if not ports.empty else 100)
    min_base = st.slider("Minimum baseline calls", 0, max_base, min(100, max_base), step=max(1, max_base // 100))
    all_continents = sorted(ports["_continent"].dropna().unique().tolist())
    selected_continents = st.multiselect("Filter continents", all_continents, default=all_continents)
    map_scope = st.selectbox("Map view", ["All selected ports", "Ports declining", "Ports growing"])
    marker_scale = st.select_slider("Marker size", options=["Compact", "Balanced", "Large"], value="Balanced")
    st.markdown("---")
    st.markdown(
        """
        <div style="border:1px solid rgba(105,185,218,.19);border-radius:10px;padding:12px;background:#0a1422;color:#7f9ab2;font-size:.76rem;line-height:1.65;">
          <span style="color:#45f0df;font-family:'DM Mono',monospace;">SYSTEM NOTE</span><br>
          Port markers show aggregated port-call changes, not individual ship positions.
          A decline or increase does not establish its cause.
        </div>
        """,
        unsafe_allow_html=True,
    )

filtered = ports[ports["_base"] >= min_base].copy()
if selected_continents:
    filtered = filtered[filtered["_continent"].isin(selected_continents)]

# --------------------------- KPI strip ---------------------------

total_base = filtered["_base"].sum()
total_recent = filtered["_recent"].sum()
delta = total_recent - total_base
pct = delta / total_base * 100 if total_base else None
down_count = int((filtered["_change"] < 0).sum())
up_count = int((filtered["_change"] > 0).sum())

st.markdown(
    f"""<div class="section-line">
      <div class="section-title">SYSTEM OVERVIEW <span style="color:#45f0df;">/</span> GLOBAL ACTIVITY</div>
      <div class="section-meta">WINDOW: {window} DAYS &nbsp; // &nbsp; FILTERED PORTS: {len(filtered):,}</div>
    </div>""",
    unsafe_allow_html=True,
)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ports monitored", f"{filtered[id_col].nunique():,}")
m2.metric("Recent port calls", f"{total_recent:,.0f}", delta=f"{delta:+,.0f} vs baseline")
m3.metric("Traffic change", f"{pct:+.1f}%" if pct is not None else "—", delta="vs baseline")
m4.metric("Ports declining", f"{down_count:,}", delta=f"{up_count:,} growing", delta_color="inverse")

# --------------------------- Main map: deliberately always visible ---------------------------

st.markdown(
    """<div class="section-line">
      <div class="section-title">GLOBAL PORT NETWORK <span style="color:#45f0df;">/</span> GEOSPATIAL VIEW</div>
      <div class="section-meta">INTERACTIVE MAP · PAN · ZOOM · HOVER</div>
    </div>""",
    unsafe_allow_html=True,
)

map_data = filtered.copy()
if lat_col and lon_col:
    map_data["_lat"] = pd.to_numeric(map_data[lat_col], errors="coerce")
    map_data["_lon"] = pd.to_numeric(map_data[lon_col], errors="coerce")
    map_data = map_data.dropna(subset=["_lat", "_lon"])
    map_data = map_data[map_data["_lat"].between(-90, 90) & map_data["_lon"].between(-180, 180)]
else:
    map_data = pd.DataFrame()

if not map_data.empty:
    if map_scope == "Ports declining":
        map_data = map_data[map_data["_change"] < 0]
    elif map_scope == "Ports growing":
        map_data = map_data[map_data["_change"] > 0]

if not map_data.empty:
    scale = {"Compact": 2500, "Balanced": 4500, "Large": 7000}[marker_scale]
    map_data["_radius"] = map_data["_base"].clip(lower=1).apply(lambda x: max(scale * .6, min(scale * 3.2, scale * .45 + x * .9)))
    map_data["_r"] = map_data["_change"].apply(lambda x: 255 if x < 0 else 69)
    map_data["_g"] = map_data["_change"].apply(lambda x: 111 if x < 0 else 240)
    map_data["_b"] = map_data["_change"].apply(lambda x: 131 if x < 0 else 223)

    # Two layers create a subtle halo under each port marker.
    halo = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[_lon, _lat]",
        get_fill_color="[_r, _g, _b, 42]",
        get_radius="_radius * 2.2",
        radius_min_pixels=7,
        radius_max_pixels=32,
        pickable=False,
    )
    points = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[_lon, _lat]",
        get_fill_color="[_r, _g, _b, 220]",
        get_line_color=[220, 246, 255, 190],
        get_radius="_radius",
        radius_min_pixels=4,
        radius_max_pixels=16,
        stroked=True,
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        latitude=float(map_data["_lat"].median()),
        longitude=float(map_data["_lon"].median()),
        zoom=0.35,
        min_zoom=0,
        max_zoom=12,
        pitch=0,
    )
    deck = pdk.Deck(
        layers=[halo, points],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": (
                "<div style='font-family:Arial;padding:9px;min-width:180px;'>"
                "<div style='font-size:12px;color:#45f0df;font-weight:bold;margin-bottom:5px;'>PORT INTELLIGENCE</div>"
                "<b>{_name}</b><br>{_country}<hr style='border-color:#284257'>"
                "Baseline calls: {_base}<br>Recent calls: {_recent}<br>"
                "Change: {_change}<br>Change %: {_pct}%</div>"
            ),
            "style": {"backgroundColor": "#081725", "color": "#eaf4ff", "border": "1px solid #286078"},
        },
    )
    st.markdown(
        """<div class="map-shell"><div class="map-caption">
        <div class="map-caption-title">◉ WORLD PORT ACTIVITY GRID</div>
        <div class="legend">
          <span><i class="dot" style="background:#45f0df"></i>GROWTH</span>
          <span><i class="dot" style="background:#ff6f83"></i>DECLINE</span>
          <span style="color:#7f9ab2">MARKER SIZE ≈ BASELINE ACTIVITY</span>
        </div></div></div>""",
        unsafe_allow_html=True,
    )
    st.pydeck_chart(deck, use_container_width=True, height=650)
    st.caption("Map points represent ports with coordinates in your summary file. This is aggregated historical activity, not real-time ship tracking.")
else:
    st.warning(
        "The map cannot draw any ports because valid coordinates were not found. "
        "Your port_summary.csv needs latitude/longitude columns (e.g. latitude and longitude) with numeric values."
    )

# --------------------------- Rankings and trends ---------------------------

st.markdown(
    """<div class="section-line">
      <div class="section-title">SIGNAL ANALYSIS <span style="color:#45f0df;">/</span> PORT PERFORMANCE</div>
      <div class="section-meta">RANKINGS · REGIONAL TRENDS · PORT HISTORY</div>
    </div>""",
    unsafe_allow_html=True,
)

tab_rank, tab_trend, tab_explorer = st.tabs(["▤  Port rankings", "⌁  Regional trends", "⌖  Port history"])

with tab_rank:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="panel-title">LARGEST DECLINES</div><div class="panel-sub">Largest absolute reductions in port calls for the selected period.</div>', unsafe_allow_html=True)
        drops = filtered.sort_values("_change").head(10)
        if drops.empty:
            st.info("No ports match the selected filters.")
        else:
            table = drops[["_name", "_country", "_base", "_recent", "_change", "_pct"]].copy()
            table.columns = ["Port", "Country", "Baseline", "Recent", "Change", "Change %"]
            table["Change %"] = table["Change %"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
            st.dataframe(table.style.format({"Baseline": "{:,.0f}", "Recent": "{:,.0f}", "Change": "{:+,.0f}"}), use_container_width=True, hide_index=True)
    with c2:
        st.markdown('<div class="panel-title">LARGEST GAINS</div><div class="panel-sub">Largest absolute increases in port calls for the selected period.</div>', unsafe_allow_html=True)
        gains = filtered.sort_values("_change", ascending=False).head(10)
        if gains.empty:
            st.info("No ports match the selected filters.")
        else:
            table = gains[["_name", "_country", "_base", "_recent", "_change", "_pct"]].copy()
            table.columns = ["Port", "Country", "Baseline", "Recent", "Change", "Change %"]
            table["Change %"] = table["Change %"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
            st.dataframe(table.style.format({"Baseline": "{:,.0f}", "Recent": "{:,.0f}", "Change": "{:+,.0f}"}), use_container_width=True, hide_index=True)

    st.markdown("#### Full ranking table")
    order = st.selectbox("Sort table", ["Largest decline", "Largest gain", "Largest decline (%)", "Largest gain (%)"])
    if order == "Largest decline":
        ranked = filtered.sort_values("_change")
    elif order == "Largest gain":
        ranked = filtered.sort_values("_change", ascending=False)
    elif order == "Largest decline (%)":
        ranked = filtered.sort_values("_pct", na_position="last")
    else:
        ranked = filtered.sort_values("_pct", ascending=False, na_position="last")
    all_table = ranked[["_name", "_country", "_continent", "_base", "_recent", "_change", "_pct"]].copy()
    all_table.columns = ["Port", "Country", "Continent", "Baseline calls", "Recent calls", "Change", "Change %"]
    all_table["Change %"] = all_table["Change %"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    st.dataframe(all_table.style.format({"Baseline calls": "{:,.0f}", "Recent calls": "{:,.0f}", "Change": "{:+,.0f}"}), use_container_width=True, hide_index=True, height=450)
    st.download_button("↓ Export ranking CSV", all_table.to_csv(index=False).encode("utf-8"), file_name=f"port_tracker_{window}d_rankings.csv", mime="text/csv")

with tab_trend:
    st.markdown('<div class="panel-title">REGIONAL ACTIVITY INDEX</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Monthly port calls per day indexed against the average of baseline months up to February 2026.</div>', unsafe_allow_html=True)
    if monthly.empty:
        st.info("country_monthly.csv was not found. Place it in the same data folder as port_summary.csv to enable this chart.")
    else:
        month_col = find_col(monthly, ["month_start", "month", "date"])
        calls_col = find_col(monthly, ["portcalls", "port_calls", "calls", "total_portcalls"])
        iso_m_col = find_col(monthly, ["iso3", "country_iso3", "iso_a3"])
        cont_m_col = find_col(monthly, ["continent"])
        if not month_col or not calls_col:
            st.warning("The monthly file needs a date/month field and a port-call total field.")
        else:
            mv = monthly.copy()
            mv["_month"] = pd.to_datetime(mv[month_col], errors="coerce")
            mv["_calls"] = pd.to_numeric(mv[calls_col], errors="coerce")
            mv = mv.dropna(subset=["_month", "_calls"])
            mv["_iso"] = mv[iso_m_col].astype(str).str.upper() if iso_m_col else ""
            if cont_m_col and selected_continents:
                mv = mv[mv[cont_m_col].fillna("Unknown").isin(selected_continents)]
            gulf = mv[mv["_iso"].isin(GULF_COUNTRIES)].groupby("_month")["_calls"].sum()
            world = mv.groupby("_month")["_calls"].sum()
            rest = (world - gulf).clip(lower=0)
            tr = pd.DataFrame({"month": world.index, "Gulf": gulf.reindex(world.index, fill_value=0).values, "Rest": rest.values}).sort_values("month")
            tr["Gulf calls/day"] = tr["Gulf"] / tr["month"].dt.days_in_month
            tr["Rest calls/day"] = tr["Rest"] / tr["month"].dt.days_in_month
            base_mask = tr["month"] <= pd.Timestamp("2026-02-28")
            gb, rb = tr.loc[base_mask, "Gulf calls/day"].mean(), tr.loc[base_mask, "Rest calls/day"].mean()
            tr["Gulf region"] = tr["Gulf calls/day"] / gb * 100 if gb else None
            tr["Rest of world"] = tr["Rest calls/day"] / rb * 100 if rb else None
            st.line_chart(tr.set_index("month")[["Gulf region", "Rest of world"]], use_container_width=True, height=390)
            st.caption("Index 100 = average daily port calls during the baseline months. These are descriptive trends, not causal findings.")
            with st.expander("Inspect monthly values"):
                st.dataframe(tr[["month", "Gulf calls/day", "Rest calls/day", "Gulf region", "Rest of world"]], use_container_width=True, hide_index=True)

with tab_explorer:
    st.markdown('<div class="panel-title">INDIVIDUAL PORT TRACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-sub">Fetch daily port-call history from the ArcGIS service for a selected port.</div>', unsafe_allow_html=True)
    if filtered.empty:
        st.info("No ports match the selected filters.")
    else:
        choices = filtered.copy()
        choices["_choice"] = choices.apply(lambda r: f"{r['_name']} — {r['_country']} ({r[id_col]})", axis=1)
        choice = st.selectbox("Select port", choices["_choice"].tolist())
        row = choices.loc[choices["_choice"] == choice].iloc[0]
        since = st.date_input("Start date", value=date.today() - timedelta(days=400), max_value=date.today())
        if st.button("Load daily history", type="primary"):
            with st.spinner("Retrieving port history…"):
                hist = port_daily(str(row[id_col]), since.isoformat())
            if hist.empty:
                st.warning("No history returned. Check the port ID and ArcGIS response.")
            else:
                hist = hist.dropna(subset=["portcalls"]).copy()
                hist["7-day average"] = hist["portcalls"].rolling(7, min_periods=1).mean()
                st.session_state["pt_hist"] = hist
                st.session_state["pt_hist_name"] = choice
        if "pt_hist" in st.session_state:
            hist = st.session_state["pt_hist"]
            st.markdown(f"#### {st.session_state.get('pt_hist_name', choice)}")
            a, b, c = st.columns(3)
            a.metric("Days returned", f"{len(hist):,}")
            b.metric("Mean calls / day", f"{hist['portcalls'].mean():,.1f}")
            last7 = hist.tail(7)["portcalls"].mean()
            prior7 = hist.tail(14).head(7)["portcalls"].mean() if len(hist) >= 14 else None
            c.metric("Latest 7-day shift", f"{last7-prior7:+.1f}" if prior7 is not None else "—")
            st.line_chart(hist.set_index("date")[["portcalls", "7-day average"]], use_container_width=True, height=360)
            st.dataframe(hist.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
            st.download_button("↓ Export daily history", hist.to_csv(index=False).encode("utf-8"), file_name="port_tracker_daily_history.csv", mime="text/csv")

# --------------------------- Footer ---------------------------

source = info.get("source", "ArcGIS daily port data / supporting maritime datasets")
updated = info.get("updated_at", info.get("last_updated", "Not specified"))
st.markdown(
    f"""<div class="footer">
    PORT TRACKER // MARITIME INTELLIGENCE<br>
    DATA SOURCE: {source}<br>
    DATASET UPDATE METADATA: {updated}<br>
    SYSTEM DISCLAIMER: Historical port-call analytics only. No live vessel positions, and no causal claims are inferred from traffic changes.
    </div>""",
    unsafe_allow_html=True,
)
