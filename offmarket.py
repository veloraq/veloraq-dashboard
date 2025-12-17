import streamlit as st
import pandas as pd

def render_off_market(api_manager, zips):
    st.subheader("Find Hidden Inventory (Predictive)")
    
    st.info("ℹ️ Currently scanning Franklin & Delaware County GIS (Free)")
    
    if st.button("Start Off-Market Scan", type="primary"):
        with st.spinner("Scanning County Records..."):
            
            # Call the Manager
            df = api_manager.get_off_market_leads(zips)
            
            if not df.empty:
                st.success(f"✅ Found {len(df)} leads!")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Leads", csv, "off_market.csv", "text/csv")
            else:
                st.warning("No leads found matching criteria.")
