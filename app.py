import json
import os
from datetime import date, timedelta

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# ============================================================
# PORT TRACKER — Streamlit dashboard
# Keep your existing data files in:
#   data/  OR  app_data/data/
# ============================================================

st.set_page_config(
    page_title="Port Tracker | Maritime Intelligence",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DAILY_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/"
    "arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
)

GULF_COUNTRIES = ["ARE", "QAT", "IRQ", "IRN", "KWT", "BHR", "SAU", "OMN"]
TYPES = ["container", "dry_bulk", "general_cargo", "roro", "tanker"]

DATA_DIR = "data" if os.path.exists("data/port_summary.csv") else "app_data/data"


# --------------------------- Styling ---------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
  --bg: #06111f;
  --panel: #0b1d2d;
  --panel2: #10263a;
  --border: rgba(143, 169, 190, .16);
  --cyan: #58e1d5;
  --blue: #76b8ff;
  --text: #f2f7fc;
  --muted: #91a9bd;
  --red: #ff8172;
  --green: #58e1b2;
}

.stApp {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(38, 115, 154, .18), transparent 36%),
    radial-gradient(ellipse at 92% 12%, rgba(50, 91, 161, .15), transparent 32%),
    var(--bg);
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
  background: rgba(6, 17, 31, .75);
  backdrop-filter: blur(14px);
}
.block-container {
  max-width: 1600px;
  padding-top: 2rem;
  padding-bottom: 3rem;
}
h1, h2, h3, h4 {
  font-family: 'Space Grotesk', sans-serif !important;
  letter-spacing: -.035em;
  color: var(--text) !important;
}
p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
  color: var(--text);
}
[data-testid="stCaptionContainer"] { color: var(--muted) !important; }

@keyframes riseIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes accentMove {
  0% { transform: translateX(-110%); }
  100% { transform: translateX(350%); }
}
@keyframes softGlow {
  0%, 100% { box-shadow: 0 8px 28px rgba(0,0,0,.12); }
  50% { box-shadow: 0 12px 34px rgba(88,225,213,.08); }
}

.hero {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(118,184,255,.22);
  border-radius: 24px;
  padding: 30px 34px 27px;
  margin: 4px 0 24px;
  background:
    radial-gradient(ellipse at 90% 0%, rgba(88,225,213,.14), transparent 38%),
    linear-gradient(125deg, rgba(15,39,59,.98), rgba(8,25,42,.96));
  animation: riseIn .65s ease both;
}
.hero:after {
  content: "";
  position: absolute;
  left: 0;
  bottom: 0;
  width: 28%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--cyan), transparent);
  animation: accentMove 7s ease-in-out infinite alternate;
}
.eyebrow {
  color: var(--cyan);
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .16em;
  text-transform: uppercase;
  margin-bottom: 13px;
}
.hero-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(2rem, 4.1vw, 3.5rem);
  font-weight: 700;
  line-height: 1.04;
  letter-spacing: -.055em;
  color: var(--text);
  margin-bottom: 15px;
}
.hero-copy {
  max-width: 720px;
  color: #a8bfd1;
  font-size: 1rem;
  line-height: 1.75;
}
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(88,225,213,.24);
  background: rgba(88,225,213,.07);
  color: #9af4e9;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: .7rem;
  letter-spacing: .08em;
  font-weight: 700;
}

.section-heading {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.18rem;
  font-weight: 700;
  letter-spacing: -.025em;
  margin: 15px 0 3px;
  color: var(--text);
}
.section-subtitle {
  color: var(--muted);
  font-size: .84rem;
  margin-bottom: 14px;
}

[data-testid="stMetric"] {
  background: linear-gradient(145deg, rgba(16,38,58,.94), rgba(9,27,44,.92));
  border: 1px solid var(--border);
  border-radius: 17px;
  padding: 18px 19px;
  min-height: 122px;
  animation: riseIn .55s ease both, softGlow 5s ease-in-out infinite;
  transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
}
[data-testid="stMetric"]:hover {
  transform: translateY(-4px);
  border-color: rgba(88,225,213,.42);
  box-shadow: 0 14px 35px rgba(0,0,0,.2);
}
[data-testid="stMetricLabel"] {
  color: var(--muted) !important;
  font-size: .82rem !important;
}
[data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-family: 'Space Grotesk', sans-serif;
  font-size: clamp(1.45rem, 2.2vw, 2rem) !important;
  font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-size: .8rem !important; }

.stTabs [data-baseweb="tab-list"] {
  gap: 7px;
  border-bottom: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
  background: transparent;
  border-radius: 10px 10px 0 0;
  color: var(--muted);
  padding: 12px 17px;
  transition: background .2s ease, color .2s ease;
}
.stTabs [aria-selected="true"] {
  color: var(--cyan) !important;
  background: rgba(88,225,213,.08) !important;
}
.stButton > button, .stDownloadButton > button {
  border: 1px solid rgba(88,225,213,.32);
  border-radius: 11px;
  color: var(--text);
  background: linear-gradient(135deg, rgba(88,225,213,.12), rgba(118,184,255,.1));
  transition: transform .2s ease, border-color .2s ease, background .2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  transform: translateY(-2px);
  border-color: var(--cyan);
  color: white;
  background: rgba(88,225,213,.16);
}
[data-baseweb="select"] > div, [data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
  background: #0c2032;
  border-color: var(--border);
  border-radius: 10px;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--border);
  border-radius: 13px;
  overflow: hidden;
}
hr { border-color: var(--border); }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #091a2a, #071522);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--text) !important;
}
.sidebar-note {
  color: var(--muted);
  font-size: .8rem;
  line-height: 1.6;
  padding: 12px 13px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(16,38,58,.55);
}
.info-card {
  border: 1px solid var(--border);
  border-radius: 15px;
  padding: 17px 18px;
  background: linear-gradient(145deg, rgba(16,38,58,.7), rgba(9,27,44,.7));
  height: 100%;
}
.info-label {
  color: var(--muted);
  font-size: .75rem;
  text-transform: uppercase;
  letter-spacing: .1em;
  font-weight: 700;
  margin-bottom: 8px;
}
.info-value {
  color: var(--text);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.3rem;
  font-weight: 700;
}
.footer {
  color: var(--muted);
  font-size: .78rem;
  border-top: 1px solid var(--border);
  margin-top: 32px;
  padding-top: 16px;
  line-height: 1.7;
}
@media (max-width: 700px) {
  .block-container { padding-top: 1rem; }
  .hero { padding: 23px 20px; border-radius: 18px; }
  .hero-title { font-size: 2.1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
  }
}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------- Data loading ---------------------------

@st.cache_data(show_spinner=False)
def load_data(data_dir: str):
    summary_path = os.path.join(data_dir, "port_summary.csv")
    monthly_path = os.path.join(data_dir, "country_monthly.csv")
    info_path = os.path.join(data_dir, "data_info.json")

    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Could not find {summary_path}")

    summary = pd.read_csv(summary_path)
    monthly = pd.read_csv(monthly_path) if os.path.exists(monthly_path) else pd.DataFrame()
    info = {}

    if os.path.exists(info_path):
        with open(info_path, "r", encoding="utf-8") as file:
            info = json.load(file)

    if "continent" in summary.columns:
        summary["continent"] = summary["continent"].fillna("Unknown")
    if "month_start" in monthly.columns:
        monthly["month_start"] = pd.to_datetime(monthly["month_start"], errors="coerce")
    if "date" in summary.columns:
        summary["date"] = pd.to_datetime(summary["date"], errors="coerce")

    return summary, monthly, info


@st.cache_data(ttl=3600, show_spinner=False)
def port_daily(portid: str, since: str):
    """Fetch daily port-call history from the ArcGIS feature service."""
    rows = []
    offset = 0
    page_size = 1000

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
            # ArcGIS date fields are often Unix timestamps in milliseconds.
            if isinstance(raw_date, (int, float)):
                parsed_date = pd.to_datetime(raw_date, unit="ms", errors="coerce")
            else:
                parsed_date = pd.to_datetime(raw_date, errors="coerce")
            rows.append(
                {
                    "date": parsed_date,
                    "portcalls": pd.to_numeric(attrs.get("portcalls"), errors="coerce"),
                }
            )

        if len(features) < page_size:
            break
        offset += page_size

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.dropna(subset=["date"]).sort_values("date")
        result["date"] = pd.to_datetime(result["date"]).dt.tz_localize(None)
    return result


def first_existing_column(frame, choices):
    for column in choices:
        if column in frame.columns:
            return column
    return None


def numeric_series(frame, column):
    if column is None:
        return pd.Series(0, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


def format_number(value):
    if pd.isna(value):
        return "—"
    return f"{value:,.0f}"


def clean_label(value):
    if pd.isna(value) or str(value).strip() == "":
        return "Unknown"
    return str(value)


# --------------------------- Load + validate ---------------------------

try:
    ports, monthly, data_info = load_data(DATA_DIR)
except Exception as exc:
    st.error(f"Could not load the Port Tracker data: {exc}")
    st.info(
        "Make sure `port_summary.csv` is in either `data/` or `app_data/data/`. "
        "The monthly file and data_info.json are optional."
    )
    st.stop()

if ports.empty:
    st.warning("Your port summary file is empty. Check the data preparation notebook.")
    st.stop()

port_id_col = first_existing_column(ports, ["portid", "port_id", "id"])
port_name_col = first_existing_column(ports, ["port_name", "name", "port", "portname"])
country_col = first_existing_column(ports, ["country", "country_name"])
iso_col = first_existing_column(ports, ["iso3", "country_iso3", "iso_a3"])
continent_col = first_existing_column(ports, ["continent"])
lat_col = first_existing_column(ports, ["latitude", "lat", "y"])
lon_col = first_existing_column(ports, ["longitude", "lon", "lng", "x"])

base_col = first_existing_column(ports, ["base_90", "base_28"])
recent_col = first_existing_column(ports, ["recent_90", "recent_28"])

if port_id_col is None:
    st.error("The port summary needs a port ID column such as `portid` or `port_id`.")
    st.stop()

if base_col is None or recent_col is None:
    st.error(
        "The port summary needs baseline and recent comparison columns "
        "(for example `base_90` and `recent_90`)."
    )
    st.stop()

ports[port_id_col] = ports[port_id_col].astype(str)
ports["_port_name"] = ports[port_name_col].map(clean_label) if port_name_col else ports[port_id_col]
ports["_country"] = ports[country_col].map(clean_label) if country_col else "Unknown"
ports["_continent"] = ports[continent_col].map(clean_label) if continent_col else "Unknown"
ports["_iso3"] = ports[iso_col].astype(str).str.upper() if iso_col else ""
ports["_base"] = numeric_series(ports, base_col)
ports["_recent"] = numeric_series(ports, recent_col)
ports["_change"] = ports["_recent"] - ports["_base"]
ports["_pct_change"] = ports.apply(
    lambda row: (row["_change"] / row["_base"] * 100) if row["_base"] else None,
    axis=1,
)

# --------------------------- Sidebar ---------------------------

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 9px 0 19px;">
          <div style="font-size:.72rem;letter-spacing:.16em;color:#58e1d5;font-weight:700;">
            MARITIME INTELLIGENCE
          </div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:1.65rem;font-weight:700;color:#f2f7fc;">
            PORT TRACKER<span style="color:#58e1d5;">.</span>
          </div>
          <div style="color:#91a9bd;font-size:.82rem;">Global port activity monitor</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("### Dashboard controls")
    window = st.radio(
        "Comparison window",
        options=[28, 90],
        format_func=lambda value: f"Last {value} days",
        index=1,
        horizontal=True,
    )
    minimum_baseline = st.slider(
        "Minimum baseline port calls",
        min_value=0,
        max_value=int(max(100, ports["_base"].max() if not ports.empty else 100)),
        value=min(100, int(max(100, ports["_base"].max() if not ports.empty else 100))),
        step=max(1, int(max(100, ports["_base"].max() if not ports.empty else 100) / 100)),
        help="Hide ports with very little activity in the baseline period.",
    )

    if continent_col:
        continents = sorted(ports["_continent"].dropna().unique().tolist())
        selected_continents = st.multiselect(
            "Continents",
            options=continents,
            default=continents,
        )
    else:
        selected_continents = []

    st.markdown(
        """
        <div class="sidebar-note">
          <strong style="color:#f2f7fc;">How to read this dashboard</strong><br>
          Compare recent port calls with a prior baseline. Changes show activity shifts,
          not the cause of those shifts.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.caption("PORT TRACKER · EXPLORATORY ANALYTICS")


# Pick matching columns for the selected comparison window.
base_selected = f"base_{window}"
recent_selected = f"recent_{window}"
if base_selected in ports.columns and recent_selected in ports.columns:
    ports["_base"] = numeric_series(ports, base_selected)
    ports["_recent"] = numeric_series(ports, recent_selected)
    ports["_change"] = ports["_recent"] - ports["_base"]
    ports["_pct_change"] = ports.apply(
        lambda row: (row["_change"] / row["_base"] * 100) if row["_base"] else None,
        axis=1,
    )

filtered = ports[ports["_base"] >= minimum_baseline].copy()
if selected_continents:
    filtered = filtered[filtered["_continent"].isin(selected_continents)]

# --------------------------- Hero ---------------------------

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">GLOBAL PORT ACTIVITY / INTELLIGENCE</div>
      <div class="hero-title">
        See the movement.<br>
        <span style="color:#58e1d5;">Understand the change.</span>
      </div>
      <div class="hero-copy">
        Explore port activity, compare recent traffic with a baseline,
        and uncover patterns across global maritime networks.
        Built on historical data. Designed for clearer decisions.
      </div>
      <br>
      <span class="status-pill">● HISTORICAL PORT-CALL DATA</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="section-heading">Global activity snapshot</div>'
    f'<div class="section-subtitle">Comparing the latest {window} days against the baseline period · based on current filters</div>',
    unsafe_allow_html=True,
)

# --------------------------- KPIs ---------------------------

total_baseline = filtered["_base"].sum()
total_recent = filtered["_recent"].sum()
total_change = total_recent - total_baseline
total_pct = (total_change / total_baseline * 100) if total_baseline else None
ports_down = int((filtered["_change"] < 0).sum())
ports_up = int((filtered["_change"] > 0).sum())
port_count = int(filtered[port_id_col].nunique())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Ports in view", format_number(port_count))
k2.metric("Recent port calls", format_number(total_recent), delta=f"{total_change:+,.0f} vs baseline")
k3.metric(
    "Overall change",
    f"{total_pct:+.1f}%" if total_pct is not None else "—",
    delta="vs baseline",
    delta_color="normal",
)
k4.metric("Ports declining", format_number(ports_down), delta=f"{ports_up:,} increasing", delta_color="inverse")

st.markdown("")

# --------------------------- Tabs ---------------------------

tab_overview, tab_rankings, tab_regions, tab_port = st.tabs(
    ["◈  Overview", "↕  Port rankings", "◎  Regional trends", "⌁  Port explorer"]
)

with tab_overview:
    left, right = st.columns([1.55, 1], gap="large")

    with left:
        st.markdown('<div class="section-heading">Port activity map</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Hover over a point for details. Teal indicates growth; coral indicates decline.</div>',
            unsafe_allow_html=True,
        )

        map_data = filtered.copy()
        if lat_col and lon_col:
            map_data["_lat"] = pd.to_numeric(map_data[lat_col], errors="coerce")
            map_data["_lon"] = pd.to_numeric(map_data[lon_col], errors="coerce")
            map_data = map_data.dropna(subset=["_lat", "_lon"])
            map_data = map_data[
                map_data["_lat"].between(-90, 90) & map_data["_lon"].between(-180, 180)
            ]
            if not map_data.empty:
                map_data["_color_r"] = map_data["_change"].apply(lambda x: 255 if x < 0 else 88)
                map_data["_color_g"] = map_data["_change"].apply(lambda x: 129 if x < 0 else 225)
                map_data["_color_b"] = map_data["_change"].apply(lambda x: 114 if x < 0 else 213)
                map_data["_radius"] = map_data["_base"].clip(lower=1).apply(
                    lambda x: max(3500, min(14000, 2500 + x * 3))
                )
                map_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_data,
                    get_position="[_lon, _lat]",
                    get_fill_color="[_color_r, _color_g, _color_b, 190]",
                    get_line_color=[225, 242, 255, 150],
                    get_radius="_radius",
                    radius_min_pixels=3,
                    radius_max_pixels=18,
                    pickable=True,
                    auto_highlight=True,
                    stroked=True,
                    line_width_min_pixels=1,
                )
                view_state = pdk.ViewState(
                    latitude=float(map_data["_lat"].median()),
                    longitude=float(map_data["_lon"].median()),
                    zoom=0.4,
                    min_zoom=0,
                    max_zoom=10,
                )
                deck = pdk.Deck(
                    layers=[map_layer],
                    initial_view_state=view_state,
                    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                    tooltip={
                        "html": (
                            "<div style='font-family:Arial;padding:8px;'>"
                            "<b>{_port_name}</b><br/>"
                            "{_country}<br/>"
                            "Baseline: {_base}<br/>"
                            "Recent: {_recent}<br/>"
                            "Change: {_change}"
                            "</div>"
                        ),
                        "style": {
                            "backgroundColor": "#0b1d2d",
                            "color": "#f2f7fc",
                            "border": "1px solid #24445d",
                        },
                    },
                )
                st.pydeck_chart(deck, use_container_width=True, height=500)
            else:
                st.info("No valid latitude/longitude values are available for the selected ports.")
        else:
            st.info(
                "The map needs latitude and longitude columns in port_summary.csv "
                "(for example `latitude` and `longitude`)."
            )

    with right:
        st.markdown('<div class="section-heading">Biggest declines</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Ports with the largest absolute drops in calls.</div>',
            unsafe_allow_html=True,
        )
        drops = filtered.sort_values("_change", ascending=True).head(7)
        if drops.empty:
            st.info("No ports match the current filters.")
        else:
            show = drops[["_port_name", "_country", "_base", "_recent", "_change"]].copy()
            show.columns = ["Port", "Country", "Baseline", "Recent", "Change"]
            st.dataframe(
                show.style.format({"Baseline": "{:,.0f}", "Recent": "{:,.0f}", "Change": "{:+,.0f}"}),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown('<div class="section-heading">Biggest gains</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Ports with the largest absolute increases in calls.</div>',
            unsafe_allow_html=True,
        )
        gains = filtered.sort_values("_change", ascending=False).head(7)
        if gains.empty:
            st.info("No ports match the current filters.")
        else:
            show = gains[["_port_name", "_country", "_base", "_recent", "_change"]].copy()
            show.columns = ["Port", "Country", "Baseline", "Recent", "Change"]
            st.dataframe(
                show.style.format({"Baseline": "{:,.0f}", "Recent": "{:,.0f}", "Change": "{:+,.0f}"}),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    st.markdown('<div class="section-heading">What the numbers say</div>', unsafe_allow_html=True)
    if total_pct is None:
        interpretation = "There is not enough baseline activity to calculate an overall percentage change."
    elif total_change > 0:
        interpretation = (
            f"Across the currently selected ports, recent calls are up by {abs(total_pct):.1f}% "
            "compared with the baseline. This is a descriptive change, not an explanation of why it happened."
        )
    elif total_change < 0:
        interpretation = (
            f"Across the currently selected ports, recent calls are down by {abs(total_pct):.1f}% "
            "compared with the baseline. Check the port-level and regional views before drawing conclusions."
        )
    else:
        interpretation = "Total recent calls are equal to the baseline for the selected ports."
    st.markdown(
        f"<div class='info-card'><div class='info-label'>Snapshot summary</div>"
        f"<div style='color:#c0d1df;line-height:1.7'>{interpretation}</div></div>",
        unsafe_allow_html=True,
    )

with tab_rankings:
    st.markdown('<div class="section-heading">Port performance rankings</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Sort and compare ports by absolute change or percentage change. Very small baselines are filtered out above.</div>',
        unsafe_allow_html=True,
    )

    sort_choice = st.selectbox(
        "Rank ports by",
        options=[
            "Largest decline (calls)",
            "Largest gain (calls)",
            "Largest decline (%)",
            "Largest gain (%)",
        ],
    )
    if sort_choice == "Largest decline (calls)":
        ranked = filtered.sort_values("_change", ascending=True)
    elif sort_choice == "Largest gain (calls)":
        ranked = filtered.sort_values("_change", ascending=False)
    elif sort_choice == "Largest decline (%)":
        ranked = filtered.sort_values("_pct_change", ascending=True, na_position="last")
    else:
        ranked = filtered.sort_values("_pct_change", ascending=False, na_position="last")

    ranking = ranked[["_port_name", "_country", "_continent", "_base", "_recent", "_change", "_pct_change"]].copy()
    ranking.columns = ["Port", "Country", "Continent", "Baseline calls", "Recent calls", "Change", "Change (%)"]
    ranking["Change (%)"] = ranking["Change (%)"].map(lambda x: f"{x:+.1f}%" if pd.notna(x) else "—")
    st.dataframe(
        ranking.style.format(
            {
                "Baseline calls": "{:,.0f}",
                "Recent calls": "{:,.0f}",
                "Change": "{:+,.0f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
        height=520,
    )
    csv = ranking.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered rankings as CSV",
        data=csv,
        file_name=f"port_tracker_rankings_{window}d.csv",
        mime="text/csv",
    )

with tab_regions:
    st.markdown('<div class="section-heading">Regional activity over time</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Monthly port calls per day, indexed to the average of the baseline months. This helps compare trends when regions differ in size.</div>',
        unsafe_allow_html=True,
    )

    if monthly.empty:
        st.info("No country_monthly.csv file was found. Add it to your data folder to enable regional trends.")
    else:
        date_month_col = first_existing_column(monthly, ["month_start", "month", "date"])
        calls_col = first_existing_column(monthly, ["portcalls", "port_calls", "calls", "total_portcalls"])
        monthly_iso_col = first_existing_column(monthly, ["iso3", "country_iso3", "iso_a3"])
        monthly_country_col = first_existing_column(monthly, ["country", "country_name"])
        monthly_continent_col = first_existing_column(monthly, ["continent"])

        if date_month_col is None or calls_col is None:
            st.warning("The monthly file needs a month/date column and a port-calls column.")
        else:
            monthly_view = monthly.copy()
            monthly_view["_month"] = pd.to_datetime(monthly_view[date_month_col], errors="coerce")
            monthly_view["_calls"] = pd.to_numeric(monthly_view[calls_col], errors="coerce")
            monthly_view = monthly_view.dropna(subset=["_month", "_calls"])
            if monthly_iso_col:
                monthly_view["_iso3"] = monthly_view[monthly_iso_col].astype(str).str.upper()
            else:
                monthly_view["_iso3"] = ""
            if monthly_country_col:
                monthly_view["_country"] = monthly_view[monthly_country_col].map(clean_label)
            else:
                monthly_view["_country"] = "Unknown"

            if monthly_continent_col and selected_continents:
                monthly_view = monthly_view[
                    monthly_view[monthly_continent_col].fillna("Unknown").isin(selected_continents)
                ]

            gulf_monthly = monthly_view[monthly_view["_iso3"].isin(GULF_COUNTRIES)].groupby("_month")["_calls"].sum()
            world_monthly = monthly_view.groupby("_month")["_calls"].sum()
            rest_monthly = (world_monthly - gulf_monthly).clip(lower=0)

            trend = pd.DataFrame(
                {
                    "month": world_monthly.index,
                    "Gulf region": gulf_monthly.reindex(world_monthly.index, fill_value=0).values,
                    "Rest of world": rest_monthly.values,
                }
            ).sort_values("month")
            trend["Gulf calls/day"] = trend["Gulf region"] / trend["month"].dt.days_in_month
            trend["Rest of world calls/day"] = trend["Rest of world"] / trend["month"].dt.days_in_month

            # Baseline is the mean daily traffic through February 2026, matching the notebook's exploratory baseline.
            baseline_mask = trend["month"] <= pd.Timestamp("2026-02-28")
            gulf_base = trend.loc[baseline_mask, "Gulf calls/day"].mean()
            rest_base = trend.loc[baseline_mask, "Rest of world calls/day"].mean()
            trend["Gulf index"] = trend["Gulf calls/day"] / gulf_base * 100 if gulf_base else None
            trend["Rest of world index"] = trend["Rest of world calls/day"] / rest_base * 100 if rest_base else None

            chart_view = trend[["month", "Gulf index", "Rest of world index"]].melt(
                id_vars="month", var_name="Region", value_name="Index (baseline = 100)"
            )
            chart_view["Region"] = chart_view["Region"].replace(
                {"Gulf index": "Gulf region", "Rest of world index": "Rest of world"}
            )
            st.line_chart(
                chart_view.pivot(index="month", columns="Region", values="Index (baseline = 100)"),
                use_container_width=True,
            )
            st.caption("Index 100 represents each region's average daily calls during the baseline months up to February 2026.")

            with st.expander("View regional monthly data"):
                st.dataframe(
                    trend[["month", "Gulf calls/day", "Rest of world calls/day", "Gulf index", "Rest of world index"]]
                    .rename(columns={"month": "Month"}),
                    use_container_width=True,
                    hide_index=True,
                )

with tab_port:
    st.markdown('<div class="section-heading">Explore an individual port</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Load daily historical calls for a selected port directly from the ArcGIS service.</div>',
        unsafe_allow_html=True,
    )

    options = filtered.sort_values("_port_name")
    if options.empty:
        st.info("No ports match the current filters. Adjust the sidebar controls.")
    else:
        options["_selector"] = options.apply(
            lambda row: f"{row['_port_name']} — {row['_country']} ({row[port_id_col]})",
            axis=1,
        )
        selected_label = st.selectbox("Choose a port", options=options["_selector"].tolist())
        selected_row = options.loc[options["_selector"] == selected_label].iloc[0]
        selected_port_id = str(selected_row[port_id_col])

        default_since = date.today() - timedelta(days=400)
        since_date = st.date_input(
            "History start date",
            value=default_since,
            max_value=date.today(),
        )

        if st.button("Load port history", type="primary"):
            with st.spinner("Fetching daily port-call history…"):
                history = port_daily(selected_port_id, since_date.isoformat())
            if history.empty:
                st.warning(
                    "No daily history was returned. Check the port ID field and the ArcGIS service response."
                )
            else:
                history = history.dropna(subset=["portcalls"]).copy()
                history["7-day average"] = history["portcalls"].rolling(7, min_periods=1).mean()
                st.session_state["port_tracker_history"] = history
                st.session_state["port_tracker_history_name"] = selected_label

        if "port_tracker_history" in st.session_state:
            history = st.session_state["port_tracker_history"]
            history_name = st.session_state.get("port_tracker_history_name", selected_label)
            st.markdown(f"#### {history_name}")
            if not history.empty:
                last_7 = history.tail(7)["portcalls"].mean()
                previous_7 = history.tail(14).head(7)["portcalls"].mean() if len(history) >= 14 else None
                change_7 = last_7 - previous_7 if previous_7 is not None else None
                h1, h2, h3 = st.columns(3)
                h1.metric("Days returned", format_number(len(history)))
                h2.metric("Average calls/day", f"{history['portcalls'].mean():,.1f}")
                h3.metric(
                    "Last 7 days vs prior 7",
                    f"{change_7:+.1f}" if change_7 is not None else "—",
                    help="Difference between the mean daily calls in the latest and previous 7-day periods.",
                )
                chart = history.set_index("date")[["portcalls", "7-day average"]]
                st.line_chart(chart, use_container_width=True)
                st.dataframe(history.sort_values("date", ascending=False), use_container_width=True, hide_index=True)
                st.download_button(
                    "Download port history as CSV",
                    data=history.to_csv(index=False).encode("utf-8"),
                    file_name="port_tracker_daily_history.csv",
                    mime="text/csv",
                )


# --------------------------- Footer ---------------------------

source_text = data_info.get("source", "ArcGIS daily port data / supporting maritime datasets")
updated_text = data_info.get("updated_at", data_info.get("last_updated", "Not specified in data_info.json"))

st.markdown(
    f"""
    <div class="footer">
      <strong style="color:#dbe8f2;">PORT TRACKER</strong> · Maritime activity intelligence<br>
      Data source: {source_text}<br>
      Dataset update metadata: {updated_text}<br>
      <span>Interpretation note: changes are descriptive. They do not, on their own, establish causes or predict future traffic.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
