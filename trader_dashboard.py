import streamlit as st
import pandas as pd

# 1. PAGE CONFIG
st.set_page_config(page_title="Trader Admin Panel", layout="wide", page_icon="💼")
st.title("💼 Trader Command Center")

# 2. CONNECT TO GOOGLE SHEET
# REPLACE with your actual CSV link
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vST3-6dJCY8iK1CbaRRFHFEohC4qc0yoU2TdcCXvYUmsxSMXXvhjj1UHvr6qS6UyPi_XkzhaWXJKk3S/pub?output=csv"

try:
    df = pd.read_csv(sheet_url)
    
    # CLEANING: Make sure we don't have spaces in names (e.g. "Rahul " vs "Rahul")
    # This fixes the most common bug where names don't match
    df['Name'] = df['Name'].astype(str).str.strip().str.title()
    df['Type'] = df['Type'].astype(str).str.strip()

except:
    st.error("⚠️ Waiting for data... (Check your CSV link or Google Sheet)")
    st.stop()

if df.empty:
    st.info("No data in sheet yet.")
else:
    # ---------------------------------------------------------
    # THE LOGIC: COUNTING PAYOUTS
    # ---------------------------------------------------------
    
    # 1. Get all the "Investment" rows (The people who gave money)
    investments = df[df['Type'] == 'Investment'].copy()
    
    # 2. Get all the "Payout" rows (The times you paid them back)
    payouts = df[df['Type'] == 'Payout'].copy()
    
    # 3. Count how many times each person has been paid
    # This creates a list like: {'Rahul': 2, 'Priya': 5}
    payout_counts = payouts['Name'].value_counts()

    # 4. The Magic Formula
    def calculate_remaining(row):
        person_name = row['Name']
        
        # Look up how many times we paid this person. If 0 times, return 0.
        times_paid = payout_counts.get(person_name, 0)
        
        # 11 Months - Times Paid
        months_left = 11 - times_paid
        
        # Safety: Don't let it show negative numbers
        return max(months_left, 0)

    # Apply the formula to every investor
    investments['Months Left'] = investments.apply(calculate_remaining, axis=1)
    
    # ---------------------------------------------------------
    # DASHBOARD DISPLAY
    # ---------------------------------------------------------

    # Filter: Only show people who still have months left
    active_deals = investments[investments['Months Left'] > 0]

    if active_deals.empty:
        st.success("🎉 All investors have been fully paid!")
    else:
        # Top Metrics
        total_held = active_deals['Amount'].sum()
        active_count = len(active_deals)
        
        # Display Metrics
        col1, col2 = st.columns(2)
        col1.metric("💰 Total Active Capital", f"₹{total_held:,.0f}")
        col2.metric("👥 Active Investors", f"{active_count}")

        st.divider()
        st.subheader("⏳ Payment Status (11-Month Cycle)")

        # Display the Table
        st.dataframe(
            active_deals[['Name', 'Amount', 'Date', 'Months Left']],
            use_container_width=True,
            column_config={
                "Months Left": st.column_config.ProgressColumn(
                    "Remaining Payouts",
                    format="%d months left",
                    min_value=0,
                    max_value=11,
                    help="Decreases every time you submit a Payout form"
                ),
                "Amount": st.column_config.NumberColumn(format="₹%d"),
                "Date": st.column_config.DateColumn("Start Date")
            }
        )
