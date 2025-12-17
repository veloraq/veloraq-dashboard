import streamlit as st
from api_manager import RealEstateAPI
import pandas as pd

st.set_page_config(page_title="VeloRaq: Real Estate Command Center", layout="wide")

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    apify_key = st.text_input("Apify API Token", type="password")
    parcl_key = st.text_input("Parcl API Key", type="password")
    
    st.divider()
    st.subheader("🔎 Search Parameters")
    days_back = st.slider("Lookback Period (Days)", 1, 90, 30) # Default to 30 for better results
    zips_raw = st.text_input("Zip Codes", "43081, 43211")
    zips = [z.strip() for z in zips_raw.split(',')]
    
    # Live Usage Section
    st.divider()
    api = RealEstateAPI(apify_key=apify_key, parcl_key=parcl_key)
    if apify_key:
        usage = api.check_credits()
        st.write(f"💳 **Apify Usage:** ${usage['apify']['used']:.2f} / $5.00")
        st.progress(min(usage['apify']['used'] / 5.0, 1.0))

st.title("🚲 VeloRaq: Real Estate Command Center")

# --- TABS ---
tab1, tab2 = st.tabs(["🕵️ Off-Market Hunter", "🏡 Active Listings"])

with tab2:
    st.subheader("Active Market Data")
    
    # Action Buttons
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        scan_clicked = st.button("🚀 Scan Market", type="primary", use_container_width=True)
    
    if scan_clicked:
        with st.spinner("Executing Zillow-Redfin Waterfall Scan..."):
            df = api.get_active_listings(zips, days_back)
            
            if not df.empty:
                st.success(f"Found {len(df)} properties in Ohio!")
                
                # 🛠️ GRID SYSTEM (3 Cards per Row)
                rows = (len(df) // 3) + 1
                for r in range(rows):
                    cols = st.columns(3)
                    for c in range(3):
                        index = r * 3 + c
                        if index < len(df):
                            row = df.iloc[index]
                            with cols[c]:
                                # THE CARD
                                with st.container(border=True):
                                    # Placeholder for Property Image (replicates v0 mockup)
                                    st.image("https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&q=80&w=400", use_container_width=True)
                                    
                                    # Pricing & Status
                                    st.markdown(f"### ${row['Price']:,}")
                                    st.caption(f"📍 {row['Address']}, {row['City']}, OH")
                                    
                                    # Property Details Row
                                    d1, d2, d3 = st.columns(3)
                                    d1.write(f"🛏️ {row.get('Beds', 'N/A')} Bed")
                                    d2.write(f"🛁 {row.get('Baths', 'N/A')} Bath")
                                    d3.write(f"🏠 {row.get('Source')}")
                                    
                                    st.divider()
                                    
                                    # Investment Actions
                                    if st.button("📈 Analyze Investment", key=f"inv_{index}", use_container_width=True):
                                        st.info(f"Opening calculation for {row['Address']}...")
                                    
                                    st.link_button("🌐 View on Web", row['URL'], use_container_width=True)
            else:
                st.warning("No listings found. Try increasing the Lookback Period.")
