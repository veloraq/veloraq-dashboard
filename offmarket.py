import requests
import pandas as pd
import streamlit as st
import credits
import json

# --- A. FREE METHOD (County Data) ---
def get_county_leads(zips):
    leads = []
    progress_text = "Starting County Scan..."
    my_bar = st.progress(0, text=progress_text)
    total_steps = len(zips)
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / total_steps) * 100), text=f"Scanning {zip_code}...")
        
        # 1. FRANKLIN COUNTY
        try:
            f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
            params = {
                'where': f"ZIPCD='{zip_code}' AND SALEDATE < '2015-01-01' AND SALEDATE IS NOT NULL", 
                'outFields': 'SITEADDRESS,OWNERNME1,SALEDATE,ZIPCD', 
                'f': 'json', 
                'resultRecordCount': 25
            }
            res = requests.get(f_url, params=params, timeout=5)
            if res.status_code == 200:
                features = res.json().get('features', [])
                for f in features:
                    attr = f['attributes']
                    leads.append({
                        "Address": attr.get('SITEADDRESS'), 
                        "Owner": attr.get('OWNERNME1'), 
                        "Zip": attr.get('ZIPCD'), 
                        "Source": "Franklin Co (Free)",
                        "Strategy": "High Equity"
                    })
        except: pass

        # 2. DELAWARE COUNTY (Fast Fail)
        try:
            d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
            params = {
                'where': f"PROP_ZIP='{zip_code}' AND SALEYEAR<2015", 
                'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 
                'f': 'json', 
                'resultRecordCount': 10
            }
            res = requests.get(d_url, params=params, timeout=2)
            if res.status_code == 200:
                features = res.json().get('features', [])
                for f in features:
                    leads.append({
                        "Address": f['attributes'].get('PROP_ADDR'), 
                        "Owner": f['attributes'].get('OWNER'), 
                        "Zip": zip_code, 
                        "Source": "Delaware Co (Free)",
                        "Strategy": "High Equity"
                    })
        except: pass

    my_bar.empty()
    return pd.DataFrame(leads)

# --- B. PAID METHOD (Parcl Database) ---
def get_parcl_leads(zips, api_key):
    cost = len(zips) * 10
    try:
        credits.spend(cost)
        st.toast(f"💳 Approved: {cost} credits used.")
    except Exception as e:
        st.error(str(e))
        return pd.DataFrame()

    leads = []
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    my_bar = st.progress(0, text="Initializing Parcl...")
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / len(zips)) * 100), text=f"Querying Parcl for {zip_code}...")
        
        try:
            # 1. GET ID
            res = requests.get("https://api.parcllabs.com/v1/search/markets", headers=headers, params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            
            if res.status_code != 200: continue
            data = res.json()
            items_list = data.get('items', [])
            if not items_list: continue
            pid = items_list[0]['parcl_id']
            
            # 2. SEARCH PROPERTIES (Corrected URL & Payload)
            url = "https://api.parcllabs.com/v2/property_search"  # <--- FIXED URL
            
            # BODY: Only contains filters
            payload = {
                "parcl_ids": [pid],
                "property_filters": {"property_types": ["SINGLE_FAMILY"]}
            }
            
            # URL PARAMS: Contains limits/pagination
            query_params = {
                "limit": 10,  # <--- MOVED HERE
                "offset": 0
            }
            
            res = requests.post(url, headers=headers, json=payload, params=query_params)
            
            if res.status_code != 200:
                st.warning(f"Parcl Error {res.status_code}: {res.text}")
                continue

            items = res.json().get('items', [])
            for item in items:
                p = item.get('property_metadata', {})
                address = f"{p.get('address1')}, {p.get('city')}"
                leads.append({
                    "Address": address,
                    "Owner": "Parcl Record",
                    "Zip": zip_code,
                    "Source": "Parcl API",
                    "Year Built": p.get('year_built', 'N/A')
                })
        except Exception as e:
            st.error(f"Error on {zip_code}: {e}")

    my_bar.empty()
    return pd.DataFrame(leads)
