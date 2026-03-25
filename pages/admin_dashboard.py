import streamlit as st
import pandas as pd
import json
from azure.storage.blob import BlobServiceClient

# --- SECURITY GATEWAY ---
st.set_page_config(page_title="Admin | Learning Analytics", layout="wide")

ADMIN_EMAIL = "solutionarchitect1975@gmail.com"

if 'user' not in st.session_state or st.session_state.user is None:
    st.warning("🔒 Secure Area. Please log in from the main portal first.")
    st.page_link("app.py", label="← Go to Login Page", icon="🏠")
    st.stop()

if st.session_state.user.get('email', '').lower() != ADMIN_EMAIL.lower():
    st.error("🛑 Unauthorized Access.")
    st.write(f"Account `{st.session_state.user.get('email', 'Unknown')}` does not have administrator privileges.")
    st.page_link("app.py", label="← Return to My Progress", icon="🔙")
    st.stop()

# -----------------------------------------------------------------------------
# 1. Cloud Connection Helpers
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_all_results():
    try:
        connect_str = st.secrets["AZURE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        results_container = blob_service_client.get_container_client("results")
        
        results_data = []
        for blob in results_container.list_blobs():
            if blob.name.endswith('.json'):
                data = results_container.get_blob_client(blob).download_blob().readall()
                results_data.append(json.loads(data))
        return results_data
    except Exception as e:
        st.error(f"Failed to fetch analytics: {e}")
        return []

def upload_quiz_to_azure(quiz_id, quiz_json_data):
    """Pushes a new quiz JSON directly to the Azure 'quizzes' container."""
    try:
        connect_str = st.secrets["AZURE_CONNECTION_STRING"]
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        quizzes_container = blob_service_client.get_container_client("quizzes")
        
        # Ensure the filename ends with .json
        filename = f"{quiz_id}.json" if not quiz_id.endswith('.json') else quiz_id
        
        # Upload and overwrite if it already exists
        blob_client = quizzes_container.get_blob_client(filename)
        blob_client.upload_blob(json.dumps(quiz_json_data, indent=4), overwrite=True)
        return True
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return False

# -----------------------------------------------------------------------------
# 2. Main Dashboard UI
# -----------------------------------------------------------------------------
def run_admin_portal():
    st.title("⚙️ Enterprise Admin Portal")
    
    tab_analytics, tab_config = st.tabs(["📊 Analytics Dashboard", "📝 Quiz Configuration"])
    
    # --- TAB 1: ANALYTICS ---
    with tab_analytics:
        st.markdown("Track cohort progress, module difficulty, and learner engagement.")
        st.markdown("---")
        
        with st.spinner("Compiling data from Azure Data Lake..."):
            raw_results = fetch_all_results()
        
        if not raw_results:
            st.info("No assessment data available yet. Waiting for learners to complete modules!")
        else:
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
                st.dataframe(user_activity[['Learner ID', 'Modules Completed']].sort_values(by='Modules Completed', ascending=False), hide_index=True, use_container_width=True)
                
            st.markdown("---")
            st.subheader("Recent Activity Audit Log")
            display_df = df.sort_values(by='date', ascending=False).head(15)
            display_df['Learner'] = display_df['user_id'].apply(lambda x: f"User_{x[:8]}")
            display_df['Score'] = display_df['score'].astype(str) + " / " + display_df['total'].astype(str)
            display_df['Date'] = display_df['date'].dt.strftime("%Y-%m-%d %H:%M")
            
            st.dataframe(display_df[['Date', 'Learner', 'title', 'Score', 'percentage']], hide_index=True, use_container_width=True)

    # --- TAB 2: QUIZ CONFIGURATION ---
    with tab_config:
        st.subheader("Module Deployment Engine")
        st.write("Deploy new assessments directly to the Azure Data Lake. They will instantly appear in the learner's Course Catalog.")
        st.markdown("---")
        
        deploy_method = st.radio("Select Deployment Method:", ["Live JSON Editor", "Upload JSON File"], horizontal=True)
        
        if deploy_method == "Upload JSON File":
            st.info("Upload a pre-formatted JSON file containing your quiz structure.")
            uploaded_file = st.file_uploader("Choose a .json file", type=['json'])
            
            if uploaded_file is not None:
                try:
                    quiz_data = json.load(uploaded_file)
                    st.success("JSON successfully validated!")
                    
                    quiz_id = st.text_input("Confirm Quiz ID (Filename)", value=uploaded_file.name.replace('.json', ''))
                    
                    if st.button("🚀 Deploy to Production", type="primary"):
                        if upload_quiz_to_azure(quiz_id, quiz_data):
                            st.success(f"Successfully deployed **{quiz_id}.json** to Azure!")
                            st.balloons()
                except json.JSONDecodeError:
                    st.error("Invalid JSON file. Please check your syntax.")
                    
        else:
            st.info("Draft and deploy a new assessment using the live editor template.")
            
            col_id, col_space = st.columns([1, 2])
            with col_id:
                quiz_id = st.text_input("Quiz ID (Internal Reference)", value="new_ai_module_01")
            
            # A standard schema template to make drafting easy
            template = {
                "title": "New AI Architecture Quiz",
                "questions": [
                    {
                        "text": "What is the primary benefit of a semantic layer?",
                        "options": ["A", "B", "C"],
                        "answer": "B"
                    }
                ]
            }
            
            json_string = st.text_area("JSON Payload", value=json.dumps(template, indent=4), height=350)
            
            if st.button("🚀 Deploy to Production", type="primary"):
                try:
                    quiz_data = json.loads(json_string)
                    if upload_quiz_to_azure(quiz_id, quiz_data):
                        st.success(f"Successfully deployed **{quiz_id}.json** to Azure!")
                        st.balloons()
                except json.JSONDecodeError:
                    st.error("Invalid JSON syntax. Please check for missing commas or brackets before deploying.")

if __name__ == "__main__":
    run_admin_portal()