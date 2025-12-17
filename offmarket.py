import requests
import pandas as pd
import streamlit as st
import credits  # <--- The Banker

# --- A. FREE METHOD (County Data) ---
def get_county_leads(zips):
    """
    Scans Franklin/Delaware GIS. 
    COST: 0 Credits.
    """
    leads = []
    my_bar = st.progress(0, text="Scanning County Records (Free)...")
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / len(zips)) * 100))
        
        # 1. FRANKLIN COUNTY
        try:
            f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
            params = {
                'where': f"ZIP_CODE='{zip_code}' AND LAST_SALE_YEAR<2015", 
                'outFields': 'SITE_ADDRESS,OWNER_NAME,LAST_SALE_YEAR', 
                'f': 'json', 
                'resultRecordCount': 15
            }
            res = requests.get(f_url, params=params, timeout=3)
            if res.status_code == 200:
                for f in res.json().get('features', []):
                    leads.append({
                        "Address": f['attributes']['SITE_ADDRESS'], 
                        "Owner": f['attributes']['OWNER_NAME'], 
                        "Zip": zip_code, 
                        "Source": "Franklin Co",
                        "Year": f['attributes']['LAST_SALE_YEAR']
                    })
        except: pass

        # 2. DELAWARE COUNTY
        try:
            d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
            params = {
                'where': f"PROP_ZIP='{zip_code}' AND SALEYEAR<2015", 
                'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 
                'f': 'json', 
                'resultRecordCount': 15
            }
            res = requests.get(d_url, params=params, timeout=3)
            if res.status_code == 200:
                for f in res.json().get('features', []):
                    leads.append({
                        "Address": f['attributes']['PROP_ADDR'], 
                        "Owner": f['attributes']['OWNER'], 
                        "Zip": zip_code, 
                        "Source": "Delaware Co",
                        "Year": f['attributes']['SALEYEAR']
                    })
        except: pass

    my_bar.empty()
    return pd.DataFrame(leads)

# --- B. PAID METHOD (Parcl Database) ---
def get_parcl_leads(zips, api_key):
    """
    Uses Parcl to find homes in rural areas (e.g. Hocking).
    COST: 10 Credits per Zip Code.
    """
    # 1. CALCULATE & CHECK CREDITS
    cost_per_zip = 10
    total_cost = len(zips) * cost_per_zip
    
    try:
        credits.spend(total_cost) # <--- PAY THE BANKER
        st.toast(f"💳 {total_cost} Credits deducted.")
    except Exception as e:
        st.error(str(e))
        return pd.DataFrame()

    # 2. RUN SEARCH
    leads = []
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    my_bar = st.progress(0, text="Querying Parcl Database...")
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / len(zips)) * 100))
        
        # Get ID
        pid = None
        try:
            res = requests.get("https://api.parcllabs.com/v1/search/markets", 
                             headers=headers, 
                             params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            pid = res.json()[0]['parcl_id']
        except: continue
        
        # Search Properties (Limit 10)
        try:
            url = "https://api.parcllabs.com/v2/property/search"
            payload = {
                "parcl_ids": [pid],
                "property_filters": {"property_types": ["SINGLE_FAMILY"]},
                "limit": 10
            }
            res = requests.post(url, headers=headers, json=payload)
            items = res.json().get('items', [])
            
            for item in items:
                p = item.get('property_metadata', {})
                address = f"{p.get('address1')}, {p.get('city')}"
                leads.append({
                    "Address": address,
                    "Owner": "Parcl Record",
                    "Zip": zip_code,
                    "Source": "Parcl API",
                    "Year": p.get('year_built', 'N/A')
                })
        except: pass

    my_bar.empty()
    return pd.DataFrame(leads)
