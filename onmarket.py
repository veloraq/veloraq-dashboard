import requests
import pandas as pd
from homeharvest import scrape_property
import streamlit as st
import credits # <--- The Banker

# --- A. PARCL MARKET STATS (PAID) ---
def get_market_stats(api_key, zip_code):
    """
    Gets Price Feeds & Housing Stock.
    COST: 1 Credit per lookup.
    """
    # 1. CHECK CREDIT
    try:
        credits.spend(1) # <--- PAY THE BANKER
    except Exception as e:
        st.error(str(e))
        return None

    headers = {"Authorization": api_key}
    stats = {}
    
    try:
        # Resolve ID
        res = requests.get("https://api.parcllabs.com/v1/search/markets", 
                         headers=headers, 
                         params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
        pid = res.json()[0]['parcl_id']
        
        # Get Stock
        res = requests.get(f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", headers=headers)
        latest = res.json().get('items', [])[0]
        
        stats['units'] = latest.get('housing_stock')
        stats['single_family'] = latest.get('single_family_units')
        stats['date'] = latest.get('date')
        
        return stats
    except:
        return None

# --- B. LISTING SCRAPER (FREE) ---
def get_listings(zip_list):
    """
    Scrapes Realtor.com.
    COST: 0 Credits.
    """
    all_homes = []
    for z in zip_list:
        try:
            homes = scrape_property(
                location=f"{z}, OH", 
                listing_type="for_sale", 
                past_days=7, 
                site_name=["realtor.com"]
            )
            if homes is not None and not homes.empty:
                homes['Zip'] = z
                # Keep only clean columns
                cols = ['street', 'list_price', 'days_on_mls', 'property_url', 'Zip']
                valid = [c for c in cols if c in homes.columns]
                all_homes.append(homes[valid])
        except: pass
        
    if all_homes:
        return pd.concat(all_homes, ignore_index=True)
    return pd.DataFrame()
