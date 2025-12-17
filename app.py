import streamlit as st
import pandas as pd
import offmarket
import onmarket
import credits

st.set_page_config(page_title="VeloRaq", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. API KEYS
    parcl_key = st.text_input("Parcl API Key", type="password")
    
    st.divider()
    
    # 2. LISTING FILTERS (New!)
    st.subheader("🔎 Search Parameters")
    days_back = st.slider("Lookback Period (Days)", min_value=1, max_value=90, value=7, help="How far back to search for new/updated listings.")
    
    st.divider()

    # 3. ZIP CODES
    st.caption("Target Markets")
    zips_input = st.text_area("Zip Codes (Comma Separated)", "43081, 43211")
    zips = [z.strip() for z in zips_input.split(',')]
    
    st.divider()
    
    # 4. CREDITS
    used, limit = credits.get_status()
    st.metric("Credits Used", f"{used} / {limit}")
    if st.button("Reset Counter"):
        credits.reset()
        st.rerun()

st.title("🚲 VeloRaq: Real Estate Command Center")

tab1, tab2 = st.tabs(["🕵️ Off-Market Hunter", "🏡 Active Listings"])

# --- TAB 1: OFF-MARKET ---
with tab1:
    st.subheader("Find Hidden Inventory (Predictive)")
    
    source = st.radio("Select Data Source:", ["Franklin/Delaware County (Free)", "Parcl Database (Paid)"])
    
    if st.button("Start Off-Market Scan", type="primary"):
        df_off = pd.DataFrame()
        
        if "Free" in source:
            df_off = offmarket.get_county_leads(zips)
        else:
            if parcl_key:
                df_off = offmarket.get_parcl_leads(zips, parcl_key)
            else:
                st.error("⚠️ Please enter Parcl API Key in sidebar.")
        
        # DISPLAY RESULTS
        if not df_off.empty:
            st.success(f"✅ Scan Complete! Found {len(df_off)} leads.")
            st.dataframe(df_off, use_container_width=True)
            
            # Download Button
            csv = df_off.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Off-Market CSV",
                data=csv,
                file_name="off_market_leads.csv",
                mime="text/csv"
            )
        else:
            st.warning("No leads found matching your criteria.")

# --- TAB 2: ON-MARKET ---
with tab2:
    st.subheader("Active Market Data")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("#### 📊 Market Stats")
        if st.button("Analyze Stats (1 Credit)"):
            if parcl_key:
                # We use a spinner here for better UX
                with st.spinner(f"Fetching stats for {zips[0]}..."):
                    stats = onmarket.get_market_stats(parcl_key, zips[0])
                    if stats:
                        st.metric("Total Housing Units", f"{stats['units']:,}")
                        st.metric("Single Family", f"{stats['single_family']:,}")
                        st.caption(f"As of: {stats['date']}")
            else:
                st.error("Need API Key")

    with col2:
        st.markdown(f"#### 🏡 Active Listings (Last {days_back} Days)")
        
        if st.button("Scan Realtor.com", type="primary"):
            # We pass 'days_back' from the slider to the function
            df_on = onmarket.get_listings(zips, days_back)
            
            if not df_on.empty:
                st.success(f"✅ Found {len(df_on)} active listings!")
                st.dataframe(df_on, use_container_width=True)
                
                # Download Button
                csv_on = df_on.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Listings CSV",
                    data=csv_on,
                    file_name="active_listings.csv",
                    mime="text/csv"
                )
            else:
                st.warning(f"No listings found in the last {days_back} days. Try increasing the 'Lookback Period' in the sidebar.")
