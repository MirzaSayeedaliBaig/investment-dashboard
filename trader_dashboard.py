import streamlit as st
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 1. PAGE CONFIG
st.set_page_config(page_title="Boss Admin Panel", layout="wide", page_icon="💼")

# 2. AUTHENTICATION (Boss Only)
# In real life, hide this password logic better, but for now:
password = st.sidebar.text_input("🔑 Admin Password", type="password")
if password != "boss123":
    st.warning("Please login to view financial data.")
    st.stop()

# 3. CONNECT TO GOOGLE SHEET
# REPLACE THIS URL with your actual "Publish to Web" CSV link from Part 2
# It will look like: https://docs.google.com/spreadsheets/d/e/2PACX.../pub?output=csv
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vST3-6dJCY8iK1CbaRRFHFEohC4qc0yoU2TdcCXvYUmsxSMXXvhjj1UHvr6qS6UyPi_XkzhaWXJKk3S/pub?output=csv" 

# Check if user put the link in yet
try:
    # Use on_bad_lines='skip' to avoid errors if the sheet is empty
    df = pd.read_csv(sheet_url)
    
    # RENAME columns to match our code logic if needed, or ensure Sheet headers match these:
    # We expect columns: Name, Amount, Date, ROI
except:
    st.error("⚠️ Could not connect to Google Sheet. Please check the link.")
    st.stop()

# 4. DASHBOARD LOGIC
st.title("💼 Trader Command Center")
st.markdown("### Live Overview")

if df.empty:
    st.info("No data found in the Google Sheet yet.")
else:
    # --- DATA CLEANING ---
    # Ensure Date is actually a date format
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Calculate Monthly Payout (Amount * ROI / 100)
    df['Monthly Payout'] = (df['Amount'] * df['ROI']) / 100

    # --- CALCULATE TIME LEFT (11 Months) ---
# --- LOGIC: CALCULATE TIME LEFT ---
    today = pd.to_datetime("today").normalize() # Get today's date
    
    def calculate_status(start_date):
        # Calculate the difference between NOW and START DATE
        delta = relativedelta(today, start_date)
        months_passed = delta.years * 12 + delta.months
        
        # FIX 1: If start date is in the future (negative passed), set passed to 0
        if months_passed < 0:
            months_passed = 0
            
        months_left = 11 - months_passed
        
        # FIX 2: If contract is over (negative left), set left to 0
        if months_left < 0:
            months_left = 0
            
        return months_left

    # Apply this new smart logic
    df['Months Left'] = df['Date'].apply(calculate_status)
    
    # Filter: Only show active deals (Months Left > 0)
    active_df = df[df['Months Left'] > 0]
    # --- METRICS THE BOSS WANTS ---
    # 1. Total Money Held
    total_held = active_df['Amount'].sum()
    
    # 2. Total Monthly Liability (What he pays out every month)
    monthly_bill = active_df['Monthly Payout'].sum()
    
    # 3. Total Profit Estimate (Assuming he makes 10% profit but pays 5%)
    # This is optional, but cool for him to see
    
    # DISPLAY METRICS
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Funds Managed", f"₹{total_held:,.0f}")
    col2.metric("⚠️ Monthly Payout Due", f"₹{monthly_bill:,.0f}", "Fixed Liability")
    col3.metric("👥 Active Investors", f"{len(active_df)}")

    st.divider()

    # --- THE DETAILED TRACKER ---
    st.subheader("⏳ Investor Time Tracker")
    
    # Create a nice display table
    display_df = active_df[['Name', 'Amount', 'Monthly Payout', 'Date', 'Months Left']]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "Months Left": st.column_config.ProgressColumn(
                "Time Remaining",
                format="%d months left",
                min_value=0,
                max_value=11,
            ),
            "Amount": st.column_config.NumberColumn(format="₹%d"),
            "Monthly Payout": st.column_config.NumberColumn(format="₹%d"),
            "Date": st.column_config.DateColumn("Start Date")
        }
    )
