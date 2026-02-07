import streamlit as st
import pandas as pd
from datetime import datetime
import time

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Trader Admin Panel", 
    layout="wide", 
    page_icon="💼"
)

# ---------------------------------------------------------
# 2. SIDEBAR & DATA LOADING
# ---------------------------------------------------------
st.sidebar.title("🔧 Controls")

# PASSWORD PROTECTION
password = st.sidebar.text_input("🔑 Admin Password", type="password")
if password != "admin123":
    st.warning("🔒 Please login to view the dashboard.")
    st.stop()

st.sidebar.success("✅ Access Granted")

# REFRESH BUTTON (Crucial for Google Sheets)
if st.sidebar.button("🔄 Force Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# LOAD DATA FUNCTION
@st.cache_data(ttl=0) # ttl=0 means "don't cache this, get fresh data"
def load_data(url):
    # Add a random timestamp to URL to trick Google into giving fresh data
    fresh_url = f"{url}&cache_bust={time.time()}"
    return pd.read_csv(fresh_url)

# ---------------------------------------------------------
# 3. MAIN APP LOGIC
# ---------------------------------------------------------
st.title("💼 Trader Command Center")
st.markdown("### Live Investment Tracker")

# REPLACE THIS WITH YOUR ACTUAL CSV LINK
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vST3-6dJCY8iK1CbaRRFHFEohC4qc0yoU2TdcCXvYUmsxSMXXvhjj1UHvr6qS6UyPi_XkzhaWXJKk3S/pub?output=csv"

try:
    df = load_data(sheet_url)
    
    # --- DATA CLEANING ---
    # 1. Clean Column Names (Remove accidental spaces)
    df.columns = df.columns.str.strip()
    
    # 2. Rename specific columns if they don't match exactly
    # We look for "Date" or "Start_Date" and standardize it to "Start_Date"
    # This prevents errors if you change the sheet header back and forth
    if 'Date' in df.columns:
        df.rename(columns={'Date': 'Start_Date'}, inplace=True)
        
    # 3. Check if 'Start_Date' exists now
    if 'Start_Date' not in df.columns:
        st.error(f"⚠️ Error: Could not find a 'Start_Date' column. Found: {list(df.columns)}")
        st.stop()

    # 4. Parse the Date (Handling DD/MM/YYYY)
    df['Start_Date'] = pd.to_datetime(df['Start_Date'], dayfirst=True, errors='coerce')

except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

# ---------------------------------------------------------
# 4. THE MONTH CALCULATOR (The Brain)
# ---------------------------------------------------------
if df.empty:
    st.info("Waiting for data... (Sheet is empty)")
else:
    now = datetime.now()

    def calculate_months_left(row):
        start_date = row['Start_Date']
        
        # If date is invalid or missing, return 0
        if pd.isnull(start_date): 
            return 0
            
        # LOGIC:
        # 1. Calculate how many months have passed since Start Date
        diff_years = now.year - start_date.year
        diff_months = now.month - start_date.month
        
        months_passed = (diff_years * 12) + diff_months
        
        # 2. Subtract passed months from 11
        months_left = 11 - months_passed
        
        # 3. Safety Limits
        if months_left > 11: return 11  # Can't have more than 11
        if months_left < 0: return 0    # Can't have negative
            
        return months_left

    # Apply calculation to every row
    df['Months Left'] = df.apply(calculate_months_left, axis=1)

    # Filter: Show only Active deals (Months Left > 0)
    active_deals = df[df['Months Left'] > 0]

    # ---------------------------------------------------------
    # 5. DASHBOARD VISUALS
    # ---------------------------------------------------------
    
    if active_deals.empty:
        st.success("🎉 All contracts are finished! No active liabilities.")
    else:
        # TOP METRICS
        total_held = active_deals['Amount'].sum()
        
        # Display Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Capital Managed", f"₹{total_held:,.0f}")
        col2.metric("👥 Active Investors", f"{len(active_deals)}")
        # Example Payout Calc (assuming 3% average return)
        estimated_payout = total_held * 0.03 
        col3.metric("⚠️ Est. Monthly Payout", f"₹{estimated_payout:,.0f}", "Approx 3%")

        st.divider()
        
        # DETAILED TABLE
        st.subheader("⏳ Contract Countdown (11 Months)")
        
        # Format the table nicely
        st.dataframe(
            active_deals[['Name', 'Amount', 'Start_Date', 'Months Left']],
            use_container_width=True,
            column_config={
                "Months Left": st.column_config.ProgressColumn(
                    "Time Remaining",
                    format="%d months left",
                    min_value=0,
                    max_value=11,
                ),
                "Amount": st.column_config.NumberColumn(
                    "Invested Amount",
                    format="₹%d"
                ),
                "Start_Date": st.column_config.DateColumn(
                    "Start Date",
                    format="DD/MM/YYYY"
                )
            }
        )

# ---------------------------------------------------------
# 6. SIDEBAR FOOTER
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.info("System Online 🟢")
st.sidebar.caption("Novanode Analytics v1.2")
