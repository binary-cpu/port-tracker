# Port Tracker

Which ports gained or lost ship traffic compared with a year earlier, and where did the changes start?

**Live dashboard:** [https://port-tracker-ndbpex2rmrqv3pbbhxeb7u.streamlit.app/#port-tracker] (free hosting: it may take a moment to wake up)

**Data snapshot:** through 2026-10-09. Sources: UN Global Platform; IMF PortWatch (AIS-observed port calls at 2,065 ports, 2019 to 2026). The repo holds derived summaries only.

## What I found
- Across all ports, calls fell 4.9% between the latest 28 days and the same days a year earlier (139,526 to 132,708). Of 611 ports ranked (at least 50 baseline calls), 402 are down and 204 are up.
- The biggest drops by calls are Shanghai (-1,171), Jebel Ali (-594), Kerch (-438) and Khalifa Port (-230). The list of biggest drops is stable across window lengths and volume rules; the list of biggest gains is less stable.
- Gulf-region countries fell from 182 calls a day in February 2026 to 73 in March, and have stayed at 47% to 59% of their earlier level since April, while the rest of the world stayed within about 4%. Jebel Ali and Khalifa Port stepped down in March 2026.
- Year-ago comparisons can mislead: Mumbai-Jawaharlal Nehru's +160% is mostly a recovery from a trough, and Bandar-E Pars Terminal's -97% reflects bursts in the baseline window.
- In May 2026, India, Korea, the Philippines and Taiwan rose across nearly every ship type while China fell. I have not established why.

## Read this first
- Counts are AIS-observed, and ports are areas defined by the source.
- The Gulf pattern matches the timing of the Hormuz pattern in my chokepoint project, but both come from the same source and method, so this is not independent confirmation.
- The data show what changed, not why. No change is linked to a cause.
- Data lag by about a week; the dashboard is a snapshot refreshed by hand.

## How it was built
Notebooks: 01 data discovery and analysis, 02 map data preparation. Dashboard: `app.py` (Streamlit). Companion project: [chokepoint-tracker](https://github.com/binary-cpu/chokepoint-tracker).
