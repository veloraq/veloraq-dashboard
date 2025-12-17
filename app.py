import streamlit as st
from api_manager import RealEstateAPI
import pandas as pd

# Page configuration for a professional dashboard look
st.set_page_config(page_title="VeloRaq: RE Investor", layout="wide")

# --- CUSTOM CSS FOR V0 LOOK ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #1f1f1f; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETTINGS ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/real-estate.png", width=80)
    st.title("VeloRaq Settings")
    
    with st.expander("🔑 API Credentials", expanded=True):
        apify_key = st.text_input("Apify Token", type="password")
        parcl_key = st.text_input("Parcl Key", type="password")
    
    with st.expander("🔎 Search Parameters", expanded=True):
        days_back = st.slider("Lookback Period (Days)", 1, 90, 30)
        zips_raw = st.text_area("Zip Codes (Comma separated)", "43081, 43211")
        zips = [z.strip() for z in zips_raw.split(',')]

    # Accurate Live Usage tracking
    st.divider()
    api = RealEstateAPI(apify_key=apify_key, parcl_key=parcl_key)
    if apify_key:
        usage = api.check_credits()
        st.metric("Apify Usage", f"${usage['apify']['used']:.2f}", delta_color="inverse")
        st.caption(f"Limit: $5.00 / Used: {usage['apify']['used']/5.0*100:.1f}%")

# --- MAIN DASHBOARD ---
st.title("🏙️ Columbus RE Investor")
st.caption("Active & Off-Market Property Intelligence")

# KPI Top Bar
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Target Markets", len(zips))
kpi2.metric("Scan Window", f"{days_back} Days")
kpi3.metric("Scraper Mode", "Waterfall (Z+R)")
kpi4.metric("Status", "Operational", delta="Live")

st.divider()

# Navigation Tabs
tab_active, tab_off = st.tabs(["🏡 On-Market Listings", "🕵️ Off-Market Hunter"])

with tab_active:
    st.header("Recently Listed in Ohio")
    
    # Header Action Row
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info(f"Scanning zips: {', '.join(zips)}")
    with col_btn:
        scan_triggered = st.button("🚀 Scan Real-Time Market", type="primary", use_container_width=True)

    if scan_triggered:
        with st.spinner("Executing multi-source waterfall scan..."):
            df = api.get_active_listings(zips, days_back)
            
            if not df.empty:
                st.success(f"Found {len(df)} properties available!")
                
                # Dynamic Grid Layout (3 cards per row)
                for i in range(0, len(df), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(df):
                            row = df.iloc[i + j]
                            with cols[j]:
                                # THE PROPERTY CARD
                                with st.container(border=True):
                                    # Visual Placeholder (Replicates v0 image look)
                                    st.image("https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=400", caption="Active Listing")
                                    
                                    # Price Formatting Guard
                                    try:
                                        p_val = float(row['Price'])
                                        display_price = f"${p_val:,.0f}"
                                    except:
                                        display_price = str(row['Price'])
                                    
                                    st.subheader(display_price)
                                    st.markdown(f"**📍 {row['Address']}**")
                                    st.caption(f"{row.get('City', 'Ohio')}, OH {row.get('Zip', '')}")
                                    
                                    # Specs Row
                                    s1, s2, s3 = st.columns(3)
                                    s1.write(f"🛏️ {row.get('Beds', '--')}")
                                    s2.write(f"🛁 {row.get('Baths', '--')}")
                                    s3.write(f"🏷️ {row.get('Source')}")
                                    
                                    st.divider()
                                    
                                    # Action Buttons
                                    st.link_button("🌐 Analyze on Zillow/Redfin", row['URL'], use_container_width=True)
                                    if st.button("📈 Run Deal Calc", key=f"calc_{i+j}", use_container_width=True):
                                        st.toast(f"Starting analysis for {row['Address']}")
            else:
                st.warning("No listings found. Try increasing the 'Lookback Period' in the sidebar.")

with tab_off:
    st.subheader("County GIS Off-Market Leads")
    if st.button("🕵️ Fetch High-Equity Leads"):
        with st.spinner("Querying County Parcel Records..."):
            off_df = api.get_off_market_leads(zips)
            if not off_df.empty:
                st.dataframe(off_df, use_container_width=True)
            else:
                st.info("No off-market leads found for these zips.")
