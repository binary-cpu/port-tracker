import html
import json
import os

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

DAILY = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
DATA_DIR = "data" if os.path.exists("data/port_summary.csv") else "app_data/data"
TYPES = {"container": "Container", "dry_bulk": "Dry bulk", "general_cargo": "General cargo", "roro": "Ro-ro", "tanker": "Tanker"}
GULF = ["ARE", "QAT", "IRQ", "IRN", "KWT", "BHR", "SAU", "OMN"]
DROP, GAIN, FLAT = "#E69F00", "#56B4E9", "#8A9BB3"
STORIES = {
    "The Gulf goes quiet": ("Mar 2026", "Gulf-region countries drop sharply this month. The timing matches the Hormuz pattern in my chokepoint project, but both come from the same AIS source and this data does not show why."),
    "Asia pulls ahead": ("May 2026", "India, Korea, the Philippines and Taiwan rise while China falls. The rise is spread across ship types, and I have not established whether it is real traffic or a change in how calls are counted."),
    "The latest month": (None, "The newest complete month in the data. Compare it with the dotted reference: the average of the months up to February 2026."),
}

st.set_page_config(page_title="Where did the ships go?", page_icon="🚢", layout="wide")
st.markdown("""<style>
.block-container{max-width:1150px;padding-top:1.6rem}
#MainMenu,footer{visibility:hidden}
.kicker{letter-spacing:.18em;text-transform:uppercase;font-size:.78rem;color:#E69F00;font-weight:700}
.hero h1{font-family:Georgia,'Times New Roman',serif;font-size:3.3rem;line-height:1.04;margin:.3rem 0 .6rem;font-weight:700}
.hero p{font-size:1.15rem;opacity:.88;max-width:48rem;line-height:1.5}
.stat{background:#12335E;border-radius:16px;padding:1rem 1.2rem;border:1px solid #1d3f6e}
.stat b{display:block;font-family:Georgia,serif;font-size:2.2rem;line-height:1.1}
.stat span{opacity:.78;font-size:.92rem}
.sec{font-family:Georgia,serif;font-size:1.9rem;margin:2.8rem 0 .1rem}
.sub{opacity:.78;margin-bottom:.9rem;max-width:46rem}
.note{border-left:4px solid #E69F00;background:#12335E;padding:.8rem 1rem;border-radius:0 12px 12px 0;margin:.8rem 0}
.row{display:grid;grid-template-columns:minmax(8rem,17rem) 1fr 6rem;gap:.8rem;align-items:center;padding:.32rem 0;border-bottom:1px solid #1d3f6e;font-size:.95rem}
.row small{opacity:.7}.bar{height:12px;border-radius:6px}.num{text-align:right;font-variant-numeric:tabular-nums}
.card{background:#12335E;border-radius:18px;padding:1.2rem 1.4rem;border:1px solid #1d3f6e}
.card h3{font-family:Georgia,serif;font-size:1.7rem;margin:0 0 .2rem}
.big{font-family:Georgia,serif;font-size:2.4rem;line-height:1.1}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load():
    ports = pd.read_csv(f"{DATA_DIR}/port_summary.csv")
    ports["continent"] = ports["continent"].fillna("Unknown"); ports["country"] = ports["country"].fillna("")
    cm = pd.read_csv(f"{DATA_DIR}/country_monthly.csv", parse_dates=["month_start"])
    return ports, cm, json.load(open(f"{DATA_DIR}/data_info.json"))


@st.cache_data(ttl=6 * 3600, show_spinner="Fetching this port's daily history...")
def port_daily(portid, since):
    rows, off = [], 0
    while True:
        r = requests.get(DAILY, params={"where": f"portid = '{portid}' AND date >= '{since}'", "outFields": "date,portcalls", "orderByFields": "ObjectId",
                                        "returnGeometry": "false", "resultOffset": off, "resultRecordCount": 1000, "f": "json"}, timeout=120).json()
        if "error" in r:
            raise RuntimeError(r["error"])
        feats = r.get("features", []); rows += [x["attributes"] for x in feats]
        if len(feats) < 1000:
            break
        off += 1000
    d = pd.DataFrame(rows)
    d["date"] = d["date"].map(lambda v: pd.to_datetime(v, unit="ms") if isinstance(v, (int, float)) else pd.to_datetime(v))
    return d.sort_values("date")


def bars(df, color, label_col="portname"):
    top = max(df["change"].abs().max(), 1)
    out = ""
    for r in df.itertuples():
        pct = "" if pd.isna(r.pct) else f"{r.pct:+.0f}%"
        out += (f'<div class="row"><div>{html.escape(str(r.portname))}<br><small>{html.escape(str(r.country))} · {int(r.base)} → {int(r.recent)}</small></div>'
                f'<div><div class="bar" style="width:{100 * abs(r.change) / top:.0f}%;background:{color}"></div></div><div class="num">{int(r.change):+,}<br><small>{pct}</small></div></div>')
    return out or "<p class='sub'>Nothing matches these settings.</p>"


try:
    ports, cm, info = load()
except Exception as e:
    st.error(f"The data files could not be loaded ({e}).")
    st.stop()

# ---------------- hero ----------------
w = 28
df = ports.assign(base=ports["base_28"], recent=ports["recent_28"])
df["change"] = df.recent - df.base
df["pct"] = (100 * (df.recent / df.base - 1)).where(df.base > 0)
tb, tr = int(df.base.sum()), int(df.recent.sum()); ranked = df[df.base >= 50]
st.markdown(f"""<div class="hero"><div class="kicker">Port Tracker · data through {info['last_day']}</div>
<h1>Where did the ships go?</h1>
<p>Every day, ships call at about {len(ports):,} ports. Travel through the last year, month by month, then meet any port in person.
The data show <b>what changed</b>, never why.</p></div>""", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="stat"><b>{tr:,}</b><span>port calls in the latest 28 days<br>{100 * (tr / tb - 1):+.1f}% against the same days a year earlier</span></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="stat"><b>{int((ranked.change < 0).sum())} down · {int((ranked.change > 0).sum())} up</b><span>among the {len(ranked)} ports with at least 50 calls a year earlier</span></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="stat"><b>{int(ports.ISO3.nunique())} countries</b><span>AIS-observed ship calls, a snapshot refreshed by hand</span></div>', unsafe_allow_html=True)
st.markdown('<div class="note"><b>Read this as a map of changes, not causes.</b> Counts come from ships\' tracking signals (AIS), which miss ships with transponders off. Each comparison inherits what happened a year earlier.</div>', unsafe_allow_html=True)

# ---------------- time machine ----------------
st.markdown('<div class="sec">The time machine</div><div class="sub">Drag the clock, or press a story. Each bubble is a country, placed at its busiest port. Orange fell below its usual level, blue rose above it, grey stayed close.</div>', unsafe_allow_html=True)
rate = cm.pivot(index="month_start", columns="ISO3", values="calls_per_day").sort_index()
labels = [m.strftime("%b %Y") for m in rate.index]
pre = [m for m in rate.index if m <= pd.Timestamp("2026-02-01")] or list(rate.index)
ref = rate.loc[pre].mean()
if "month" not in st.session_state:
    st.session_state["month"] = labels[-1]


def go(story):
    month = STORIES[story][0] or labels[-1]
    if month in labels:
        st.session_state["month"] = month; st.session_state["story"] = story


cols = st.columns(len(STORIES))
for col, name in zip(cols, STORIES):
    col.button(name, on_click=go, args=(name,), width="stretch", disabled=(STORIES[name][0] not in labels and STORIES[name][0] is not None))
month_label = st.select_slider("Move the clock", options=labels, key="month")
mi = labels.index(month_label)
story = st.session_state.get("story")
if story and (STORIES[story][0] or labels[-1]) == month_label:
    st.markdown(f'<div class="note"><b>{html.escape(story)}.</b> {html.escape(STORIES[story][1])}</div>', unsafe_allow_html=True)

hub = ports.sort_values("base_90", ascending=False).drop_duplicates("ISO3").set_index("ISO3")[["lat", "lon", "country"]]
now = rate.iloc[mi]
m = pd.DataFrame({"now": now, "ref": ref}).join(hub, how="inner")
m = m[m.ref >= 3].copy()
m["ratio"] = m.now / m.ref
m["color"] = m.ratio.map(lambda x: [230, 159, 0, 215] if x < 0.8 else ([86, 180, 233, 215] if x > 1.2 else [138, 155, 179, 170]))
m["radius"] = m.now.clip(lower=0.5) ** 0.5 * 14000
m["text"] = m.apply(lambda r: f"{r.country}: {r.now:.0f} calls a day ({100 * (r.ratio - 1):+.0f}% vs usual)", axis=1)
layer = pdk.Layer("ScatterplotLayer", m.reset_index(), get_position="[lon, lat]", get_radius="radius", get_fill_color="color", pickable=True,
                  radius_min_pixels=3, radius_max_pixels=46, stroked=True, get_line_color=[11, 37, 69, 255], line_width_min_pixels=1)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=22, longitude=35, zoom=1.15), map_provider="carto", map_style="dark",
                         tooltip={"text": "{text}"}), height=520)
if mi > 0:
    prev = rate.iloc[mi - 1]; chg = (now / prev - 1) * 100; big = prev >= 10
    cn = hub["country"]
    ups, downs = chg[big].nlargest(3), chg[big].nsmallest(3)
    fmt = lambda s: " · ".join(f"<b>{html.escape(cn.get(i, i))}</b> {v:+.0f}%" for i, v in s.items())
    st.markdown(f'<div class="sub">Against the month before ({labels[mi - 1]}, per day):<br>Biggest falls: {fmt(downs)}<br>Biggest rises: {fmt(ups)}</div>', unsafe_allow_html=True)

g = [c for c in GULF if c in rate.columns]
if g:
    gulf, rest = rate[g].sum(axis=1), rate.drop(columns=g).sum(axis=1)
    idx = pd.DataFrame({"Gulf-region countries": 100 * gulf / gulf.loc[pre].mean(), "Rest of the world": 100 * rest / rest.loc[pre].mean()})
    st.line_chart(idx, color=[DROP, FLAT], height=230)
    st.caption("Calls per day, indexed so the months up to February 2026 average 100. The Gulf grouping is by country, so it is approximate.")

# ---------------- leaderboard ----------------
st.markdown('<div class="sec">The movers</div><div class="sub">Ports ranked by the change in ship calls: the latest 28 days against the same 28 days a year earlier. Percentages sit under the numbers because a big percentage on a small port can mislead.</div>', unsafe_allow_html=True)
minvol = st.slider("Only rank ports with at least this many calls a year earlier", 0, 1000, 50, step=10)
pool = df[df.base >= minvol]
t1, t2 = st.tabs(["Fell the most", "Grew the most"])
t1.markdown(bars(pool[pool.change < 0].nsmallest(10, "change"), DROP), unsafe_allow_html=True)
t2.markdown(bars(pool[pool.change > 0].nlargest(10, "change"), GAIN), unsafe_allow_html=True)
st.caption("A port that looks like a big gain may be recovering from a low period a year ago. The monthly history shows which.")

# ---------------- port postcard ----------------
st.markdown('<div class="sec">Meet a port</div><div class="sub">Pick any port for its postcard. Type to search.</div>', unsafe_allow_html=True)
opts = df.sort_values("base", ascending=False)
label = (opts.portname + ", " + opts.country + " (" + opts.portid + ")").tolist()
pid = st.selectbox("Port", label).rsplit("(", 1)[1].rstrip(")")
r_ = df[df.portid == pid].iloc[0]
verb = "fewer" if r_.change < 0 else "more"
mix = "".join(f'<div class="row"><div>{n}</div><div><div class="bar" style="width:{100 * r_[f"recent_28_{k}"] / max(r_.recent, 1):.0f}%;background:{GAIN}"></div></div><div class="num">{int(r_[f"recent_28_{k}"])}</div></div>' for k, n in TYPES.items())
left, right = st.columns([1, 1.25])
with left:
    st.markdown(f'<div class="card"><h3>{html.escape(r_.portname)}</h3><span style="opacity:.75">{html.escape(r_.country)} · {html.escape(r_.continent)}</span>'
                f'<p class="big">{int(r_.recent):,} calls</p><p>in the latest 28 days: <b>{abs(int(r_.change)):,} {verb}</b> than the {int(r_.base):,} a year earlier'
                f'{"" if pd.isna(r_.pct) else f" ({r_.pct:+.1f}%)"}.</p><b>Ship mix, latest 28 days</b>{mix}</div>', unsafe_allow_html=True)
with right:
    try:
        d = port_daily(pid, str((pd.Timestamp(info["last_day"]) - pd.Timedelta(days=400)).date()))
        d["7-day average"] = d["portcalls"].rolling(7).mean()
        st.line_chart(d.set_index("date")[["7-day average"]], color=[GAIN], height=300)
        st.caption("Calls per day, 7-day average, the last 400 days.")
    except Exception as e:
        st.warning(f"Could not load this port's daily history right now ({e}).")

st.markdown("---")
st.markdown("Sources: UN Global Platform; IMF PortWatch (AIS-observed port calls). Method, notebooks and code: github.com/binary-cpu/port-tracker")
