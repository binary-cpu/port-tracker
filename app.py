
import json
import os

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# =========================================================
# CONFIGURATION
# =========================================================

DAILY = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/"
    "arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
)

GULF = ["ARE", "QAT", "IRQ", "IRN", "KWT", "BHR", "SAU", "OMN"]

NAVY = "#071525"
PANEL = "#102438"
BLUE = "#48D6D2"
UP_COLOR = [72, 214, 210, 210]
DOWN_COLOR = [255, 118, 95, 210]
MUTED = "#91A9BE"

st.set_page_config(
    page_title="Port Tracker | Maritime Intelligence",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = (
    "data"
    if os.path.exists("data/port_summary.csv")
    else "app_data/data"
)

# =========================================================
# VISUAL DESIGN
# =========================================================

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap'
    );

    :root {
        --navy: #071525;
        --panel: #102438;
        --border: #21394e;
        --cyan: #48D6D2;
        --text: #F1F6FC;
        --muted: #91A9BE;
    }

    .stApp {
        background: var(--navy);
        color: var(--text);
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(7, 21, 37, 0.92);
    }

    [data-testid="stSidebar"] {
        background: #0B1D30;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] * {
        font-family: 'DM Sans', sans-serif;
    }

    .block-container {
        max-width: 1600px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.6px;
        color: var(--text);
    }

    h1 {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
    }

    h2 {
        font-size: 1.35rem !important;
    }

    p, label, li {
        line-height: 1.65;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #122A40, #0D2033);
        border: 1px solid var(--border);
        padding: 19px 20px;
        border-radius: 15px;
        min-height: 125px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: 0.84rem !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--text) !important;
        font-weight: 700;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }

    div[data-testid="stPlotlyChart"],
    div[data-testid="stDeckGlJsonChart"],
    div[data-testid="stVegaLiteChart"] {
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 13px;
        margin-bottom: 24px;
    }

    .brand-icon {
        background: #15364B;
        color: var(--cyan);
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 13px;
        font-size: 25px;
        border: 1px solid #28506A;
    }

    .brand-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
        color: var(--text);
    }

    .brand-sub {
        color: var(--muted);
        font-size: 10px;
        letter-spacing: 2px;
        margin-top: 3px;
    }

    .eyebrow {
        color: var(--cyan);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 9px;
    }

    .hero {
        background:
            radial-gradient(
                ellipse at 95% 0%,
                rgba(72,214,210,0.12),
                transparent 42%
            ),
            linear-gradient(135deg, #102A40, #0B1B2D);
        border: 1px solid #25445B;
        border-radius: 18px;
        padding: 27px 30px;
        margin-bottom: 25px;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(26px, 3.2vw, 39px);
        font-weight: 700;
        line-height: 1.2;
        color: var(--text);
        margin: 8px 0 12px 0;
        letter-spacing: -1.3px;
    }

    .hero-copy {
        color: #B2C6D8;
        font-size: 15px;
        max-width: 680px;
        line-height: 1.7;
    }

    .status-pill {
        display: inline-block;
        border: 1px solid #286B69;
        color: var(--cyan);
        background: rgba(72,214,210,0.08);
        border-radius: 20px;
        padding: 5px 11px;
        font-size: 11px;
        letter-spacing: 0.5px;
    }

    .section-kicker {
        color: var(--muted);
        font-size: 0.7rem;
        letter-spacing: 1.8px;
        font-weight: 700;
        margin-bottom: 5px;
        text-transform: uppercase;
    }

    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 5px;
    }

    .section-copy {
        color: var(--muted);
        font-size: 0.87rem;
        margin-bottom: 18px;
    }

    .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 17px;
        color: var(--muted);
        font-size: 12px;
        margin: 12px 0 18px;
    }

    .legend span {
        display: flex;
        align-items: center;
        gap: 7px;
    }

    .dot {
        height: 9px;
        width: 9px;
        border-radius: 50%;
        display: inline-block;
    }

    .footnote {
        color: var(--muted);
        font-size: 0.77rem;
        line-height: 1.7;
    }

    .stButton > button {
        border-radius: 9px;
    }

    button[data-baseweb="tab"] {
        font-weight: 600;
    }

    hr {
        border-color: var(--border);
    }

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    @media (max-width: 700px) {
        .block-container {
            padding: 1rem 1rem 2rem;
        }
        .hero {
            padding: 21px;
        }
        h1 {
            font-size: 1.8rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def load():
    ports = pd.read_csv(f"{DATA_DIR}/port_summary.csv")
    ports["continent"] = ports["continent"].fillna("Unknown")

    cm = pd.read_csv(
        f"{DATA_DIR}/country_monthly.csv",
        parse_dates=["month_start"],
    )

    with open(f"{DATA_DIR}/data_info.json", encoding="utf-8") as f:
        info = json.load(f)

    return ports, cm, info


@st.cache_data(ttl=6 * 3600, show_spinner="Loading port history...")
def port_daily(portid, since):
    rows = []
    offset = 0

    while True:
        response = requests.get(
            DAILY,
            params={
                "where": (
                    f"portid = '{portid}' "
                    f"AND date >= '{since}'"
                ),
                "outFields": "date,portcalls",
                "orderByFields": "ObjectId",
                "returnGeometry": "false",
                "resultOffset": offset,
                "resultRecordCount": 1000,
                "f": "json",
            },
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            raise RuntimeError(result["error"])

        features = result.get("features", [])
        rows.extend(x["attributes"] for x in features)

        if len(features) < 1000:
            break

        offset += len(features)

    if not rows:
        return pd.DataFrame(columns=["date", "portcalls"])

    d = pd.DataFrame(rows)

    def parse_date(value):
        if pd.isna(value):
            return pd.NaT
        if isinstance(value, (int, float)):
            return pd.to_datetime(value, unit="ms", utc=True).tz_localize(None)
        return pd.to_datetime(value, utc=True).tz_localize(None)

    d["date"] = d["date"].map(parse_date)
    d["portcalls"] = pd.to_numeric(d["portcalls"], errors="coerce")

    return d.sort_values("date")


try:
    ports, cm, info = load()
except Exception as e:
    st.error(f"Could not load the data files: {e}")
    st.stop()

# =========================================================
# BRAND AND HERO
# =========================================================

st.markdown(
    """
    <div class="brand">
        <div class="brand-icon">⚓</div>
        <div>
            <div class="brand-name">PORT TRACKER</div>
            <div class="brand-sub">MARITIME INTELLIGENCE</div>
        </div>
    </div>

    <div class="hero">
        <div class="eyebrow">GLOBAL PORT ACTIVITY</div>
        <div class="hero-title">
            Know where traffic is changing.
        </div>
        <div class="hero-copy">
            Explore port activity, compare year-over-year changes,
            and identify movements in global maritime traffic.
            Evidence first. Explanations require further investigation.
        </div>
        <br>
        <span class="status-pill">● HISTORICAL AIS DATA</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Latest source date: {info['last_day']} · "
    "Data is refreshed manually, not in real time."
)

# =========================================================
# SIDEBAR FILTERS
# =========================================================

with st.sidebar:
    st.markdown("## ⚓ Port Tracker")
    st.caption("ANALYSIS CONTROLS")
    st.divider()

    w = st.radio(
        "Comparison period",
        [28, 90],
        format_func=lambda d: (
            f"{d} days vs same period last year"
        ),
    )

    min_default = 50 if w == 28 else 150

    minvol = st.slider(
        "Minimum baseline calls",
        min_value=0,
        max_value=1000,
        value=min_default,
        step=10,
        help=(
            "Ports below this baseline are excluded from "
            "the rankings to reduce small-sample noise."
        ),
    )

    conts = sorted(ports["continent"].dropna().unique().tolist())

    pick = st.multiselect(
        "Continents",
        conts,
        default=conts,
    )

    st.divider()
    st.caption("DATA SOURCES")
    st.markdown(
        """
        <div class="footnote">
        • UN Global Platform<br>
        • IMF PortWatch<br>
        • ArcGIS daily port service
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("Refresh local data", use_container_width=True):
        load.clear()
        port_daily.clear()
        st.rerun()

# =========================================================
# COMPARISON DATA
# =========================================================

df = ports.copy()
df["base"] = pd.to_numeric(df[f"base_{w}"], errors="coerce")
df["recent"] = pd.to_numeric(df[f"recent_{w}"], errors="coerce")

df["change"] = df["recent"] - df["base"]
df["pct"] = (
    100 * (df["recent"] / df["base"] - 1)
).where(df["base"] > 0).round(1)

shown = df[
    (df["base"] >= minvol)
    & df["continent"].isin(pick)
].copy()

rb = info[f"baseline_{w}"]
rr = info[f"recent_{w}"]

st.markdown(
    f"""
    <div class="section-kicker">REPORTING WINDOW</div>
    <div class="section-copy">
        Comparing <b>{rr[0]} – {rr[1]}</b>
        against <b>{rb[0]} – {rb[1]}</b>.
        Rankings reflect the selected filters.
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# KPI CARDS
# =========================================================

tot_b = df["base"].sum()
tot_r = df["recent"].sum()

overall_pct = (
    100 * (tot_r / tot_b - 1)
    if tot_b > 0
    else 0
)

down_count = int((shown["change"] < 0).sum())
up_count = int((shown["change"] > 0).sum())

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "PORT CALLS",
    f"{tot_r:,.0f}",
    f"{overall_pct:+.1f}% vs year earlier",
    delta_color="off",
    help="Total calls across all ports in the selected window.",
)

k2.metric(
    "PORTS RANKED",
    f"{len(shown):,}",
    "Based on active filters",
)

k3.metric(
    "TRAFFIC DECLINES",
    f"{down_count:,}",
    "Fewer calls than baseline",
    delta_color="inverse",
)

k4.metric(
    "TRAFFIC INCREASES",
    f"{up_count:,}",
    "More calls than baseline",
    delta_color="normal",
)

st.write("")

# =========================================================
# MAIN ANALYSIS TABS
# =========================================================

tab_map, tab_rank, tab_regions, tab_detail = st.tabs(
    [
        "🌍  Global map",
        "↕️  Port rankings",
        "📈  Regional trends",
        "🔎  Port explorer",
    ]
)

# =========================================================
# TAB 1: MAP
# =========================================================

with tab_map:
    st.markdown(
        '<div class="section-title">Global traffic map</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">'
        'Explore where port calls are rising or falling. '
        'Select a marker to inspect the port.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="legend">
            <span><i class="dot" style="background:#FF765F"></i>
            Traffic down</span>
            <span><i class="dot" style="background:#48D6D2"></i>
            Traffic up or unchanged</span>
            <span>Circle size = baseline traffic</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    map_data = shown.dropna(subset=["lon", "lat"]).copy()

    if len(map_data):
        map_data["radius"] = (
            map_data["base"].clip(lower=1).pow(0.5) * 2500
        ).clip(upper=50000)

        map_data["color"] = map_data["change"].map(
            lambda value: (
                DOWN_COLOR if value < 0 else UP_COLOR
            )
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position="[lon, lat]",
            get_radius="radius",
            get_fill_color="color",
            get_line_color=[220, 235, 245, 180],
            line_width_min_pixels=1,
            stroked=True,
            filled=True,
            pickable=True,
            auto_highlight=True,
            radius_min_pixels=3,
            radius_max_pixels=30,
        )

        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=pdk.ViewState(
                latitude=20,
                longitude=20,
                zoom=0.6,
                min_zoom=0,
                max_zoom=12,
            ),
            map_style=(
                "https://basemaps.cartocdn.com/gl/"
                "dark-matter-gl-style/style.json"
            ),
            tooltip={
                "html": """
                    <div style="font-family:Arial;padding:6px">
                    <b>{portname}</b><br/>
                    {country}<br/><br/>
                    Baseline: {base}<br/>
                    Recent: {recent}<br/>
                    Change: {change}<br/>
                    Change: {pct}%
                    </div>
                """,
                "style": {
                    "backgroundColor": "#102438",
                    "color": "#F1F6FC",
                    "border": "1px solid #28506A",
                    "borderRadius": "8px",
                    "padding": "12px",
                },
            },
        )

        st.pydeck_chart(
            deck,
            use_container_width=True,
            height=560,
        )

        st.caption(
            "Marker locations and boundaries are inherited from "
            "the source dataset. The map is not a live vessel tracker."
        )
    else:
        st.info(
            "No ports with valid coordinates meet the current filters."
        )

# =========================================================
# TAB 2: RANKINGS
# =========================================================

with tab_rank:
    st.markdown(
        '<div class="section-title">Biggest changes in port calls</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">'
        'Rankings show absolute changes. Read these together '
        'with percentage changes and baseline traffic.'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = [
        "portname",
        "country",
        "base",
        "recent",
        "change",
        "pct",
    ]

    drops, gains = st.columns(2)

    with drops:
        st.markdown("### 🔻 Biggest drops")

        drop_data = (
            shown[shown["change"] < 0]
            .nsmallest(10, "change")[cols]
            .rename(
                columns={
                    "portname": "Port",
                    "country": "Country",
                    "base": "Baseline",
                    "recent": "Recent",
                    "change": "Change",
                    "pct": "Change %",
                }
            )
        )

        st.dataframe(
            drop_data,
            hide_index=True,
            use_container_width=True,
        )

    with gains:
        st.markdown("### 🔹 Biggest gains")

        gain_data = (
            shown[shown["change"] > 0]
            .nlargest(10, "change")[cols]
            .rename(
                columns={
                    "portname": "Port",
                    "country": "Country",
                    "base": "Baseline",
                    "recent": "Recent",
                    "change": "Change",
                    "pct": "Change %",
                }
            )
        )

        st.dataframe(
            gain_data,
            hide_index=True,
            use_container_width=True,
        )

    st.divider()

    st.markdown("### All ranked ports")

    all_ranked = shown.sort_values(
        "change", ascending=True
    )[cols].rename(
        columns={
            "portname": "Port",
            "country": "Country",
            "base": "Baseline",
            "recent": "Recent",
            "change": "Change",
            "pct": "Change %",
        }
    )

    st.dataframe(
        all_ranked,
        hide_index=True,
        use_container_width=True,
        height=420,
    )

    st.download_button(
        "Download rankings as CSV",
        data=all_ranked.to_csv(index=False).encode("utf-8"),
        file_name="port_tracker_rankings.csv",
        mime="text/csv",
    )

    st.caption(
        "A percentage increase on a small baseline may represent "
        "few additional calls. Rankings do not establish causes."
    )

# =========================================================
# TAB 3: REGIONAL TRENDS
# =========================================================

with tab_regions:
    st.markdown(
        '<div class="section-title">'
        'Gulf-region countries vs the rest of the world'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-copy">'
        'Compare monthly calls per day, indexed to a historical '
        'reference period. This is a country grouping, not a '
        'precise geographic boundary.'
        '</div>',
        unsafe_allow_html=True,
    )

    rate = cm.pivot_table(
        index="month_start",
        columns="ISO3",
        values="calls_per_day",
        aggfunc="sum",
    ).sort_index()

    gulf_codes = [c for c in GULF if c in rate.columns]

    ref = rate.index <= pd.Timestamp("2026-02-01")

    if gulf_codes and ref.any():
        gulf = rate[gulf_codes].sum(axis=1, min_count=1)

        rest = rate.drop(
            columns=gulf_codes
        ).sum(axis=1, min_count=1)

        gulf_base = gulf.loc[ref].mean()
        rest_base = rest.loc[ref].mean()

        if gulf_base and rest_base:
            indexed = pd.DataFrame(
                {
                    "Gulf-region countries": (
                        100 * gulf / gulf_base
                    ),
                    "Rest of the world": (
                        100 * rest / rest_base
                    ),
                }
            )

            st.line_chart(
                indexed,
                color=["#48D6D2", "#91A9BE"],
                use_container_width=True,
                height=420,
            )

            st.caption(
                "Index 100 = average of monthly calls per day "
                "through February 2026. Confirm that the "
                "reference period is fully covered by your data."
            )
        else:
            st.warning(
                "The reference period has no usable baseline."
            )
    else:
        st.info(
            "The country-month data does not contain enough "
            "columns or reference months for this comparison."
        )

# =========================================================
# TAB 4: PORT EXPLORER
# =========================================================

with tab_detail:
    st.markdown(
        '<div class="section-title">Explore an individual port</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-copy">'
        'Inspect the daily history behind a port-level comparison.'
        '</div>',
        unsafe_allow_html=True,
    )

    opts = df.sort_values("base", ascending=False).copy()

    opts["label"] = (
        opts["portname"].fillna("Unknown port")
        + ", "
        + opts["country"].fillna("Unknown country")
        + " ("
        + opts["portid"].astype(str)
        + ")"
    )

    if not opts.empty:
        choice = st.selectbox(
            "Choose a port",
            opts["label"].tolist(),
        )

        selected = opts.loc[
            opts["label"] == choice
        ].iloc[0]

        pid = str(selected["portid"])
        last = pd.Timestamp(info["last_day"])

        try:
            daily = port_daily(
                pid,
                str((last - pd.Timedelta(days=400)).date()),
            )

            if daily.empty:
                st.warning(
                    "No daily records were returned for this port."
                )
            else:
                daily["7-day average"] = (
                    daily["portcalls"].rolling(7).mean()
                )

                st.markdown("### Daily port-call trend")

                st.line_chart(
                    daily.set_index("date")[["7-day average"]],
                    color="#48D6D2",
                    use_container_width=True,
                    height=380,
                )

                p1, p2, p3 = st.columns(3)

                p1.metric(
                    "Recent calls",
                    f"{selected['recent']:,.0f}",
                )

                p2.metric(
                    "Baseline calls",
                    f"{selected['base']:,.0f}",
                )

                p3.metric(
                    "Change",
                    f"{selected['change']:+,.0f}",
                    delta_color="off",
                )

                st.caption(
                    "The chart displays a seven-day rolling average "
                    "over the available history. Missing dates must "
                    "not automatically be interpreted as zero calls."
                )

                st.download_button(
                    "Download daily history",
                    data=daily.to_csv(index=False).encode("utf-8"),
                    file_name=f"port_{pid}_daily_history.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.warning(
                f"Could not load daily port history: {e}"
            )
    else:
        st.info("No ports are available in the loaded dataset.")

# =========================================================
# FOOTER
# =========================================================

st.divider()

f1, f2 = st.columns([2, 1])

with f1:
    st.markdown(
        """
        **PORT TRACKER**
        
        <div class="footnote">
        An independent maritime data exploration project.
        Sources: UN Global Platform, IMF PortWatch and the
        configured ArcGIS daily port service.
        </div>
        """,
        unsafe_allow_html=True,
    )

with f2:
    st.markdown(
        """
        <div class="footnote" style="text-align:right">
        Built for maritime insight.<br/>
        Historical data, not live vessel positions.
        </div>
        """,
        unsafe_allow_html=True,
    )
