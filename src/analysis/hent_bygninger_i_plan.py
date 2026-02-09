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
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)  # sørg for at data-mappen findes

# ---------------------------------------------------------
# Hent plan
# ---------------------------------------------------------
komnr=101
plantype="LOKALPLAN"
status="VEDTAGET"
planid=1072539
plan=plan.hent_enkelt_plan(komnr,plantype,status,planid)[0]
geometri=shape(plan["geometry"])
wkt_geometri=geometri.wkt
#print(wkt_geometri)

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

filepath= DATA_DIR / f"bygninger_{planid}.geojson"
gdf.to_file(filepath, driver="GeoJSON")