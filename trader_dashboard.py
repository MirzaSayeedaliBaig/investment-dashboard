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
    
    # --- CRITICAL FIX: DATE PARSING ---
    # This tells Python: "Expect Day First!" (e.g. 05/11 is 5th Nov, not May 11th)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

except:
    st.error("⚠️ Waiting for data... (Check your CSV link)")
    st.stop()

if df.empty:
    st.info("No data in sheet yet.")
else:
    # ---------------------------------------------------------
    # THE LOGIC: ROBUST MONTH CALCULATOR
    # ---------------------------------------------------------
    
    # Get today's date
    now = datetime.now()
    
    def calculate_months_left(start_date):
        if pd.isnull(start_date): # Check for bad dates
            return 0
            
        # THE MATH FORMULA:
        # (Difference in Years * 12) + (Difference in Months)
        # Ex: Feb 2026 vs Nov 2025
        # (1 Year * 12) + (2 - 11) = 12 - 9 = 3 Months Passed
        
        diff_years = now.year - start_date.year
        diff_months = now.month - start_date.month
        
        months_passed = (diff_years * 12) + diff_months
        
        # Calculate Left
        months_left = 11 - months_passed
        
        # SAFETY CAPS:
        # 1. If date is in future, don't show more than 11
        if months_left > 11:
            return 11
        # 2. If time is up, don't show negative
        if months_left < 0:
            return 0
            
        return months_left

    # Apply the math
    df['Months Left'] = df['Date'].apply(calculate_months_left)
    
    # Filter for active investors (where time is not 0)
    active_deals = df[df['Months Left'] > 0]

    # ---------------------------------------------------------
    # DASHBOARD DISPLAY
    # ---------------------------------------------------------

    if active_deals.empty:
        st.success("🎉 All contracts are finished!")
    else:
        # Top Metrics
        total_held = active_deals['Amount'].sum()
        # Monthly payout is usually Amount * ROI% / 100
        # If your CSV has 'ROI', uncomment the next line:
        # active_deals['Monthly Payout'] = active_deals['Amount'] * active_deals['ROI'] / 100
        
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
