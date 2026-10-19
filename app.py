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
    page_title="NEXUS | Maritime Intelligence Command",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS & ANIMATIONS INJECTION ---
st.markdown("""
<style>
    /* Dark Command Theme */
    .stApp {
        background-color: #07090E;
        color: #E2E8F0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    header[data-testid="stHeader"] { background: rgba(7, 9, 14, 0.8); }

    /* Keyframe Animations */
    @keyframes pulseGlow {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animated-container {
        animation: fadeIn 0.6s ease-out forwards;
    }

    .live-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
        animation: pulseGlow 2s infinite;
    }
    
    /* Glassmorphism Metric Cards with Hover Glow */
    div.metric-card {
        background: linear-gradient(135deg, rgba(22, 27, 38, 0.8) 0%, rgba(13, 17, 23, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    div.metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 15px 35px 0 rgba(56, 189, 248, 0.15);
    }
    
    .metric-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #94A3B8;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.03em;
    }
    .metric-sub {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 8px;
    }
    .text-positive { color: #10B981; }
    .text-negative { color: #EF4444; }
    .text-neutral { color: #38BDF8; }

    /* Section Headers */
    .section-header {
        border-left: 4px solid #38BDF8;
        padding-left: 12px;
        margin: 35px 0 18px 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: #F8FAFC;
        letter-spacing: -0.01em;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: #0C1017;
        border-right: 1px solid rgba(255, 255, 255, 0.04);
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
    st.markdown("### ⚓ NEXUS COMMAND")
    st.caption("Global Maritime Telemetry")
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
    with st.expander("ℹ️ Telemetry Notes"):
        st.caption(
            "• **Sources:** UN Global Platform & IMF PortWatch.\n"
            "• **Tracking:** AIS Transponder Analytics.\n"
            "• Seasonally adjusted against identical baseline periods from the previous year."
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
    <div class="animated-container" style="padding: 10px 0 15px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="font-size: 2.3rem; margin: 0 0 6px 0; color: #F8FAFC;">Global Port Traffic Intelligence</h1>
                <p style="color: #94A3B8; font-size: 1rem; margin: 0;">
                    Comparing <span style="color: #38BDF8; font-weight: 600;">{rr[0]} to {rr[1]}</span> 
                    vs Baseline <span style="color: #94A3B8; font-weight: 600;">{rb[0]} to {rb[1]}</span>
                </p>
            </div>
            <div>
                <div class="live-badge">
                    <span class="pulse-dot"></span>AIS ENGINE ACTIVE
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- KPI METRIC TILES ---
k1, k2, k3, k4 = st.columns(4)

with k1:
    trend_class = "text-positive" if pct_change >= 0 else "text-negative"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Port Calls</div>
            <div class="metric-value">{tot_r:,}</div>
            <div class="metric-sub {trend_class}">
                {"▲" if pct_change >= 0 else "▼"} {pct_change:+.1f}% YoY Volume
            </div>
        </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Ranked Ports</div>
            <div class="metric-value">{len(shown):,}</div>
            <div class="metric-sub text-neutral">Passing Threshold</div>
        </div>
    """, unsafe_allow_html=True)

with k3:
    gaining = int((shown.change > 0).sum())
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Expansions</div>
            <div class="metric-value" style="color: #10B981;">{gaining:,}</div>
            <div class="metric-sub text-positive">Traffic Increased</div>
        </div>
    """, unsafe_allow_html=True)

with k4:
    dropping = int((shown.change < 0).sum())
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Contractions</div>
            <div class="metric-value" style="color: #EF4444;">{dropping:,}</div>
            <div class="metric-sub text-negative">Traffic Decreased</div>
        </div>
    """, unsafe_allow_html=True)

# --- MAP VISUALIZATION SECTION ---
st.markdown('<div class="section-header">Live Spatial Vector Map</div>', unsafe_allow_html=True)

if len(shown):
    # Color mapping: Emerald for positive gains, Red for contractions
    shown["color"] = shown.change.map(
        lambda c: [239, 68, 68, 210] if c < 0 else [16, 185, 129, 210]
    )
    shown["radius"] = (shown.base.clip(lower=1) ** 0.5) * 2400

    # PyDeck layer with standard token-free dark map style
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        shown,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        radius_min_pixels=3,
        radius_max_pixels=42,
        stroked=True,
        get_line_color=[255, 255, 255, 80],
        line_width_min_pixels=1
    )

    view_state = pdk.ViewState(latitude=20, longitude=15, zoom=1.4, pitch=20)
    
    st.pydeck_chart(
        pdk.Deck(
            map_style=pdk.map_styles.DARK,
            layers=[scatterplot_layer],
            initial_view_state=view_state,
            tooltip={
                "html": """
                    <div style="background-color: #0F172A; color: #F8FAFC; padding: 12px; border-radius: 10px; border: 1px solid #334155; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                        <b style="font-size: 1rem; color: #38BDF8;">{portname}</b> ({country})<br/>
                        <hr style="margin: 6px 0; border-color: #334155;"/>
                        Baseline Calls: <b>{base}</b><br/>
                        Recent Calls: <b>{recent}</b><br/>
                        Net Shift: <b style="color: {'#10B981' if change >= 0 else '#EF4444'};">{change} ({pct}%)</b>
                    </div>
                """,
                "style": {"color": "white", "zIndex": "1000"}
            }
        ),
        height=520
    )
    st.caption("🟢 Green: Increased traffic vs. year earlier. 🔴 Red: Decreased traffic. Circle scale represents baseline volume.")
else:
    st.info("No ports meet the selected filter criteria.")

# --- BIGGEST CHANGES SECTION ---
st.markdown('<div class="section-header">Volatility Extremes</div>', unsafe_allow_html=True)
cols = ["portname", "country", "base", "recent", "change", "pct"]

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**🔻 Top 10 Contractions**")
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
    st.markdown("**🟢 Top 10 Expansions**")
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
st.markdown('<div class="section-header">Regional Macro Index: Gulf vs Rest of World</div>', unsafe_allow_html=True)

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

    chart = alt.Chart(macro_df).mark_line(size=3, interpolate="monotone").encode(
        x=alt.X("Date:T", title=""),
        y=alt.Y("Index:Q", title="Indexed Calls/Day (Baseline Avg = 100)"),
        color=alt.Color("Region:N", scale=alt.Scale(domain=["Gulf Region", "Rest of World"], range=["#EF4444", "#38BDF8"])),
        tooltip=["Date:T", "Region:N", alt.Tooltip("Index:Q", format=".1f")]
    ).properties(height=320).configure_view(strokeWidth=0).configure_axis(
        gridColor="rgba(255, 255, 255, 0.04)",
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
st.markdown('<div class="section-header">Individual Port Telemetry Inspector</div>', unsafe_allow_html=True)

opts = df.sort_values("base", ascending=False)
label = opts.portname + ", " + opts.country.fillna("") + " (" + opts.portid + ")"
choice = st.selectbox("Select Port", label.tolist())

pid = choice.rsplit("(", 1)[1].rstrip(")")
last = pd.Timestamp(info["last_day"])

try:
    with st.spinner("Streaming port telemetry..."):
        d = port_daily(pid, str((last - pd.Timedelta(days=400)).date()))
        d["7-day average"] = d["portcalls"].rolling(7).mean()
        
        r_ = df[df.portid == pid].iloc[0]
        
        st.caption(f"**{r_.portname}** recorded **{int(r_.recent):,}** calls over the last {w} days against **{int(r_.base):,}** a year earlier (Past 400 Days Rolling Average).")

        port_chart = alt.Chart(d).mark_area(
            line={"color": "#38BDF8", "size": 2.5},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(56, 189, 248, 0.5)", offset=1),
                    alt.GradientStop(color="rgba(56, 189, 248, 0.0)", offset=0)
                ],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("7-day average:Q", title="7-Day Moving Avg Calls"),
            tooltip=["date:T", alt.Tooltip("7-day average:Q", format=".1f"), "portcalls:Q"]
        ).properties(height=300).configure_axis(
            gridColor="rgba(255, 255, 255, 0.04)",
            labelColor="#94A3B8",
            titleColor="#94A3B8"
        )
        
        st.altair_chart(port_chart, use_container_width=True)

except Exception as e:
    st.warning(f"Could not load daily telemetry data for this port: {e}")

st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #64748B; font-size: 0.8rem; padding: 10px 0;">
        Powered by UN Global Platform & IMF PortWatch AIS Engine | Nexus Maritime Intelligence Command
    </div>
""", unsafe_allow_html=True)
