import streamlit as st
import pandas as pd
import datetime

# Notice we now pass QUIZ_DB as an argument here
def render_dashboard(QUIZ_DB): 
    # -----------------------------------------
    # Sidebar: User Profile
    # -----------------------------------------
    avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={st.session_state.user['name']}&backgroundColor=0052cc"
    
    st.sidebar.image(avatar_url, width=80)
    st.sidebar.title(st.session_state.user['name'])
    st.sidebar.caption("📍 Folsom, CA | AI Solution Architect") 
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio("Navigation", ["My Progress", "Course Catalog"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()

    # -----------------------------------------
    # Main Page: My Progress
    # -----------------------------------------
    if page == "My Progress":
        st.markdown("<h1 style='text-align: center; color: #0052cc; padding-bottom: 20px;'>AI Solution Architect Welcomes you</h1>", unsafe_allow_html=True)
        
        if not st.session_state.history:
            st.info("You haven't attempted any quizzes yet. Head to the Course Catalog to start your journey!")
        else:
            df = pd.DataFrame(st.session_state.history)
            df['date'] = pd.to_datetime(df['date'])
            df['Accuracy %'] = (df['score'] / df['total']) * 100
            df_sorted = df.sort_values(by="date", ascending=False).reset_index(drop=True)

            st.markdown("### 👤 Profile Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Total Attempts", value=len(df))
            with col2:
                st.metric(label="Highest Score", value=f"{df['score'].max()} / {df['total'].iloc[0]}")
            with col3:
                st.metric(label="Average Accuracy", value=f"{df['Accuracy %'].mean():.1f}%")
            
            st.markdown("---")
            st.markdown("### 📈 Learning Trend")
            
            chart_data = df.sort_values(by="date", ascending=True).copy()
            chart_data['Attempt Sequence'] = range(1, len(chart_data) + 1)
            st.line_chart(data=chart_data.set_index('Attempt Sequence'), y='Accuracy %', color="#0052cc", height=300)

            st.markdown("---")
            st.markdown("### 🕒 Recent History")
            
            display_df = df_sorted.copy()
            display_df['Date & Time'] = display_df['date'].dt.strftime("%b %d, %Y - %I:%M %p")
            display_df['Accuracy'] = display_df['Accuracy %'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(display_df[['Date & Time', 'title', 'score', 'total', 'Accuracy']], use_container_width=True, hide_index=True)

    # -----------------------------------------
    # Main Page: Course Catalog
    # -----------------------------------------
    elif page == "Course Catalog":
        st.markdown("<h1 style='text-align: center; color: #0052cc; padding-bottom: 20px;'>Course Catalog</h1>", unsafe_allow_html=True)
        
        # Now uses the dynamic QUIZ_DB passed from Azure
        if not QUIZ_DB:
            st.warning("No courses are currently available. Check back later!")
        else:
            for q_id, q_data in QUIZ_DB.items():
                with st.expander(f"📖 {q_data['title']} (Category: {q_data.get('category', 'General')})"):
                    st.write(f"Contains {len(q_data['questions'])} questions.")
                    if st.button("Start Module", key=f"start_{q_id}", type="primary"):
                        st.query_params.quiz_id = q_id
                        st.rerun()

    current_year = datetime.datetime.now().year
    st.markdown(
        f"""
        <hr style="margin-top: 50px;">
        <div style='text-align: center; padding: 10px; font-size: 14px; color: gray;'>
            &copy; {current_year} AI Solution Architect. All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )