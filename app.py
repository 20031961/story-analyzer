import streamlit as st
import google.generativeai as genai
import markdown
import pandas as pd

# 1. SETUP
st.set_page_config(
    page_title="Story Grid Analyzer Pro",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True
    st.title("🔒 Login Required")
    password = st.text_input("Enter Password", type="password")
    if st.button("Enter"):
        if password == "story2026": 
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("😕 Incorrect password")
    return False

if not check_password():
    st.stop()

# --- SESSION STATE INITIALIZATION (The Memory) ---
if 'chapter_log' not in st.session_state:
    st.session_state.chapter_log = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = ""

# --- API SETUP ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("⚠️ API Key missing. Please check Secrets.")

# --- HELPER: DOWNLOAD HTML ---
def create_html_report(content, title):
    html_content = markdown.markdown(content)
    return f"<html><body><h1>{title}</h1>{html_content}</body></html>"

# --- BRAIN 1: SCENE ANALYZER ---
def analyze_scene(text, genre, framework, beat):
    prompt = f"""
    You are a ruthless Story Grid editor. Analyze this SCENE.
    STYLE: Concise. Bullet points. Visual Scoreboard.
    
    CONTEXT: Genre: {genre} | Framework: {framework} | Beat: {beat}
    
    OUTPUT FORMAT:
    1. HEADER: "# [Emoji] [Start Value] ➔ [End Value]"
    2. THE 5 COMMANDMENTS (Bullet points)
    """
    if "None" not in framework:
        prompt += f"\n3. FRAMEWORK CHECK ({framework}): Verdict (✅ PASS / ❌ FAIL) and 1 sentence reason."
    
    prompt += f"\n4. GENRE CHECK: Gold Star Moment 🌟\n\nSTORY TEXT: {text}"
    
    model = genai.GenerativeModel('gemini-flash-latest')
    return model.generate_content(prompt).text

# --- BRAIN 2: OUTLINE DOCTOR ---
def analyze_outline(text, genre, framework):
    if "None" not in framework:
        prompt = f"""
        Analyze this PLOT OUTLINE against {framework} structure.
        OUTPUT: 
        1. Structural Health Score (0-10)
        2. Gap Analysis (✅ Found / ❌ Missing)
        3. Pacing Check
        """
    else:
        prompt = f"""
        Analyze this PLOT OUTLINE for Global 5 Commandments.
        OUTPUT:
        1. Narrative Arc Score (0-10)
        2. Global 5 Commandments Check
        3. Gap Analysis
        """
    prompt += f"\nOUTLINE TEXT: {text}"
    model = genai.GenerativeModel('gemini-flash-latest')
    return model.generate_content(prompt).text

# --- UI ---
st.title("Story Grid Analyzer Pro 🧬")

with st.sidebar:
    st.header("🎛️ Project Settings")
    st.caption("Logged in")
    selected_genre = st.selectbox("Genre", ["Action/Thriller", "Love Story", "Horror", "Mystery/Crime", "Sci-Fi/Fantasy", "Drama", "Non-Fiction"])
    selected_framework = st.selectbox("Structure Framework", ["None (Pure Story Grid)", "Save the Cat!", "Dan Harmon's Story Circle", "Fichtean Curve"])
    
    st.divider()
    st.markdown("### 🗑️ Project Data")
    if st.button("Clear Project Table"):
        st.session_state.chapter_log = []
        st.success("Table cleared!")
        st.rerun()

# TABS
tab1, tab2 = st.tabs(["🔬 Scene Logger", "🩺 Outline Doctor"])

# === TAB 1: SCENE LOGGER ===
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 1. Analyze Chapter")
        chapter_title = st.text_input("Chapter Name", placeholder="e.g. Chapter 1: The Arrival")
        
        beat_options = ["N/A"]
        if "Save the Cat" in selected_framework:
            beat_options = ["Opening Image", "Catalyst", "Debate", "Fun and Games", "All is Lost", "Finale"]
        elif "Story Circle" in selected_framework:
            beat_options = ["1. YOU", "2. NEED", "3. GO", "4. SEARCH", "5. FIND", "6. TAKE", "7. RETURN", "8. CHANGE"]
        
        if "None" not in selected_framework:
            selected_beat = st.selectbox("Beat", beat_options)
        else:
            selected_beat = "General Scene"

        scene_input = st.text_area("Paste Text:", height=200, key="scene_in")

        if st.button("🚀 Analyze Scene", type="primary"):
            if scene_input:
                with st.spinner("Analyzing..."):
                    try:
                        # Run AI
                        report = analyze_scene(scene_input, selected_genre, selected_framework, selected_beat)
                        # Save to Session State so it persists
                        st.session_state.current_report = report
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    with col2:
        st.markdown("### 2. Review & Log")
        if st.session_state.current_report:
            st.info("Analysis Ready below ⬇️")
            # The "Add to Log" Button
            if st.button("➕ Add to Project Table"):
                # Append data to the list
                new_entry = {
                    "Chapter": chapter_title,
                    "Beat": selected_beat,
                    "Verdict": "See Report", 
                    "Full Analysis": st.session_state.current_report
                }
                st.session_state.chapter_log.append(new_entry)
                st.success(f"Saved {chapter_title}!")
        else:
            st.markdown("*Run an analysis to see results here.*")

    # DISPLAY REPORT (Full Width)
    if st.session_state.current_report:
        st.markdown("---")
        st.markdown(st.session_state.current_report)

    # DISPLAY PROJECT TABLE (Bottom)
    st.markdown("---")
    st.subheader("📊 Project Table (Your Book Map)")
    
    if len(st.session_state.chapter_log) > 0:
        # Convert list to DataFrame
        df = pd.DataFrame(st.session_state.chapter_log)
        st.dataframe(df, use_container_width=True)
        
        # CSV Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Project CSV",
            csv,
            "my_novel_analysis.csv",
            "text/csv",
            key='download-csv'
        )
    else:
        st.caption("No chapters logged yet. Analyze a scene and click 'Add to Project Table'.")

# === TAB 2: OUTLINE DOCTOR ===
with tab2:
    st.markdown("### 🚑 Structural Health Check")
    if "None" not in selected_framework:
        st.info(f"Checking against **{selected_framework}** beats.")
    else:
        st.info("Checking for **Global 5 Commandments**.")
    
    outline_input = st.text_area("Paste Full Plot Outline:", height=300)
    
    if st.button("Diagnose Outline", type="primary"):
        if outline_input:
            with st.spinner("Diagnosing..."):
                try:
                    diagnosis = analyze_outline(outline_input, selected_genre, selected_framework)
                    st.markdown(diagnosis)
                except Exception as e:
                    st.error(f"Error: {e}")