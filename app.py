import streamlit as st
import datetime
import json
import uuid
import hashlib
from azure.storage.blob import BlobServiceClient
from dashboard import render_dashboard
import auth

# Page config MUST be the first Streamlit command
st.set_page_config(page_title="AI Solution Architect Portal", layout="wide")

# -----------------------------------------------------------------------------
# 1. Azure & Auth Initialization
# -----------------------------------------------------------------------------
try:
    connect_str = st.secrets["AZURE_CONNECTION_STRING"]
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    quizzes_container = blob_service_client.get_container_client("quizzes")
    results_container = blob_service_client.get_container_client("results")
except Exception as e:
    st.error("Cloud connection failed. Check your Streamlit Secrets.")
    st.stop()

@st.cache_data(ttl=300)
def fetch_quizzes():
    db = {}
    try:
        blobs = quizzes_container.list_blobs()
        for blob in blobs:
            if blob.name.endswith('.json'):
                blob_client = quizzes_container.get_blob_client(blob)
                data = blob_client.download_blob().readall()
                quiz_json = json.loads(data)
                quiz_id = blob.name.replace('.json', '')
                db[quiz_id] = quiz_json
    except Exception:
        pass
    return db

# -----------------------------------------------------------------------------
# 2. Session State & Routing
# -----------------------------------------------------------------------------
if 'user' not in st.session_state:
    st.session_state.user = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

# Initial load of quizzes
if 'QUIZ_DB' not in st.session_state:
    st.session_state.QUIZ_DB = fetch_quizzes()

# Handle Authentication Redirect
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    result = auth.get_token_from_code(auth_code)
    
    if result and "id_token_claims" in result:
        claims = result["id_token_claims"]
        
        # Aggressively hunt for the name across Microsoft's various claim keys
        user_name = claims.get("name") or claims.get("given_name") or claims.get("extension_DisplayName") or "AI Learner"
        
        st.session_state.user = {
            "name": user_name,
            "oid": claims.get("oid", str(uuid.uuid4())), # Unique ID for privacy-safe tracking
            "email": claims.get("preferred_username", claims.get("emails", ["External User"])[0])
        }
        st.query_params.clear()
        st.rerun()

query_params = st.query_params
target_quiz = query_params.get("quiz_id", None)
traffic_source = query_params.get("source", "direct")

# -----------------------------------------------------------------------------
# 3. Application Components
# -----------------------------------------------------------------------------
def login_page():
    st.markdown("<h1 style='text-align: center;'>Welcome to the AI Learning Portal</h1>", unsafe_allow_html=True)
    st.write(f"*(Source: **{traffic_source}**)*")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Please sign in to access your dashboard and track your progress.")
        login_url = auth.get_login_url()
        st.link_button("🚀 Sign In with Microsoft / Social", url=login_url, type="primary", use_container_width=True)

def render_quiz(quiz_id):
    quiz = st.session_state.QUIZ_DB.get(quiz_id)
    if not quiz:
        st.error("Module not found.")
        return

    questions = quiz["questions"]
    total_q = len(questions)
    curr = st.session_state.q_index

    st.progress(curr / total_q)
    st.title(quiz["title"])
    st.markdown(f"**Question {curr + 1} of {total_q}**")
    
    q = questions[curr]
    st.markdown(f"### {q['text']}")
    
    existing_ans = st.session_state.user_answers.get(curr, None)
    idx = q["options"].index(existing_ans) if existing_ans in q["options"] else None
    choice = st.radio("Select your answer:", q["options"], index=idx, key=f"radio_{curr}")

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c1:
        if curr > 0:
            if st.button("← Previous", use_container_width=True):
                st.session_state.user_answers[curr] = choice
                st.session_state.q_index -= 1
                st.rerun()

    with c3:
        if curr < total_q - 1:
            if st.button("Next →", use_container_width=True, type="primary"):
                st.session_state.user_answers[curr] = choice
                st.session_state.q_index += 1
                st.rerun()
        else:
            if st.button("Submit Answers ✓", use_container_width=True, type="primary"):
                st.session_state.user_answers[curr] = choice
                score = sum(1 for i, q_data in enumerate(questions) if st.session_state.user_answers.get(i) == q_data["answer"])
                
                # Privacy-safe payload using Azure OID
                result_payload = {
                    "user_id": st.session_state.user['oid'],
                    "quiz_id": quiz_id,
                    "title": quiz["title"],
                    "date": datetime.datetime.now().isoformat(),
                    "score": score,
                    "total": total_q
                }
                
                # Save locally and to Azure
                st.session_state.history.append(result_payload)
                try:
                    blob_name = f"res_{st.session_state.user['oid'][:8]}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json"
                    results_container.get_blob_client(blob_name).upload_blob(json.dumps(result_payload))
                except:
                    pass
                
                st.session_state.q_index = 0
                st.session_state.user_answers = {}
                st.success(f"### Completed! Score: {score} / {total_q}")
                if score == total_q: st.balloons()

# -----------------------------------------------------------------------------
# 4. Main Router
# -----------------------------------------------------------------------------
if st.session_state.user is None:
    login_page()
else:
    if target_quiz and target_quiz in st.session_state.QUIZ_DB:
        if st.button("← Back to Dashboard"):
            st.query_params.clear()
            st.session_state.q_index = 0
            st.session_state.user_answers = {}
            st.rerun()
        render_quiz(target_quiz)
    else:
        render_dashboard(st.session_state.QUIZ_DB)