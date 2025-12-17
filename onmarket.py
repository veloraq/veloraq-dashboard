import requests
import pandas as pd
from homeharvest import scrape_property
import streamlit as st
import credits

# --- A. MARKET STATS (PAID - PARCL) ---
def get_market_stats(api_key, zip_code):
    try:
        credits.spend(1)
    except Exception as e:
        st.error(str(e))
        return None

    headers = {"Authorization": api_key}
    stats = {}
    
    try:
        # 1. Resolve Zip to ID
        res = requests.get(
            "https://api.parcllabs.com/v1/search/markets", 
            headers=headers, 
            params={"query": zip_code, "location_type": "ZIP5", "limit": 1}
        )
        
        if res.status_code != 200:
            st.error(f"API Error {res.status_code}")
            return None
            
        data = res.json()
        items_list = data.get('items', []) if isinstance(data, dict) else data
        
        if not items_list:
            st.warning(f"Zip {zip_code} not found in Parcl DB.")
            return None
            
        pid = items_list[0]['parcl_id']
        
        # 2. Fetch Metrics (Housing Stock)
        res_stats = requests.get(f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", headers=headers)
        
        if res_stats.status_code != 200: return None
            
        stock_data = res_stats.json()
        stock_items = stock_data.get('items', []) if isinstance(stock_data, dict) else stock_data
        
        if stock_items:
            latest = stock_items[0]
            
            # 🛠️ FIX: Mapped to correct API keys from your diagnostic
            total = latest.get('all_properties') or 0
            sf = latest.get('single_family') or 0
            
            # Calculate "Other" (Condos + Townhomes + Multi)
            other = total - sf
            
            stats['units'] = total
            stats['single_family'] = sf
            stats['other'] = other
            stats['date'] = latest.get('date')
            return stats
        else:
            return {'units': 0, 'single_family': 0, 'other': 0, 'date': 'N/A'}

    except Exception as e:
        st.error(f"Connection failed: {e}")
        return None

# --- B. LISTING SCRAPER (Safe Mode) ---
def get_listings(zip_list, days_back=7):
    """
    Scrapes active listings with error protection.
    """
    all_homes = []
    
    # Progress Bar
    progress_text = "Connecting to listing service..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, z in enumerate(zip_list):
        my_bar.progress(int((i / len(zip_list)) * 100), text=f"Scraping {z}...")
        
        try:
            # 🛡️ PROTECTION: We try to scrape, but catch the Auth Error if blocked
            homes = scrape_property(
                location=f"{z}, OH", 
                listing_type="for_sale", 
                past_days=days_back
            )
            
            if homes is not None and not homes.empty:
                desired_cols = ['street', 'city', 'list_price', 'days_on_mls', 'property_url']
                valid_cols = [c for c in desired_cols if c in homes.columns]
                
                clean_homes = homes[valid_cols].copy()
                clean_homes['Zip'] = z
                all_homes.append(clean_homes)
        
        except Exception as e:
            # Check for that specific AuthenticationError
            err_msg = str(e)
            if "AuthenticationError" in err_msg or "403" in err_msg:
                st.warning(f"⚠️ Access to listings for {z} was blocked by the provider. (Try running locally).")
            else:
                st.warning(f"Could not scrape {z}: {e}")
            
    my_bar.empty()
    
    if all_homes:
        return pd.concat(all_homes, ignore_index=True)
    return pd.DataFrame()
