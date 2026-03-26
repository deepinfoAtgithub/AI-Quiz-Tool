import streamlit as st
import pandas as pd
import json
from azure.storage.blob import BlobServiceClient

# --- SECURITY GATEWAY ---
st.set_page_config(page_title="Admin | Learning Analytics", layout="wide") #[cite: 1]

ADMIN_EMAIL = "solutionarchitect1975@gmail.com" #[cite: 1]

if 'user' not in st.session_state or st.session_state.user is None: #[cite: 1]
    st.warning("🔒 Secure Area. Please log in from the main portal first.") #[cite: 1]
    st.page_link("app.py", label="← Go to Login Page", icon="🏠") #[cite: 1]
    st.stop() #[cite: 1]

if st.session_state.user.get('email', '').lower() != ADMIN_EMAIL.lower(): #[cite: 1]
    st.error("🛑 Unauthorized Access.") #[cite: 1]
    st.write(f"Account `{st.session_state.user.get('email', 'Unknown')}` does not have administrator privileges.") #[cite: 1]
    st.page_link("app.py", label="← Return to My Progress", icon="🔙") #[cite: 1]
    st.stop() #[cite: 1]

# -----------------------------------------------------------------------------
# 1. Cloud & AI Helpers
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60) #[cite: 1]
def fetch_all_results(): #[cite: 1]
    try: #[cite: 1]
        connect_str = st.secrets["AZURE_CONNECTION_STRING"] #[cite: 1]
        blob_service_client = BlobServiceClient.from_connection_string(connect_str) #[cite: 1]
        results_container = blob_service_client.get_container_client("results") #[cite: 1]
        
        results_data = [] #[cite: 1]
        for blob in results_container.list_blobs(): #[cite: 1]
            if blob.name.endswith('.json'): #[cite: 1]
                data = results_container.get_blob_client(blob).download_blob().readall() #[cite: 1]
                results_data.append(json.loads(data)) #[cite: 1]
        return results_data #[cite: 1]
    except Exception as e: #[cite: 1]
        st.error(f"Failed to fetch analytics: {e}") #[cite: 1]
        return [] #[cite: 1]

def upload_quiz_to_azure(quiz_id, quiz_json_data): #[cite: 1]
    """Pushes a new quiz JSON directly to the Azure 'quizzes' container.""" #[cite: 1]
    try: #[cite: 1]
        connect_str = st.secrets["AZURE_CONNECTION_STRING"] #[cite: 1]
        blob_service_client = BlobServiceClient.from_connection_string(connect_str) #[cite: 1]
        quizzes_container = blob_service_client.get_container_client("quizzes") #[cite: 1]
        
        filename = f"{quiz_id}.json" if not quiz_id.endswith('.json') else quiz_id #[cite: 1]
        
        blob_client = quizzes_container.get_blob_client(filename) #[cite: 1]
        blob_client.upload_blob(json.dumps(quiz_json_data, indent=4), overwrite=True) #[cite: 1]
        return True #[cite: 1]
    except Exception as e: #[cite: 1]
        st.error(f"Upload failed: {e}") #[cite: 1]
        return False #[cite: 1]

def generate_quiz_via_ai(file_bytes, file_type, quiz_name, num_questions):
    """
    Placeholder for the LLM call. 
    This is where we will pass the image/text to the AI to get the JSON.
    """
    # TODO: Insert OpenAI/Gemini API call here.
    # For now, it returns a strictly formatted mock JSON so you can test the UI flow.
    return {
        "title": quiz_name,
        "questions": [
            {
                "text": f"This is an AI generated question for {quiz_name}?",
                "options": ["True", "False"],
                "answer": "True"
            }
        ]
    }

# -----------------------------------------------------------------------------
# 2. Main Dashboard UI
# -----------------------------------------------------------------------------
def run_admin_portal(): #[cite: 1]
    st.title("⚙️ Enterprise Admin Portal") #[cite: 1]
    
    tab_analytics, tab_config = st.tabs(["📊 Analytics Dashboard", "📝 Quiz Configuration"]) #[cite: 1]
    
    # --- TAB 1: ANALYTICS (Unchanged) ---
    with tab_analytics: #[cite: 1]
        st.markdown("Track cohort progress, module difficulty, and learner engagement.") #[cite: 1]
        st.markdown("---") #[cite: 1]
        
        with st.spinner("Compiling data from Azure Data Lake..."): #[cite: 1]
            raw_results = fetch_all_results() #[cite: 1]
        
        if not raw_results: #[cite: 1]
            st.info("No assessment data available yet. Waiting for learners to complete modules!") #[cite: 1]
        else: #[cite: 1]
            df = pd.DataFrame(raw_results) #[cite: 1]
            df['date'] = pd.to_datetime(df['date']) #[cite: 1]
            df['percentage'] = (df['score'] / df['total']) * 100 #[cite: 1]
            
            col1, col2, col3, col4 = st.columns(4) #[cite: 1]
            with col1: st.metric("Total Assessments", len(df)) #[cite: 1]
            with col2: st.metric("Unique Learners", df['user_id'].nunique()) #[cite: 1]
            with col3: st.metric("Global Avg Score", f"{df['percentage'].mean():.1f}%") #[cite: 1]
            with col4: st.metric("Perfect Scores", len(df[df['score'] == df['total']])) #[cite: 1]
                
            st.markdown("---") #[cite: 1]
            
            col_chart, col_table = st.columns([1.5, 1]) #[cite: 1]
            with col_chart: #[cite: 1]
                st.subheader("Average Score by Module") #[cite: 1]
                avg_scores = df.groupby('title')['percentage'].mean().reset_index() #[cite: 1]
                st.bar_chart(data=avg_scores.set_index('title'), y='percentage', color="#4F8BF9") #[cite: 1]
                
            with col_table: #[cite: 1]
                st.subheader("Learner Engagement") #[cite: 1]
                user_activity = df.groupby('user_id').size().reset_index(name='Modules Completed') #[cite: 1]
                user_activity['Learner ID'] = user_activity['user_id'].apply(lambda x: f"User_{x[:8]}") #[cite: 1]
                st.dataframe(user_activity[['Learner ID', 'Modules Completed']].sort_values(by='Modules Completed', ascending=False), hide_index=True, use_container_width=True) #[cite: 1]
                
            st.markdown("---") #[cite: 1]
            st.subheader("Recent Activity Audit Log") #[cite: 1]
            display_df = df.sort_values(by='date', ascending=False).head(15) #[cite: 1]
            display_df['Learner'] = display_df['user_id'].apply(lambda x: f"User_{x[:8]}") #[cite: 1]
            display_df['Score'] = display_df['score'].astype(str) + " / " + display_df['total'].astype(str) #[cite: 1]
            display_df['Date'] = display_df['date'].dt.strftime("%Y-%m-%d %H:%M") #[cite: 1]
            
            st.dataframe(display_df[['Date', 'Learner', 'title', 'Score', 'percentage']], hide_index=True, use_container_width=True) #[cite: 1]

    # --- TAB 2: QUIZ CONFIGURATION ---
    with tab_config: #[cite: 1]
        st.subheader("Module Deployment Engine") #[cite: 1]
        st.write("Deploy new assessments directly to the Azure Data Lake. They will instantly appear in the learner's Course Catalog.") #[cite: 1]
        st.markdown("---") #[cite: 1]
        
        # ADDED "AI Auto-Generate" to the options
        deploy_method = st.radio("Select Deployment Method:", ["AI Auto-Generate", "Live JSON Editor", "Upload JSON File"], horizontal=True) #[cite: 1]
        
        # --- NEW OPTION: AI GENERATOR ---
        if deploy_method == "AI Auto-Generate":
            st.info("Upload an architecture diagram or source document to automatically generate a quiz.")
            
            with st.form("ai_generator_form"):
                quiz_name = st.text_input("Quiz Title", placeholder="e.g., Semantic Layer Basics")
                num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5)
                
                source_file = st.file_uploader("Upload Diagram or Source Text", type=['png', 'jpg', 'jpeg', 'txt', 'pdf', 'csv'])
                
                submitted = st.form_submit_button("Generate & Deploy", type="primary")

                if submitted:
                    if not source_file or not quiz_name:
                        st.warning("Please provide a quiz title and upload a source file.")
                    else:
                        with st.spinner("AI is analyzing the source and generating the JSON schema..."):
                            # 1. Read the file
                            file_bytes = source_file.read()
                            
                            # 2. Pass to our AI function
                            generated_json = generate_quiz_via_ai(file_bytes, source_file.type, quiz_name, num_questions)
                            
                            # 3. Format filename securely
                            safe_filename = quiz_name.lower().replace(" ", "_") + ".json"
                            
                            # 4. Push to Azure
                            if upload_quiz_to_azure(safe_filename, generated_json):
                                st.success(f"Successfully generated and deployed **{safe_filename}** to Azure!")
                                st.balloons()
                                with st.expander("View Generated JSON"):
                                    st.json(generated_json)

        # --- EXISTING OPTION 1: UPLOAD JSON ---
        elif deploy_method == "Upload JSON File": #[cite: 1]
            st.info("Upload a pre-formatted JSON file containing your quiz structure.") #[cite: 1]
            uploaded_file = st.file_uploader("Choose a .json file", type=['json']) #[cite: 1]
            
            if uploaded_file is not None: #[cite: 1]
                try: #[cite: 1]
                    quiz_data = json.load(uploaded_file) #[cite: 1]
                    st.success("JSON successfully validated!") #[cite: 1]
                    
                    quiz_id = st.text_input("Confirm Quiz ID (Filename)", value=uploaded_file.name.replace('.json', '')) #[cite: 1]
                    
                    if st.button("🚀 Deploy to Production", type="primary"): #[cite: 1]
                        if upload_quiz_to_azure(quiz_id, quiz_data): #[cite: 1]
                            st.success(f"Successfully deployed **{quiz_id}.json** to Azure!") #[cite: 1]
                            st.balloons() #[cite: 1]
                except json.JSONDecodeError: #[cite: 1]
                    st.error("Invalid JSON file. Please check your syntax.") #[cite: 1]
                    
        # --- EXISTING OPTION 2: LIVE EDITOR ---
        else:
            st.info("Draft and deploy a new assessment using the live editor template.") #[cite: 1]
            
            col_id, col_space = st.columns([1, 2]) #[cite: 1]
            with col_id: #[cite: 1]
                quiz_id = st.text_input("Quiz ID (Internal Reference)", value="new_ai_module_01") #[cite: 1]
            
            template = { #[cite: 1]
                "title": "New AI Architecture Quiz", #[cite: 1]
                "questions": [ #[cite: 1]
                    { #[cite: 1]
                        "text": "What is the primary benefit of a semantic layer?", #[cite: 1]
                        "options": ["A", "B", "C"], #[cite: 1]
                        "answer": "B" #[cite: 1]
                    } #[cite: 1]
                ] #[cite: 1]
            } #[cite: 1]
            
            json_string = st.text_area("JSON Payload", value=json.dumps(template, indent=4), height=350) #[cite: 1]
            
            if st.button("🚀 Deploy to Production", type="primary"): #[cite: 1]
                try: #[cite: 1]
                    quiz_data = json.loads(json_string) #[cite: 1]
                    if upload_quiz_to_azure(quiz_id, quiz_data): #[cite: 1]
                        st.success(f"Successfully deployed **{quiz_id}.json** to Azure!") #[cite: 1]
                        st.balloons() #[cite: 1]
                except json.JSONDecodeError: #[cite: 1]
                    st.error("Invalid JSON syntax. Please check for missing commas or brackets before deploying.") #[cite: 1]

if __name__ == "__main__": #[cite: 1]
    run_admin_portal() #[cite: 1]