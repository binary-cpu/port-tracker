import json
import os
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

DAILY = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Ports_Data/FeatureServer/0/query"
TYPES = ["container", "dry_bulk", "general_cargo", "roro", "tanker"]
GULF = ["ARE", "QAT", "IRQ", "IRN", "KWT", "BHR", "SAU", "OMN"]

st.set_page_config(page_title="Port Tracker", layout="wide")


DATA_DIR = "data" if os.path.exists("data/port_summary.csv") else "app_data/data"      # works whether the folder was uploaded as data/ or app_data/data/


@st.cache_data
def load():
    ports = pd.read_csv(f"{DATA_DIR}/port_summary.csv")
    ports["continent"] = ports["continent"].fillna("Unknown")      # keep ports with no continent label in the default view
    cm = pd.read_csv(f"{DATA_DIR}/country_monthly.csv", parse_dates=["month_start"])
    info = json.load(open(f"{DATA_DIR}/data_info.json"))
    return ports, cm, info


@st.cache_data(ttl=6 * 3600, show_spinner="Loading daily calls for this port...")
def port_daily(portid, since):
    rows, off = [], 0
    while True:
        r = requests.get(DAILY, params={"where": f"portid = '{portid}' AND date >= '{since}'", "outFields": "date,portcalls", "orderByFields": "ObjectId",
                                        "returnGeometry": "false", "resultOffset": off, "resultRecordCount": 1000, "f": "json"}, timeout=120).json()
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
    st.error(f"The data files could not be loaded ({e}).")
    st.stop()

st.title("Port Tracker")
st.caption("Which ports gained or lost ship traffic compared with a year earlier? Sources: UN Global Platform; IMF PortWatch.")
st.markdown(f"**Data through {info['last_day']}.** This is a snapshot of AIS-observed port calls, refreshed by hand; it is not live.")
with st.expander("Read this first", expanded=True):
    st.markdown(
        "- Counts are AIS-observed port calls. A port is an area defined by the source, and ships with transponders off are missed.\n"
        "- Each port is compared with the same days a year earlier, so the result inherits whatever happened then. A port that looks like a big gain may be recovering from a low period.\n"
        "- Small ports are noisy, so ports need a minimum number of baseline calls to be ranked (set it in the sidebar).\n"
        "- The dashboard shows what changed, not why. No change here is linked to a cause.")

w = st.sidebar.radio("Compare the latest", [28, 90], format_func=lambda d: f"{d} days with the same {d} days a year earlier")
min_default = 50 if w == 28 else 150
minvol = st.sidebar.slider("Minimum baseline calls to rank a port", 0, 1000, min_default, step=10)
conts = sorted(ports.continent.dropna().unique())
pick = st.sidebar.multiselect("Continents", conts, default=conts)

df = ports.assign(base=ports[f"base_{w}"], recent=ports[f"recent_{w}"])
df["change"] = df.recent - df.base
df["pct"] = (100 * (df.recent / df.base - 1)).where(df.base > 0).round(1)
shown = df[(df.base >= minvol) & df.continent.isin(pick)].copy()

rb, rr = info[f"baseline_{w}"], info[f"recent_{w}"]
st.markdown(f"Comparing **{rr[0]} to {rr[1]}** with **{rb[0]} to {rb[1]}**.")
tot_b, tot_r = int(df.base.sum()), int(df.recent.sum())
c1, c2, c3 = st.columns(3)
c1.metric("All ports, calls in the window", f"{tot_r:,}", f"{100 * (tot_r / tot_b - 1):+.1f}% vs a year earlier", delta_color="off")
c2.metric("Ports ranked", f"{len(shown):,}")
c3.metric("Ranked ports down / up", f"{int((shown.change < 0).sum())} / {int((shown.change > 0).sum())}")

st.subheader("Map")
if len(shown):
    m = shown.assign(radius=(shown.base.clip(lower=1) ** 0.5) * 2500, color=shown.change.map(lambda c: [213, 94, 0, 170] if c < 0 else [0, 114, 178, 170]))
    layer = pdk.Layer("ScatterplotLayer", m, get_position="[lon, lat]", get_radius="radius", get_fill_color="color", pickable=True, radius_min_pixels=2, radius_max_pixels=40)
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=20, longitude=30, zoom=1),
                             tooltip={"text": "{portname}, {country}\nbaseline {base} calls, recent {recent} ({change})"}), height=520)
    st.caption("Red: fewer calls than a year earlier. Blue: more. Circle size: baseline calls.")
else:
    st.info("No ports meet the current filters.")

st.subheader("Biggest changes in calls")
cols = ["portname", "country", "base", "recent", "change", "pct"]
a, b = st.columns(2)
a.markdown("**Biggest drops**"); a.dataframe(shown[shown.change < 0].nsmallest(10, "change")[cols], hide_index=True, width="stretch")
b.markdown("**Biggest gains**"); b.dataframe(shown[shown.change > 0].nlargest(10, "change")[cols], hide_index=True, width="stretch")
st.caption("Read percentages together with the change in calls: a large percentage on a small base can mislead.")

st.subheader("Gulf-region countries and the rest of the world")
rate = cm.pivot(index="month_start", columns="ISO3", values="calls_per_day")
g = [c for c in GULF if c in rate.columns]
ref = [m_ for m_ in rate.index if m_ <= pd.Timestamp("2026-02-01")]
if g and ref:
    gulf, rest = rate[g].sum(axis=1), rate.drop(columns=g).sum(axis=1)
    idx = pd.DataFrame({"Gulf-region countries": 100 * gulf / gulf.loc[ref].mean(), "Rest of the world": 100 * rest / rest.loc[ref].mean()})
    st.line_chart(idx, color=["#D55E00", "#555555"])
    st.caption("Calls per day, indexed so that the months up to February 2026 average 100. The Gulf grouping is by country and approximate: some of those countries have ports outside the Gulf.")

st.subheader("One port in detail")
opts = df.sort_values("base", ascending=False)
label = opts.portname + ", " + opts.country.fillna("") + " (" + opts.portid + ")"
choice = st.selectbox("Port", label.tolist())
pid = choice.rsplit("(", 1)[1].rstrip(")")
last = pd.Timestamp(info["last_day"])
try:
    d = port_daily(pid, str((last - pd.Timedelta(days=400)).date()))
    d["7-day average"] = d["portcalls"].rolling(7).mean()
    st.line_chart(d.set_index("date")[["7-day average"]], color=["#0072B2"])
    r_ = df[df.portid == pid].iloc[0]
    st.caption(f"{r_.portname}: {int(r_.recent)} calls in the latest {w} days against {int(r_.base)} a year earlier. The chart shows the last 400 days.")
except Exception as e:
    st.warning(f"Could not load daily data for this port right now ({e}).")

st.markdown("---")
st.markdown("Sources: UN Global Platform; IMF PortWatch. Method, notebooks and code: github.com/binary-cpu/port-tracker")
