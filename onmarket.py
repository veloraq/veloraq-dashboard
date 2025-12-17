import streamlit as st

def render_active_listings(api_manager, zips, days_back):
    st.subheader(f"🏡 Active Listings (Apify Scraper)")
    
    # Check if key is present
    if not api_manager.apify_key:
        st.warning("⚠️ Please enter an Apify API Token in the sidebar to scan.")
        st.info("💡 You can get a free token at console.apify.com")
        return

    if st.button("Scan Market", type="primary"):
        with st.spinner("🤖 Running Apify Scraper... (This may take 10-20s)"):
            
            # The one line that matters:
            df = api_manager.get_active_listings(zips, days_back)
            
            if not df.empty:
                st.success(f"✅ Found {len(df)} listings!")
                st.dataframe(df, use_container_width=True)
                
                # CSV Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, "apify_listings.csv", "text/csv")
            else:
                st.warning("No listings found. (Check Apify credits or Zip Code)")

def render_market_stats(api_manager, zips):
    st.markdown("#### 📊 Market Stats")
    if st.button("Analyze Stats (1 Credit)"):
        with st.spinner("Checking Parcl..."):
            stats = api_manager.get_market_stats(zips[0])
            if stats:
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Units", f"{stats['units']:,}")
                c2.metric("Single Family", f"{stats['single_family']:,}")
                c3.metric("Condos/Apts", f"{stats['other']:,}")
                st.caption(f"As of: {stats['date']}")
            else:
                st.error("Stats unavailable (Check Parcl Key)")
