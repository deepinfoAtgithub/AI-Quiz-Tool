import streamlit as st
import pandas as pd
import json
from azure.storage.blob import BlobServiceClient

# --- SECURITY GATEWAY ---
# This MUST be the first thing to run on the page!
st.set_page_config(page_title="Admin | Learning Analytics", layout="wide")

if 'user' not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Secure Area. Please log in from the main portal first.")
    st.page_link("app.py", label="← Go to Login Page", icon="🏠")
    st.stop() # This completely halts the rest of the dashboard from loading

# -----------------------------------------------------------------------------
# 1. Cloud Connection & Data Fetching
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_all_results():
    try:
        connect_str = st.secrets["AZURE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        results_container = blob_service_client.get_container_client("results")
        
        results_data = []
        blobs = results_container.list_blobs()
        for blob in blobs:
            if blob.name.endswith('.json'):
                blob_client = results_container.get_blob_client(blob)
                data = blob_client.download_blob().readall()
                result_json = json.loads(data)
                results_data.append(result_json)
        return results_data
    except Exception as e:
        st.error(f"Failed to connect to Azure Analytics: {e}")
        return []

# -----------------------------------------------------------------------------
# 2. Main Dashboard UI
# -----------------------------------------------------------------------------
def run_admin_portal():
    st.title("📊 Enterprise Learning Analytics")
    st.markdown("Track cohort progress, module difficulty, and learner engagement.")
    st.markdown("---")
    
    with st.spinner("Compiling data from Azure Data Lake..."):
        raw_results = fetch_all_results()
    
    if not raw_results:
        st.info("No assessment data available yet. Waiting for learners to complete modules!")
        return
        
    df = pd.DataFrame(raw_results)
    df['date'] = pd.to_datetime(df['date'])
    df['percentage'] = (df['score'] / df['total']) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Assessments", len(df))
    with col2: st.metric("Unique Learners", df['user_id'].nunique())
    with col3: st.metric("Global Avg Score", f"{df['percentage'].mean():.1f}%")
    with col4: st.metric("Perfect Scores", len(df[df['score'] == df['total']]))
        
    st.markdown("---")
    
    col_chart, col_table = st.columns([1.5, 1])
    with col_chart:
        st.subheader("Average Score by Module")
        avg_scores = df.groupby('title')['percentage'].mean().reset_index()
        st.bar_chart(data=avg_scores.set_index('title'), y='percentage', color="#4F8BF9")
        
    with col_table:
        st.subheader("Learner Engagement")
        user_activity = df.groupby('user_id').size().reset_index(name='Modules Completed')
        user_activity['Learner ID'] = user_activity['user_id'].apply(lambda x: f"User_{x[:8]}")
        user_activity = user_activity[['Learner ID', 'Modules Completed']].sort_values(by='Modules Completed', ascending=False)
        st.dataframe(user_activity, hide_index=True, use_container_width=True)
        
    st.markdown("---")
    st.subheader("Recent Activity Audit Log")
    display_df = df.sort_values(by='date', ascending=False).head(15)
    display_df['Learner'] = display_df['user_id'].apply(lambda x: f"User_{x[:8]}")
    display_df['Score'] = display_df['score'].astype(str) + " / " + display_df['total'].astype(str)
    display_df['Date'] = display_df['date'].dt.strftime("%Y-%m-%d %H:%M")
    
    st.dataframe(display_df[['Date', 'Learner', 'title', 'Score', 'percentage']], hide_index=True, use_container_width=True)

if __name__ == "__main__":
    run_admin_portal()