import streamlit as st
from streamlit_folium import st_folium
import folium
import geopandas as gpd
from pathlib import Path

st.sidebar.header("Vælg datalag")

plantype = st.sidebar.selectbox(
    "Hvilken plantype vil du se?",
    options=["lokalplan", "lokalplandelomraade"],
    index=0
)
status = st.sidebar.selectbox(
    "Hvilken plantype vil du se?",
    options=["forslag", "vedtaget","aflyst"],
    index=0
)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / f"{plantype}_{status}_wgs.geojson"

st.title("Dashboard")

# Load data
@st.cache_data
def load_data(path):
    return gpd.read_file(path)

gdf = load_data(DATA_FILE)

st.subheader("Dataoversigt")

st.write(f"Antal planer: {len(gdf)}")
if plantype=="lokalplan":
    st.dataframe(gdf[["plannavn", "plannummer", "kommunekode"]])
elif plantype=="lokalplandelomraade":
    st.dataframe(gdf[["delnummer", "kommunekode"]])
else:
    st.dataframe(gdf[["plannavn", "plannummer", "kommunekode"]])

# ---------------------------------------------------------
# Konverter ALLE kolonner undtagen geometry til string
# Dette gør alle værdier json-serializable og Folium-venlige
# ---------------------------------------------------------
for col in gdf.columns:
    if col != "geometry":
        gdf[col] = gdf[col].astype(str)


# Folium-kort
st.subheader("Kort over lokalplaner i forslag")

# Start kort centralt i DK
m = folium.Map(location=[56.0, 10.0], zoom_start=7, tiles="OpenStreetMap")

# Tilføj polygoner
if plantype=="lokalplan":
    folium.GeoJson(
    gdf,
    name="Lokalplaner",
    tooltip=folium.GeoJsonTooltip(fields=["plannavn", "plannummer", "kommunekode"]),
).add_to(m)
elif plantype=="lokalplandelomraade":
    folium.GeoJson(
    gdf,
    name="Lokalplaner",
    tooltip=folium.GeoJsonTooltip(fields=["delnummer", "kommunekode"]),
).add_to(m)
else:
    st.dataframe(gdf[["plannavn", "plannummer", "kommunekode"]])

# Vis kortet i Streamlit
st_folium(m, width=800, height=500)
