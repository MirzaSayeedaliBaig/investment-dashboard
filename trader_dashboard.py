import streamlit as st
import pandas as pd
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="Trader Admin Panel", layout="wide", page_icon="💼")
st.title("💼 Trader Command Center")

# 2. CONNECT TO GOOGLE SHEET
# REPLACE THIS WITH YOUR LINK
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vST3-6dJCY8iK1CbaRRFHFEohC4qc0yoU2TdcCXvYUmsxSMXXvhjj1UHvr6qS6UyPi_XkzhaWXJKk3S/pub?output=csv"

try:
    df = pd.read_csv(sheet_url)
    
    # --- CRITICAL FIX: EXPLICITLY SELECT THE 'Date' COLUMN ---
    # Python might be confusing 'Timestamp' (Col A) with 'Date' (Col D).
    # We will rename the columns to be 100% sure.
    
    # Check if we have the right columns. If not, print what we found.
    # The standard Google Sheet headers from your script should be:
    # Timestamp, Name, Amount, Date, ROI
    
    # Let's force the column names just in case
    expected_cols = ['Timestamp', 'Name', 'Amount', 'Date', 'ROI']
    if len(df.columns) >= 5:
        df.columns = expected_cols + list(df.columns[5:]) # Rename first 5 cols
    
    # NOW parse the specific 'Date' column (Column D)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

except Exception as e:
    st.error(f"⚠️ Error reading data: {e}")
    st.stop()

if df.empty:
    st.info("No data in sheet yet.")
else:
    # ---------------------------------------------------------
    # THE LOGIC: ROBUST MONTH CALCULATOR
    # ---------------------------------------------------------
    
    now = datetime.now()
    
    def calculate_months_left(start_date):
        if pd.isnull(start_date): 
            return 0
            
        # DEBUG: If date is today/future, return 11.
        # If date is Nov 2025, it should calculate diff.
        
        diff_years = now.year - start_date.year
        diff_months = now.month - start_date.month
        
        months_passed = (diff_years * 12) + diff_months
        
        # Calculate Left
        months_left = 11 - months_passed
        
        if months_left > 11: return 11
        if months_left < 0: return 0
            
        return months_left

    # Apply the math
    df['Months Left'] = df['Date'].apply(calculate_months_left)
    
    # Filter for active investors
    active_deals = df[df['Months Left'] > 0]

    # ---------------------------------------------------------
    # DASHBOARD DISPLAY
    # ---------------------------------------------------------

    if active_deals.empty:
        st.success("🎉 All contracts are finished!")
    else:
        # Top Metrics
        total_held = active_deals['Amount'].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("💰 Total Active Capital", f"₹{total_held:,.0f}")
        col2.metric("👥 Active Investors", f"{len(active_deals)}")

        st.divider()
        st.subheader("⏳ Time Tracker (Auto-Decreasing)")

        # Display the Table
        st.dataframe(
            active_deals[['Name', 'Amount', 'Date', 'Months Left']],
            use_container_width=True,
            column_config={
                "Months Left": st.column_config.ProgressColumn(
                    "Countdown",
                    format="%d months left",
                    min_value=0,
                    max_value=11,
                ),
                "Amount": st.column_config.NumberColumn(format="₹%d"),
                "Date": st.column_config.DateColumn("Start Date", format="DD/MM/YYYY")
            }
        )
