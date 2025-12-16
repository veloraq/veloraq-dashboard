import streamlit as st
import pandas as pd
import requests
from homeharvest import scrape_property
import time

# --- APP CONFIGURATION ---
st.set_page_config(page_title="VeloRaq Dashboard", layout="wide")
st.title("🚲 VeloRaq: AI Real Estate Hunter")
st.markdown("Automated Deal Finding for **Columbus & Central Ohio**")

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("Search Settings")
    target_zips = st.text_area("Target Zip Codes (comma separated)", "43081, 43035, 43211, 43085")
    # Convert string input to list
    ZIP_LIST = [z.strip() for z in target_zips.split(',')]
    
    st.divider()
    st.info(f"Targeting {len(ZIP_LIST)} Zip Codes")

# --- ENGINE 1: OFF-MARKET (County Data) ---
def get_off_market_leads(zips):
    leads = []
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    for i, zip_code in enumerate(zips):
        status_text.text(f"Scanning {zip_code} in County Records...")
        progress_bar.progress((i + 1) / len(zips))
        
        # FRANKLIN COUNTY
        f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
        f_params = {
            'where': f"ZIP_CODE = '{zip_code}' AND LAST_SALE_YEAR < 2015 AND LAST_SALE_PRICE > 0",
            'outFields': 'SITE_ADDRESS,OWNER_NAME,LAST_SALE_YEAR,MAIL_ZIP',
            'f': 'json',
            'resultRecordCount': 20
        }
        try:
            res = requests.get(f_url, params=f_params)
            data = res.json()
            features = data.get('features', [])
            for f in features:
                attr = f['attributes']
                leads.append({
                    "Address": attr['SITE_ADDRESS'],
                    "Owner": attr['OWNER_NAME'],
                    "Zip": zip_code,
                    "Strategy": "Off-Market (Long Term Owner)",
                    "Year Bought": attr['LAST_SALE_YEAR']
                })
        except:
            pass

        # DELAWARE COUNTY
        d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
        d_params = {
            'where': f"PROP_ZIP = '{zip_code}' AND SALEYEAR < 2015",
            'outFields': 'PROP_ADDR,OWNER,SALEYEAR',
            'f': 'json',
            'resultRecordCount': 20
        }
        try:
            res = requests.get(d_url, params=d_params)
            data = res.json()
            features = data.get('features', [])
            for f in features:
                attr = f['attributes']
                leads.append({
                    "Address": attr['PROP_ADDR'],
                    "Owner": attr['OWNER'],
                    "Zip": zip_code,
                    "Strategy": "Off-Market (Delaware)",
                    "Year Bought": attr['SALEYEAR']
                })
        except:
            pass

    status_text.text("Scan Complete!")
    return pd.DataFrame(leads)

# --- ENGINE 2: ON-MARKET (Zillow/Realtor) ---
def get_on_market_leads(zips):
    all_homes = []
    status_text = st.empty()
    progress_bar = st.progress(0)

    for i, zip_code in enumerate(zips):
        status_text.text(f"Scraping Zillow/Realtor for {zip_code}...")
        progress_bar.progress((i + 1) / len(zips))
        
        try:
            homes = scrape_property(
                location=f"{zip_code}, OH",
                listing_type="for_sale",
                past_days=7,
                # Using general arguments to catch 'site_name' or 'source' automatically handled by library updates
            )
            if homes is not None and not homes.empty:
                # Keep relevant columns
                cols = ['street', 'city', 'list_price', 'days_on_mls', 'property_url']
                valid_cols = [c for c in cols if c in homes.columns]
                homes = homes[valid_cols]
                homes['Zip'] = zip_code
                all_homes.append(homes)
        except Exception as e:
            st.warning(f"Skipped {zip_code}: {e}")
            
    if all_homes:
        return pd.concat(all_homes, ignore_index=True)
    return pd.DataFrame()

# --- DASHBOARD LAYOUT ---
tab1, tab2 = st.tabs(["🕵️ Off-Market Deals", "🏡 New Listings (7 Days)"])

with tab1:
    st.subheader("Find Hidden Deals (County Data)")
    if st.button("Run Off-Market Scan", type="primary"):
        df_off = get_off_market_leads(ZIP_LIST)
        if not df_off.empty:
            st.success(f"Found {len(df_off)} Off-Market Leads!")
            st.dataframe(df_off)
            st.download_button("Download CSV", df_off.to_csv(index=False), "off_market.csv")
        else:
            st.warning("No leads found. Try different zip codes.")

with tab2:
    st.subheader("Find Active Listings (Zillow/Realtor)")
    if st.button("Run Listing Scraper"):
        df_on = get_on_market_leads(ZIP_LIST)
        if not df_on.empty:
            st.success(f"Found {len(df_on)} New Listings!")
            st.dataframe(df_on)
            st.download_button("Download CSV", df_on.to_csv(index=False), "on_market.csv")
        else:
            st.warning("No new listings found in last 7 days.")
