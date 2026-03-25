# manage_quiz.py
import streamlit as st
import json
from azure.storage.blob import BlobServiceClient

st.set_page_config(page_title="Quiz Manager (Admin)", layout="wide")

# Connect to Azure
try:
    connect_str = st.secrets["AZURE_CONNECTION_STRING"]
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client("quizzes")
except Exception as e:
    st.error("Could not connect to Azure. Check secrets.toml.")
    st.stop()

st.title("🛠️ Quiz Manager (Admin Only)")

# Feature: List Existing Quizzes
st.subheader("Existing Quizzes in Azure")
blobs = container_client.list_blobs()
quiz_files = [blob.name for blob in blobs]

if quiz_files:
    st.write(quiz_files)
else:
    st.info("No quizzes found in the 'quizzes' container.")

st.markdown("---")

# Feature: Create / Update a Quiz
st.subheader("Add or Update a Quiz")
with st.form("quiz_editor_form"):
    quiz_id = st.text_input("Quiz ID (e.g., ai_kitchen_01 - this will be the filename)", placeholder="ai_kitchen_01")
    quiz_title = st.text_input("Quiz Title", placeholder="The AI Kitchen: Architecture Basics")
    quiz_category = st.text_input("Category", placeholder="AI/ML Basics")
    
    # Using a text area for raw JSON input of questions for speed and flexibility
    default_questions = """[
  {
    "text": "Sample Question?",
    "options": ["A", "B", "C", "D"],
    "answer": "A"
  }
]"""
    questions_json = st.text_area("Questions (JSON Format)", value=default_questions, height=300)
    
    submitted = st.form_submit_button("Save to Azure Blob Storage", type="primary")
    
    if submitted:
        if quiz_id:
            try:
                # Validate JSON structure
                questions_parsed = json.loads(questions_json)
                
                # Construct the final document
                quiz_document = {
                    "title": quiz_title,
                    "category": quiz_category,
                    "questions": questions_parsed
                }
                
                # Upload to Azure
                blob_client = blob_service_client.get_blob_client(container="quizzes", blob=f"{quiz_id}.json")
                blob_client.upload_blob(json.dumps(quiz_document, indent=2), overwrite=True)
                
                st.success(f"Successfully saved {quiz_id}.json to Azure!")
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON format in the Questions field. Please check your syntax.")
        else:
            st.error("Quiz ID is required.")