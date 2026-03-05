import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="GUVI Feedback Portal", layout="wide")
st.title("📞 GUVI Learner Feedback Portal")

# -----------------------------
# GOOGLE SHEET CONNECTION
# -----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)


client = gspread.authorize(creds)

SHEET_NAME = "Sheet1"

spreadsheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/17wG1UbihhBD-JGMhDaBbQGIi_kq8XgvwLEEPdCnBlNI"
)

worksheet = spreadsheet.worksheet(SHEET_NAME)

data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Clean column names
df.columns = df.columns.str.strip().str.replace(" ", "_")

# -----------------------------
# ELIGIBILITY FILTER
# -----------------------------
eligible_df = df[
    (df["Assigned_Mini_Project"] == df["Submitted_Mini_Projects"]) &
    (df["Total_Final_Project"] == df["Submitted_Final_Project"]) &
    (df["Codekata_Count"] >= 250) &
    (df["Feedback_status"] != "Completed")
]

eligible_df = eligible_df.sort_values(by="Codekata_Count", ascending=False)

st.subheader("✅ Eligible Candidates")
st.write(f"Total Eligible: {len(eligible_df)}")

if len(eligible_df) == 0:
    st.success("🎉 No pending feedback. All caught up!")
    st.stop()

# -----------------------------
# TABLE VIEW WITH EXTRA COLUMNS
# -----------------------------
st.subheader("📋 Eligible Candidates List")

display_df = eligible_df[[
    "Learner_Name",
    "Mail_ID",
    "Batch_Number",
    "Assigned_Mini_Project",
    "Submitted_Mini_Projects",
    "Total_Final_Project",
    "Submitted_Final_Project",
    "Codekata_Count"
]].copy()

# Create clean x/y format columns
display_df["Mini Projects"] = (
    display_df["Submitted_Mini_Projects"].astype(str)
    + " / "
    + display_df["Assigned_Mini_Project"].astype(str)
)

display_df["Final Projects"] = (
    display_df["Submitted_Final_Project"].astype(str)
    + " / "
    + display_df["Total_Final_Project"].astype(str)
)

# Select final columns to display
display_df = display_df[[
    "Learner_Name",
    "Mail_ID",
    "Batch_Number",
    "Mini Projects",
    "Final Projects",
    "Codekata_Count"
]]

# Rename for better UI
display_df = display_df.rename(columns={
    "Learner_Name": "Learner",
    "Mail_ID": "Email",
    "Batch_Number": "Batch",
    "Codekata_Count": "Codekata"
})

st.dataframe(display_df, use_container_width=True)

# -----------------------------
# SELECT CANDIDATE
# -----------------------------
st.subheader("🎯 Select Candidate To Give Feedback")

selected_name = st.selectbox(
    "Select Candidate",
    eligible_df["Learner_Name"]
)

selected_row = eligible_df[
    eligible_df["Learner_Name"] == selected_name
].iloc[0]

st.write("### 📌 Candidate Details")
st.write(f"📧 Mail ID: {selected_row['Mail_ID']}")
st.write(f"🏫 Batch: {selected_row['Batch_Number']}")
st.write(f"💻 Codekata: {selected_row['Codekata_Count']}")
st.write(f"📘 Mini Projects: {selected_row['Submitted_Mini_Projects']} / {selected_row['Assigned_Mini_Project']}")
st.write(f"📗 Final Projects: {selected_row['Submitted_Final_Project']} / {selected_row['Total_Final_Project']}")

# -----------------------------
# FEEDBACK FORM
# -----------------------------
st.write("### 📝 Enter Feedback")

feedback_category = st.selectbox(
    "Feedback Category",
    ["Strong Candidate", "Needs Improvement", "Not Ready"]
)

feedback_text = st.text_area("Detailed Feedback")

if st.button("✅ Submit Feedback"):

    sheet_data = worksheet.get_all_values()
    headers = sheet_data[0]

    name_col_index = headers.index("Learner_Name")
    feedback_status_col = headers.index("Feedback_status")
    feedback_text_col = headers.index("Feedback_text")
    date_col = headers.index("Last_called_date")

    for i, row in enumerate(sheet_data[1:], start=2):
        if row[name_col_index] == selected_name:
            worksheet.update_cell(i, feedback_status_col + 1, "Completed")
            worksheet.update_cell(i, feedback_text_col + 1, f"{feedback_category} - {feedback_text}")
            worksheet.update_cell(i, date_col + 1, datetime.today().strftime("%Y-%m-%d"))
            break

    st.success("✅ Feedback submitted successfully!")
    st.rerun()