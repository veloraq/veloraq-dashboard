import requests
import pandas as pd
from homeharvest import scrape_property
import streamlit as st
import credits

# --- A. MARKET STATS ---
def get_market_stats(api_key, zip_code):
    try:
        credits.spend(1)
    except Exception as e:
        st.error(str(e))
        return None

    headers = {"Authorization": api_key}
    stats = {}
    
    try:
        # We don't need a progress bar for a single API call, but we handle errors strictly
        res = requests.get(
            "https://api.parcllabs.com/v1/search/markets", 
            headers=headers, 
            params={"query": zip_code, "location_type": "ZIP5", "limit": 1}
        )
        
        if res.status_code != 200:
            st.error(f"API Error {res.status_code}: {res.text}")
            return None
            
        data = res.json()
        if not data:
            st.error(f"Zip {zip_code} not found.")
            return None
            
        pid = data[0]['parcl_id']
        
        res_stats = requests.get(f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", headers=headers)
        items = res_stats.json().get('items', [])
        
        if items:
            latest = items[0]
            stats['units'] = latest.get('housing_stock')
            stats['single_family'] = latest.get('single_family_units')
            stats['date'] = latest.get('date')
            return stats
        else:
            st.warning("No housing data available for this location.")
            return None

    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# --- B. LISTING SCRAPER ---
def get_listings(zip_list, days_back=7):
    """
    Scrapes Realtor.com. 
    days_back: Int controlled by the Sidebar Slider.
    """
    all_homes = []
    
    # Progress Bar for Scraping
    progress_text = "Connecting to Realtor.com..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, z in enumerate(zip_list):
        my_bar.progress(int((i / len(zip_list)) * 100), text=f"Scraping active listings in {z}...")
        
        try:
            # We use the 'days_back' variable here
            homes = scrape_property(
                location=f"{z}, OH", 
                listing_type="for_sale", 
                past_days=days_back,  # <--- DYNAMIC LOOKBACK
                site_name=["realtor.com"]
            )
            
            if homes is not None and not homes.empty:
                homes['Zip'] = z
                # Clean Columns
                cols = ['street', 'city', 'list_price', 'days_on_mls', 'property_url', 'Zip']
                valid = [c for c in cols if c in homes.columns]
                all_homes.append(homes[valid])
                
        except Exception as e:
            # We print a small warning but don't stop the whole process
            st.warning(f"Could not scrape {z}: {e}")
            
    my_bar.empty()
    
    if all_homes:
        return pd.concat(all_homes, ignore_index=True)
    return pd.DataFrame()
