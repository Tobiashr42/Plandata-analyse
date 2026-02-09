from ..api import bbr
from ..api import plan
from shapely.geometry import shape
import geopandas as gpd
import pandas as pd
from shapely import wkt
from pathlib import Path


# ---------------------------------------------------------
# Projektstier
# ---------------------------------------------------------
# Øverst i alle scripts der skal gemme/læse filer
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# Hent plan
# ---------------------------------------------------------
komnr=101
plantype="LOKALPLAN"
status="VEDTAGET"
planid=1072539

print(f"Henter plan {planid}…")
plan_data = plan.hent_enkelt_plan(komnr, plantype, status, planid)

if not plan_data:
    raise RuntimeError("Ingen plan fundet")

plan_geom = shape(plan_data[0]["geometry"])
wkt_geometri = plan_geom.wkt

# ---------------------------------------------------------
# Hent bygninger (i status 6 og anvendelse under 900)
# ---------------------------------------------------------
bygninger_i_plan=bbr.hent_bygning(wkt_geometri)

# ---------------------------------------------------------
# gem fil
# ---------------------------------------------------------
df = pd.DataFrame(bygninger_i_plan)
df["wkt"] = df["byg404Koordinat"].apply(lambda x: x.get("wkt") if isinstance(x, dict) else None)
df["geometry"] = df["wkt"].apply(wkt.loads)
gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:25832")

filepath= RESULTS_DIR / f"bygninger_i_plan_{planid}.geojson"
gdf.to_file(filepath, driver="GeoJSON")