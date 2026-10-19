import json
import os
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
import altair as alt

# --- API & CONSTANTS ---
DAILY = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
TYPES = ["container", "dry_bulk", "general_cargo", "roro", "tanker"]
GULF = ["ARE", "QAT", "IRQ", "IRN", "KWT", "BHR", "SAU", "OMN"]

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NEXUS | Maritime Port Intelligence",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
    /* Dark Theme Base Overrides */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Hide Streamlit Header Elements */
    header[data-testid="stHeader"] { background: rgba(11, 14, 20, 0.8); }
    
    /* Glassmorphism Cards */
    div.metric-card {
        background: rgba(22, 27, 38, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div.metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    
    /* Metric Typography */
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-sub {
        font-size: 0.85rem;
        font-weight: 500;
        margin-top: 6px;
    }
    .text-positive { color: #10B981; }
    .text-negative { color: #EF4444; }
    .text-neutral { color: #38BDF8; }

    /* Custom Headers */
    h1, h2, h3 {
        color: #F8FAFC !important;
        font-weight: 700 !important;
    }
    .section-header {
        border-left: 4px solid #38BDF8;
        padding-left: 12px;
        margin: 28px 0 16px 0;
        font-size: 1.3rem;
        letter-spacing: -0.02em;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111622;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)


DATA_DIR = "data" if os.path.exists("data/port_summary.csv") else "app_data/data"


@st.cache_data
def load():
    ports = pd.read_csv(f"{DATA_DIR}/port_summary.csv")
    ports["continent"] = ports["continent"].fillna("Unknown")
    cm = pd.read_csv(f"{DATA_DIR}/country_monthly.csv", parse_dates=["month_start"])
    info = json.load(open(f"{DATA_DIR}/data_info.json"))
    return ports, cm, info


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def port_daily(portid, since):
    rows, off = [], 0
    while True:
        r = requests.get(
            DAILY, 
            params={
                "where": f"portid = '{portid}' AND date >= '{since}'", 
                "outFields": "date,portcalls", 
                "orderByFields": "ObjectId",
                "returnGeometry": "false", 
                "resultOffset": off, 
                "resultRecordCount": 1000, 
                "f": "json"
            }, 
            timeout=120
        ).json()
        if "error" in r:
            raise RuntimeError(r["error"])
        feats = r.get("features", [])
        rows += [x["attributes"] for x in feats]
        if len(feats) < 1000:
            break
        off += 1000
    d = pd.DataFrame(rows)
    d["date"] = d["date"].map(lambda v: pd.to_datetime(v, unit="ms") if isinstance(v, (int, float)) else pd.to_datetime(v))
    return d.sort_values("date")


try:
    ports, cm, info = load()
except Exception as e:
    st.error(f"Data files could not be loaded: {e}")
    st.stop()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric-line/100/38BDF8/container-ship.png", width=64)
    st.title("NEXUS Port AI")
    st.caption("Global AIS Maritime Intelligence")
    st.markdown("---")
    
    w = st.radio(
        "Observation Window", 
        [28, 90], 
        format_func=lambda d: f"{d}-Day YoY Window"
    )
    
    min_default = 50 if w == 28 else 150
    minvol = st.slider("Min Baseline Traffic Volume", 0, 1000, min_default, step=10)
    
    conts = sorted(ports.continent.dropna().unique())
    pick = st.multiselect("Filter Continents", conts, default=conts)

    st.markdown("---")
    with st.expander("ℹ️ Data Context & Methodology"):
        st.caption(
            "• **Source:** UN Global Platform & IMF PortWatch.\n"
            "• **Tracking:** Real-time AIS transponder signals.\n"
            "• Baseline comparisons evaluate identical calendar days from the prior year to adjust for seasonality."
        )

# --- DATA COMPUTATION ---
df = ports.assign(base=ports[f"base_{w}"], recent=ports[f"recent_{w}"])
df["change"] = df.recent - df.base
df["pct"] = (100 * (df.recent / df.base - 1)).where(df.base > 0).round(1)
shown = df[(df.base >= minvol) & df.continent.isin(pick)].copy()

rb, rr = info[f"baseline_{w}"], info[f"recent_{w}"]
tot_b, tot_r = int(df.base.sum()), int(df.recent.sum())
pct_change = 100 * (tot_r / tot_b - 1)

# --- HERO SECTION ---
st.markdown(f"""
    <div style="padding: 10px 0 20px 0;">
        <h1 style="font-size: 2.4rem; margin-bottom: 4px;">Global Maritime Traffic Radar</h1>
        <p style="color: #94A3B8; font-size: 1.05rem;">
            Comparing window <span style="color: #38BDF8;">{rr[0]} to {rr[1]}</span> 
            against baseline <span style="color: #94A3B8;">{rb[0]} to {rb[1]}</span>
        </p>
    </div>
""", unsafe_allow_html=True)

# --- KPI METRIC TILES ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    trend_class = "text-positive" if pct_change >= 0 else "text-negative"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Tracked Port Calls</div>
            <div class="metric-value">{tot_r:,}</div>
            <div class="metric-sub {trend_class}">
                {"▲" if pct_change >= 0 else "▼"} {pct_change:+.1f}% YoY Overall
            </div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Ranked Ports</div>
            <div class="metric-value">{len(shown):,}</div>
            <div class="metric-sub text-neutral">Meeting Volume Threshold</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    gaining = int((shown.change > 0).sum())
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Expanding Ports</div>
            <div class="metric-value" style="color: #10B981;">{gaining:,}</div>
            <div class="metric-sub text-positive">Increased Activity</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    dropping = int((shown.change < 0).sum())
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Contracting Ports</div>
            <div class="metric-value" style="color: #EF4444;">{dropping:,}</div>
            <div class="metric-sub text-negative">Decreased Activity</div>
        </div>
    """, unsafe_allow_html=True)

# --- MAP VISUALIZATION SECTION ---
st.markdown('<div class="section-header">Spatial Dynamics Map</div>', unsafe_allow_html=True)

if len(shown):
    # Color logic: Red/Orange for drops [239, 68, 68], Green/Teal for gains [16, 185, 129]
    shown["color"] = shown.change.map(
        lambda c: [239, 68, 68, 200] if c < 0 else [16, 185, 129, 200]
    )
    shown["radius"] = (shown.base.clip(lower=1) ** 0.5) * 2200

    # Deck.gl map layer with glowing Scatterplot Layer
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        shown,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        radius_min_pixels=3,
        radius_max_pixels=45,
        stroked=True,
        get_line_color=[255, 255, 255, 60],
        line_width_min_pixels=1
    )

    view_state = pdk.ViewState(latitude=20, longitude=15, zoom=1.3, pitch=25)
    
    st.pydeck_chart(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/dark-v11",
            layers=[scatterplot_layer],
            initial_view_state=view_state,
            tooltip={
                "html": """
                    <div style="background-color: #1E293B; color: #F8FAFC; padding: 10px; border-radius: 8px; border: 1px solid #334155;">
                        <b>{portname}</b> ({country})<br/>
                        <hr style="margin: 5px 0; border-color: #475569;"/>
                        Baseline Calls: <b>{base}</b><br/>
                        Recent Calls: <b>{recent}</b><br/>
                        Volume Net Shift: <b style="color: {'#10B981' if change >= 0 else '#EF4444'};">{change} ({pct}%)</b>
                    </div>
                """,
                "style": {"color": "white", "zIndex": "1000"}
            }
        ),
        height=540
    )
else:
    st.info("No ports meet the selected filter criteria.")

# --- BIGGEST CHANGES SECTION ---
st.markdown('<div class="section-header">Extremes & Volatility</div>', unsafe_allow_html=True)
cols = ["portname", "country", "base", "recent", "change", "pct"]

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🔻 Top 10 Contractions")
    drops_df = shown[shown.change < 0].nsmallest(10, "change")[cols]
    st.dataframe(
        drops_df,
        column_config={
            "portname": "Port",
            "country": "Country",
            "base": st.column_config.NumberColumn("Baseline", format="%d"),
            "recent": st.column_config.NumberColumn("Recent", format="%d"),
            "change": st.column_config.NumberColumn("Net Change", format="%d"),
            "pct": st.column_config.NumberColumn("Change %", format="%.1f%%"),
        },
        hide_index=True,
        use_container_width=True
    )

with col_b:
    st.subheader("🟢 Top 10 Expansions")
    gains_df = shown[shown.change > 0].nlargest(10, "change")[cols]
    st.dataframe(
        gains_df,
        column_config={
            "portname": "Port",
            "country": "Country",
            "base": st.column_config.NumberColumn("Baseline", format="%d"),
            "recent": st.column_config.NumberColumn("Recent", format="%d"),
            "change": st.column_config.NumberColumn("Net Change", format="%d"),
            "pct": st.column_config.NumberColumn("Change %", format="%.1f%%"),
        },
        hide_index=True,
        use_container_width=True
    )

# --- REGIONAL TREND ANALYSIS ---
st.markdown('<div class="section-header">Regional Macro Trends: Gulf vs Rest of World</div>', unsafe_allow_html=True)

rate = cm.pivot(index="month_start", columns="ISO3", values="calls_per_day")
g = [c for c in GULF if c in rate.columns]
ref = [m_ for m_ in rate.index if m_ <= pd.Timestamp("2026-02-01")]

if g and ref:
    gulf = rate[g].sum(axis=1)
    rest = rate.drop(columns=g).sum(axis=1)
    
    macro_df = pd.DataFrame({
        "Date": rate.index,
        "Gulf Region": 100 * gulf / gulf.loc[ref].mean(),
        "Rest of World": 100 * rest / rest.loc[ref].mean()
    }).melt("Date", var_name="Region", value_name="Index")

    chart = alt.Chart(macro_df).mark_line(size=2.5, interpolate="monotone").encode(
        x=alt.X("Date:T", title=""),
        y=alt.Y("Index:Q", title="Indexed Calls/Day (Baseline Avg = 100)"),
        color=alt.Color("Region:N", scale=alt.Scale(domain=["Gulf Region", "Rest of World"], range=["#EF4444", "#38BDF8"])),
        tooltip=["Date:T", "Region:N", alt.Tooltip("Index:Q", format=".1f")]
    ).properties(height=320).configure_view(strokeWidth=0).configure_axis(
        gridColor="rgba(255, 255, 255, 0.05)",
        domainColor="rgba(255, 255, 255, 0.1)",
        labelColor="#94A3B8",
        titleColor="#94A3B8"
    ).configure_legend(
        labelColor="#F8FAFC",
        titleColor="#F8FAFC",
        orient="top-left"
    )

    st.altair_chart(chart, use_container_width=True)

# --- SINGLE PORT DRILLDOWN ---
st.markdown('<div class="section-header">Individual Port Inspector</div>', unsafe_allow_html=True)

opts = df.sort_values("base", ascending=False)
label = opts.portname + ", " + opts.country.fillna("") + " (" + opts.portid + ")"
choice = st.selectbox("Select Port to Inspect", label.tolist())

pid = choice.rsplit("(", 1)[1].rstrip(")")
last = pd.Timestamp(info["last_day"])

try:
    with st.spinner("Fetching high-resolution telemetry..."):
        d = port_daily(pid, str((last - pd.Timedelta(days=400)).date()))
        d["7-day average"] = d["portcalls"].rolling(7).mean()
        
        r_ = df[df.portid == pid].iloc[0]
        
        st.caption(f"**{r_.portname}** recorded **{int(r_.recent):,}** calls over the last {w} days compared to **{int(r_.base):,}** a year prior.")

        # Interactive Daily Chart
        port_chart = alt.Chart(d).mark_area(
            line={"color": "#38BDF8", "size": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(56, 189, 248, 0.4)", offset=1),
                    alt.GradientStop(color="rgba(56, 189, 248, 0.0)", offset=0)
                ],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("7-day average:Q", title="7-Day Moving Avg Calls"),
            tooltip=["date:T", alt.Tooltip("7-day average:Q", format=".1f"), "portcalls:Q"]
        ).properties(height=300).configure_axis(
            gridColor="rgba(255, 255, 255, 0.05)",
            labelColor="#94A3B8",
            titleColor="#94A3B8"
        )
        
        st.altair_chart(port_chart, use_container_width=True)

except Exception as e:
    st.warning(f"Could not load daily telemetry data for this port: {e}")

st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #64748B; font-size: 0.85rem; padding: 10px 0;">
        Powered by UN Global Platform & IMF PortWatch AIS Engine | Nexus Maritime Intelligence
    </div>
""", unsafe_allow_html=True)
