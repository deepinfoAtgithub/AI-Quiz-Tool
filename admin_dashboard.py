# admin_dashboard.py
import streamlit as st
import pandas as pd
import json
from azure.storage.blob import BlobServiceClient

st.set_page_config(page_title="Platform Analytics (Admin)", layout="wide")

# Connect to Azure
try:
    connect_str = st.secrets["AZURE_CONNECTION_STRING"]
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client("results")
except Exception as e:
    st.error("Could not connect to Azure. Check secrets.toml.")
    st.stop()

st.title("📊 Platform Analytics")
st.caption("Privacy-Preserving View: User identities are masked.")

# Fetch all result blobs
blobs = list(container_client.list_blobs())

if not blobs:
    st.info("No user attempts recorded yet.")
else:
    # Read data from Azure
    data = []
    for blob in blobs:
        blob_client = container_client.get_blob_client(blob)
        blob_data = blob_client.download_blob().readall()
        result_json = json.loads(blob_data)
        data.append(result_json)
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Aggregate Data for Privacy
    # Grouping by an anonymized user_id (or hashed username) and the quiz
    agg_df = df.groupby(['user_id', 'quiz_id']).agg(
        Total_Attempts=('score', 'count'),
        Last_Attempt=('date', 'max'),
        Average_Score=('score', 'mean')
    ).reset_index()

    # Mask the User ID (e.g., show only first 4 chars of the hash/ID)
    agg_df['user_id'] = agg_df['user_id'].apply(lambda x: f"User_{str(x)[:4]}***")
    
    # Formatting
    agg_df['Last_Attempt'] = agg_df['Last_Attempt'].dt.strftime("%b %d, %Y - %I:%M %p")
    agg_df['Average_Score'] = agg_df['Average_Score'].round(1)

    st.markdown("### User Engagement Overview")
    st.dataframe(agg_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # High-level Platform Metrics
    st.markdown("### Platform Health")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Quizzes Taken", len(df))
    with col2:
        st.metric("Unique Active Users", df['user_id'].nunique())
    with col3:
        # Which quiz is most popular?
        most_popular = df['quiz_id'].value_counts().idxmax() if not df.empty else "N/A"
        st.metric("Most Popular Module", most_popular)