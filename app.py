import streamlit as st
from api_manager import RealEstateAPI
import onmarket
import offmarket
import credits

st.set_page_config(page_title="VeloRaq", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 🔑 NEW INPUT: Apify Key
    apify_key = st.text_input("Apify API Token", type="password", help="Required for Active Listings")
    parcl_key = st.text_input("Parcl API Key", type="password", help="Required for Market Stats")
    
    st.divider()
    st.subheader("🔎 Search Parameters")
    days_back = st.slider("Lookback Period (Days)", 1, 90, 7)
    st.divider()
    zips_input = st.text_area("Zip Codes", "43081, 43211")
    zips = [z.strip() for z in zips_input.split(',')]
    
    st.divider()
    used, limit = credits.get_status()
    st.metric("Credits Used", f"{used} / {limit}")
    if st.button("Reset Counter"):
        credits.reset()
        st.rerun()

st.title("🚲 VeloRaq: Real Estate Command Center")

# --- INITIALIZE API MANAGER ---
# The app creates one manager instance and passes it everywhere
api = RealEstateAPI(apify_key=apify_key, parcl_key=parcl_key)

tab1, tab2 = st.tabs(["🕵️ Off-Market Hunter", "🏡 Active Listings"])

with tab1:
    offmarket.render_off_market(api, zips)

with tab2:
    st.subheader("Active Market Data")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        onmarket.render_market_stats(api, zips)
    with col2:
        onmarket.render_active_listings(api, zips, days_back)
