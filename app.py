import streamlit as st
import offmarket
import onmarket
import credits

st.set_page_config(page_title="VeloRaq", layout="wide")

# --- SIDEBAR: CONTROLS & CREDITS ---
with st.sidebar:
    st.header("⚙️ VeloRaq Settings")
    
    # 1. API Key
    parcl_key = st.text_input("Parcl API Key", type="password")
    
    st.divider()
    
    # 2. CREDIT METER (The Visual)
    used, limit = credits.get_status()
    st.metric("Credits Used", f"{used} / {limit}")
    progress = min(used / limit, 1.0)
    st.progress(progress)
    
    if used >= limit:
        st.error("⛔ LIMIT REACHED")
    
    if st.button("Reset Counter (New Month)"):
        credits.reset()
        st.rerun()

    st.divider()
    
    # 3. Zip Codes
    st.caption("Target Markets (Comma Separated)")
    zips_input = st.text_area("Zip Codes", "43081, 43138")
    zips = [z.strip() for z in zips_input.split(',')]

st.title("🚲 VeloRaq: Real Estate Command Center")

tab1, tab2 = st.tabs(["🕵️ Off-Market Hunter", "🏡 On-Market Listings"])

# --- TAB 1: OFF-MARKET ---
with tab1:
    st.subheader("Find Hidden Inventory")
    
    source = st.radio(
        "Select Data Source:", 
        ["Franklin/Delaware County (Free)", "Parcl Database (Paid - 10 Credits/Zip)"]
    )
    
    if st.button("Start Scan"):
        if "Free" in source:
            df = offmarket.get_county_leads(zips)
        else:
            if not parcl_key:
                st.error("Please enter API Key in sidebar.")
                df = pd.DataFrame()
            else:
                # Credit check happens inside this function
                df = offmarket.get_parcl_leads(zips, parcl_key)
        
        if not df.empty:
            st.success(f"Found {len(df)} Leads")
            st.dataframe(df, use_container_width=True)
            st.download_button("Download CSV", df.to_csv(index=False), "leads.csv")
        else:
            st.warning("No leads found.")

# --- TAB 2: ON-MARKET ---
with tab2:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### 📊 Market Stats (Paid)")
        if st.button("Analyze Market (1 Credit)"):
            if parcl_key:
                stats = onmarket.get_market_stats(parcl_key, zips[0])
                if stats:
                    st.metric("Total Units", f"{stats['units']:,}")
                    st.metric("Single Family", f"{stats['single_family']:,}")
                    st.caption(f"Updated: {stats['date']}")
            else:
                st.error("Need API Key")

    with col2:
        st.markdown("#### 🏡 Active Listings (Free)")
        if st.button("Scan Realtor.com"):
            with st.spinner("Scraping..."):
                df_on = onmarket.get_listings(zips)
            if not df_on.empty:
                st.dataframe(df_on, use_container_width=True)
            else:
                st.info("No new listings found.")
