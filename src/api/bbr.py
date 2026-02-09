import http.client
import json
import time
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

# Load .env fra projektroden
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
dotenv_path = PROJECT_ROOT / "env" / ".env"
load_dotenv(dotenv_path)

def hent_bygning(geometri, tidspunkt=None):
    register = "BBR"                # fx BBR, DAR, DKDF osv.
    version = "v1"                    # fx v1
    api_key = os.getenv("BBR_API_KEY")
    if not api_key:
        raise RuntimeError("BBR_API_KEY mangler. Tjek din .env-fil.")
    conn = http.client.HTTPSConnection("graphql.datafordeler.dk")
    nu = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if tidspunkt is None:
        tidspunkt = nu
    all_nodes = []
    cursor = None
    side = 1

    while True:
        # Byg GraphQL-query (med/uden cursor)
        after_str = f', after: "{cursor}"' if cursor else ""

        # GraphQL som rigtig tekst, ikke escaped
        query = f"""
        query {{
        BBR_Bygning(
            first: 100
            virkningstid: "{tidspunkt}"
            registreringstid: "{nu}"
            where: {{
            status: {{eq: "6"}}
            byg021BygningensAnvendelse: {{in: [
            "110","120","121","122","130","131","132","140","150","160","185","190",
            "210","211","212","213","214","215","216","217","218","219",
            "220","221","222","223","229",
            "230","231","232","233","234","239","290",
            "310","311","312","313","314","315","319",
            "320","321","322","323","324","325","329",
            "330","331","332","333","334","339","390",
            "410","411","412","413","414","415","416","419",
            "420","421","422","429",
            "430","431","432","433","439",
            "440","441","442","443","444","449","451","490",
            "510","520","521","522","523","529",
            "530","531","532","533","534","535","539",
            "540","585","590"
            ]}}
            byg404Koordinat: {{
                intersects: {{
                crs: 25832
                wkt: "{geometri}"
                }}
            }}
            }}
            {after_str}
        ) {{
            pageInfo {{
            endCursor
            hasNextPage
            }}
            nodes {{
            id_lokalId
            byg404Koordinat{{wkt}}
            byg021BygningensAnvendelse
            husnummer
            registreringFra
            registreringTil
            virkningFra
            virkningTil
            status
            byg007Bygningsnummer
            byg024AntalLejlighederMedKoekken
            byg025AntalLejlighederUdenKoekken
            byg030Vandforsyning
            }}
        }}
        }}
        """
        payload = json.dumps({"query": query})
        headers = {"content-type": "application/json"}
        conn.request("POST", f"/{register}/{version}?apiKey={api_key}", payload, headers)
        res = conn.getresponse()
        raw_data = res.read()
        data = json.loads(raw_data.decode("utf-8"))

        bygninger = data.get("data", {}).get("BBR_Bygning", {}).get("nodes", [])
        pageinfo = data.get("data", {}).get("BBR_Bygning", {}).get("pageInfo", {})
        has_next = pageinfo.get("hasNextPage", False)
        cursor = pageinfo.get("endCursor", None)
        all_nodes.extend(bygninger)

        if not has_next:
            break
        side += 1
        time.sleep(0.5)
    conn.close()
    return all_nodes

# Eksempel på brug:
if __name__ == "__main__":
    hent_bygning("POLYGON((507269.454538909 6220414.46082892, 507305.574611149 6220539.06107812, 507470.77494155 6220525.9010518, 507433.33273166 6220424.33582511, 507384.047971257 6220421.36601678, 507269.454538909 6220414.46082892))")