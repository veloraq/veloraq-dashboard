import requests
import pandas as pd
import streamlit as st
import credits

# --- A. FREE METHOD (County Data) ---
def get_county_leads(zips):
    leads = []
    
    # 1. SETUP PROGRESS BAR
    progress_text = "Starting County Scan..."
    my_bar = st.progress(0, text=progress_text)
    
    total_steps = len(zips)
    
    for i, zip_code in enumerate(zips):
        # Update Status
        my_bar.progress(int((i / total_steps) * 100), text=f"Scanning {zip_code} in County Database...")
        
        # FRANKLIN COUNTY
        try:
            f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
            params = {
                'where': f"ZIP_CODE='{zip_code}' AND LAST_SALE_YEAR<2015", 
                'outFields': 'SITE_ADDRESS,OWNER_NAME,LAST_SALE_YEAR', 
                'f': 'json', 
                'resultRecordCount': 20
            }
            res = requests.get(f_url, params=params, timeout=5)
            if res.status_code == 200:
                features = res.json().get('features', [])
                for f in features:
                    leads.append({
                        "Address": f['attributes'].get('SITE_ADDRESS'), 
                        "Owner": f['attributes'].get('OWNER_NAME'), 
                        "Zip": zip_code, 
                        "Source": "Franklin Co",
                        "Year": f['attributes'].get('LAST_SALE_YEAR')
                    })
        except Exception as e:
            st.error(f"⚠️ Error scanning Franklin Co for {zip_code}: {e}")

        # DELAWARE COUNTY
        try:
            d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
            params = {
                'where': f"PROP_ZIP='{zip_code}' AND SALEYEAR<2015", 
                'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 
                'f': 'json', 
                'resultRecordCount': 20
            }
            res = requests.get(d_url, params=params, timeout=5)
            if res.status_code == 200:
                features = res.json().get('features', [])
                for f in features:
                    leads.append({
                        "Address": f['attributes'].get('PROP_ADDR'), 
                        "Owner": f['attributes'].get('OWNER'), 
                        "Zip": zip_code, 
                        "Source": "Delaware Co",
                        "Year": f['attributes'].get('SALEYEAR')
                    })
        except Exception as e:
            st.error(f"⚠️ Error scanning Delaware Co for {zip_code}: {e}")

    my_bar.empty() # Clear bar when done
    return pd.DataFrame(leads)

# --- B. PAID METHOD (Parcl) ---
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
            # 1. Get ID
            res = requests.get("https://api.parcllabs.com/v1/search/markets", 
                             headers=headers, 
                             params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            data = res.json()
            if not data:
                st.warning(f"Skipping {zip_code}: Not found in Parcl DB.")
                continue
                
            pid = data[0]['parcl_id']
            
            # 2. Search Properties
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
                    "Year Built": p.get('year_built', 'N/A')
                })
        except Exception as e:
            st.error(f"Failed to fetch {zip_code}: {e}")

    my_bar.empty()
    return pd.DataFrame(leads)
