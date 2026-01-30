import requests
import json
import geopandas as gpd
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------
# Projektstier
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)  # sørg for at data-mappen findes

plantyper = ["KOMMUNEPLANRAMME"]
#["LOKALPLAN","LOKALPLANDELOMRAADE", "BYGGEFELT", "KOMMUNEPLANRAMME", "LANDZONETILLADELSE"]

statusmuligheder = ["AFLYST"]
#["FORSLAG", "VEDTAGET", "AFLYST"]

# ---------------------------------------------------------
# Funktion: Hent planer for én kommune
# ---------------------------------------------------------
def hent_planer_for_kommune(komnr, plantype="LOKALPLAN", status="", planid=""):
    """
    Henter planer for en enkelt kommune via Plandata API.
    Returnerer en liste af GeoJSON-lignende features.
    """
    features = []
    page = 1
    if not planid:
        planid_url=""
    else:
        planid_url=f"&planId={planid}"
    
    if not status:
        status_url=""
    else:
        status_url=f"&planstatus={status}"


    while True:
        api_url = (
            "https://indberet.plandata.dk/plandata-api/offentlig/"
            f"hentOffentligePlaner?kommunekode={komnr}&plantype={plantype}{status_url}{planid_url}&page={page}"
        )

        response = requests.get(api_url)

        if response.status_code != 200:
            print(f"❌ API-fejl for kommune {komnr}: {response.status_code}")
            break

        json_pagination = response.json()["pagination"]
        pagecount= json_pagination["pageCount"]
        
        if pagecount>1:
            print(f"Henter side {page} af {pagecount} for kommune {komnr}")

        try:
            json_data = response.json()["data"]
            for item in json_data:
                if item.get("geometri"):
                    try:
                        geometry = json.loads(item["geometri"])
                        #kopi af properties
                        props = item.copy()
                        #Fjern Geometri-felt
                        props.pop("geometri", None)
                        #Fjern Projection-felt
                        props.pop("projection", None)
                        feature = {
                            "type": "Feature",
                            "geometry": geometry,
                            "properties": props,
                        }
                        features.append(feature)
                    except Exception as e:
                        print(f"⚠️ Fejl ved parsing af geometri i kommune {komnr}: {e}")
        except Exception as e:
            print(f"❌ Fejl ved behandling af JSON for kommune {komnr}: {e}")
        
        if page >= pagecount:
            break

        page += 1
    
    print(f"✅ Færdig med kommune {komnr}: {len(features)} features i alt")
    return features


# ---------------------------------------------------------
# Funktion: Hent planer for flere kommuner
# ---------------------------------------------------------
def hent_alle_planer(kommuner, plantype, status):
    """
    Løber igennem en liste af kommunekoder.
    Returnerer én samlet liste af features.
    """
    alle_features = []
    for komnr in kommuner:
        kommune_features = hent_planer_for_kommune(komnr, plantype, status)
        alle_features.extend(kommune_features)

    print(f"📊 Samlet antal features: {len(alle_features)}")
    return alle_features


# ---------------------------------------------------------
# Funktion: Lav FeatureCollection
# ---------------------------------------------------------
def lav_geojson(features):
    """Pakker features ind i en FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": features,
    }

# ---------------------------------------------------------
# Funktion: Skriv log
# ---------------------------------------------------------

def skriv_log(filnavn, antal_features):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    logpath = DATA_DIR / "log.txt"
    with open(logpath, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} – Opdaterede {filnavn} med {antal_features} features\n")
    
    print(f"📝 Log: {filnavn} opdateret ({antal_features} features)")

# ---------------------------------------------------------
# Funktion: Gem som GeoJSON
# ---------------------------------------------------------
def gem_geojson(geojson_data, plantype, status="alle", planid=""):
    #CRS sættes til 25832 (som det er i filen)
    gdf_utm = gpd.GeoDataFrame.from_features(geojson_data["features"])
    gdf_utm = gdf_utm.set_crs(25832)

    # Lav WGS84 version
    gdf_wgs = gdf_utm.to_crs(4326)

    #begge versioner gemmes
    filnavn_utm = f"{plantype.lower()}_{status.lower()}_{planid}_utm.geojson"
    filnavn_wgs = f"{plantype.lower()}_{status.lower()}_{planid}_wgs.geojson"
    
    filepath_utm = DATA_DIR / filnavn_utm
    filepath_wgs = DATA_DIR / filnavn_wgs

    gdf_utm.to_file(filepath_utm, driver="GeoJSON")
    gdf_wgs.to_file(filepath_wgs, driver="GeoJSON")
    
    #Det markeres i loggen at filen er gemt
    skriv_log(filnavn_utm, len(geojson_data["features"]))
    skriv_log(filnavn_wgs, len(geojson_data["features"]))

# ---------------------------------------------------------
# Funktion: Normalkørsel
# ---------------------------------------------------------
def hent_plantype(kommuner, plantype, status, gem=False):
    if plantype not in plantyper:
        plantype = "LOKALPLAN"

    if status not in statusmuligheder:
        status = "VEDTAGET"

    allekommuner = [
        101,147,151,153,155,157,159,161,163,165,167,169,173,175,
        183,185,187,190,201,210,217,219,223,230,240,250,253,259,
        260,265,269,270,306,316,320,326,329,330,336,340,350,360,
        370,376,390,400,410,420,430,440,450,461,479,480,482,492,
        510,530,540,550,561,563,573,575,580,607,615,621,630,657,
        661,665,671,706,707,710,727,730,740,741,746,751,756,760,
        766,773,779,787,791,810,813,820,825,840,846,849,851,860
    ]

    if isinstance(kommuner, int):
        kommuner = [kommuner]
    elif isinstance(kommuner, (list, tuple)) and len(kommuner) > 0:
        kommuner = list(kommuner)
    else:
        kommuner = allekommuner

    print(f"Henter planer af typen {plantype.lower()} i status {status.lower()}")

    features = hent_alle_planer(kommuner, plantype, status)
    
    if gem==False:
        return features
    else:
        geojson_data = lav_geojson(features)
        gem_geojson(geojson_data, plantype, status)



# ---------------------------------------------------------
# Funktion: Totalkørsel
# ---------------------------------------------------------

def hent_alle_plantyper():
    kommuner = None
    gem=True
    print("🚀 Henter alle typer planer for alle statusser ...")
    for plantype in plantyper:
        for status in statusmuligheder:  
            hent_plantype(kommuner,plantype,status,gem)

# ---------------------------------------------------------
# Funktion: Hent enkelt plan
# ---------------------------------------------------------
def hent_enkelt_plan(komnr, plantype, status, planid, gem=False):

    features = hent_planer_for_kommune(komnr, plantype, status, planid)
    if gem==False:
        return features
    else:
        geojson_data = lav_geojson(features)
        gem_geojson(geojson_data, plantype, status, planid)

# ---------------------------------------------------------
# Start scriptet hvis filen køres direkte
# ---------------------------------------------------------

if __name__ == "__main__":
    hent_alle_plantyper()
