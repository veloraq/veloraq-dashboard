import streamlit as st
from api_manager import RealEstateAPI
import onmarket
import offmarket

st.set_page_config(page_title="VeloRaq", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    apify_key = st.text_input("Apify API Token", type="password")
    parcl_key = st.text_input("Parcl API Key", type="password")
    
    st.divider()
    st.subheader("🔎 Search Parameters")
    days_back = st.slider("Lookback Period (Days)", 1, 90, 7)
    zips = [z.strip() for z in st.text_area("Zip Codes", "43081, 43211").split(',')]
    
    # 💳 NEW LIVE CREDIT TRACKER
    st.divider()
    st.subheader("💳 Live Usage")
    
    # Initialize API
    api = RealEstateAPI(apify_key=apify_key, parcl_key=parcl_key)
    
    if apify_key or parcl_key:
        if st.button("🔄 Refresh Credits"):
            st.cache_data.clear() # Clear cache to fetch fresh data
            
        status = api.check_credits()
        
        # Apify Gauge
        if apify_key:
            used = status["apify"]["used"]
            limit = status["apify"]["limit"]
            st.caption(f"Apify (Scraper): ${used:.2f} / ${limit:.2f}")
            st.progress(min(used / limit, 1.0))
        
        # Parcl Gauge
        if parcl_key:
            left = status["parcl"]["remaining"]
            st.caption(f"Parcl (Stats): {left} credits left")
            # Simple bar (assuming 1000 is default start)
            st.progress(min(left / 1000, 1.0))
    else:
        st.info("Enter keys to see credit usage.")

st.title("🚲 VeloRaq: Real Estate Command Center")

tab1, tab2 = st.tabs(["🕵️ Off-Market Hunter", "🏡 Active Listings"])

with tab1:
    offmarket.render_off_market(api, zips)

with tab2:
    st.subheader("Active Market Data")
    col1, col2 = st.columns([1, 3])
    with col1: onmarket.render_market_stats(api, zips)
    with col2: onmarket.render_active_listings(api, zips, days_back)
