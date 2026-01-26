import streamlit as st
import google.generativeai as genai
import markdown
import pandas as pd
import io
import docx
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from pyairtable import Api

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

# --- SESSION STATE ---
if 'chapter_log' not in st.session_state:
    st.session_state.chapter_log = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = ""

# --- API SETUP ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("⚠️ API Key missing. Please check Secrets.")

# --- 📚 PROJECT CONFIGURATION (THE FILING CABINET) ---
PROJECTS = {
    "❄️ Chione Trilogy": {
        "base_id": "apphWWXcojkv7nPni",  # The Base ID for Chione
        "tables": {
            "Main Codex": "tblVIzhmAnBxCXbtU",
            "Characters": "tblPYX2dWW6q1aJuM",
            "Locations": "tblhi6WcDzZ7ycTQV",
            "Laws & Lore": "tblVIzhmAnBxCXbtU",
            "Glossary": "tblyJohOidLdC3dZ6",
            "Scenes": "tblZ3wc6zUW9oQ4rM",
            "Master data digest": "tblpYgBSnNz3QBtPD"

        }
    },
    "🌵 The Gatekeepers": {
        "base_id": "appS0RBUAeRGaSsOl",  
        "tables": {
            "Characters": "tbl1b3FoNzVdIxIS6",
            "Locations": "tblMMVh7qA3wovl8t",
            "Scenes": "tblVIzhmAnBxCXbtU",
            "Ironless Earth world-building": "tblzeWkM2S7FvSrGl"
        }
    }
}

# --- AIRTABLE FUNCTION (Updated for Dynamic Bases) ---
@st.cache_data(ttl=600)
def fetch_airtable_data(base_id, table_id):
    try:
        if "AIRTABLE_TOKEN" in st.secrets:
            api = Api(st.secrets["AIRTABLE_TOKEN"])
            table = api.table(base_id, table_id)
            records = table.all()
            data = [r['fields'] for r in records]
            return pd.DataFrame(data)
        else:
            return None
    except Exception as e:
        if "REPLACE" in table_id or "appXXX" in base_id:
            return pd.DataFrame({"Info": ["Please configure IDs in app.py"]})
        st.error(f"Airtable Error: {e}")
        return None

# --- HELPERS ---
def read_file(uploaded_file):
    if uploaded_file is None: return ""
    if uploaded_file.name.endswith(".docx"):
        try:
            doc = docx.Document(uploaded_file)
            full_text = []
            for para in doc.paragraphs: full_text.append(para.text)
            return "\n".join(full_text)
        except: return ""
    elif uploaded_file.name.endswith(".txt"):
        try: return uploaded_file.read().decode("utf-8")
        except: return ""
    return ""

def create_html_report(content, title):
    html_content = markdown.markdown(content, extensions=['tables'])
    return f"<html><body><h1>{title}</h1>{html_content}</body></html>"

def clean_markdown_text(text):
    if not isinstance(text, str): return text
    text = text.replace('**', '').replace('__', '').replace('### ', '').replace('## ', '').replace('# ', '')
    return text

def to_excel(df):
    export_df = df.copy()
    for col in export_df.columns:
        export_df[col] = export_df[col].apply(clean_markdown_text)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Story Map')
        workbook = writer.book
        worksheet = writer.sheets['Story Map']
        header_fill = PatternFill(start_color="008080", end_color="008080", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=12, name="Calibri")
        row_fill_even = PatternFill(start_color="F0F8FF", end_color="F0F8FF", fill_type="solid") 
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')
                if row_idx % 2 == 0: cell.fill = row_fill_even
        for i, col in enumerate(export_df.columns):
            worksheet.column_dimensions[chr(65 + i)].width = 25
    return output.getvalue()

# --- BRAINS ---
def analyze_scene(text, genre, framework, beat):
    prompt = f"""
    You are a ruthless Story Grid editor. Analyze this SCENE.
    STYLE: RUTHLESSLY CONCISE. Use Markdown Tables.
    CONTEXT: Genre: {genre} | Framework: {framework} | Beat: {beat}
    OUTPUT FORMAT:
    1. HEADER: "# [Emoji] [Start Value] ➔ [End Value]"
    2. THE 5 COMMANDMENTS (Bullet points)
    3. VISUAL SCOREBOARD (Markdown Table: Element, Start Value, End Value, Notes)
    """
    if "None" not in framework: prompt += f"\n4. FRAMEWORK CHECK ({framework}): Verdict & Reason."
    prompt += f"\n5. GENRE CHECK: Gold Star Moment 🌟\n\nSTORY TEXT: {text}"
    model = genai.GenerativeModel('gemini-flash-latest')
    return model.generate_content(prompt).text

def analyze_outline(text, genre, framework):
    prompt = f"Analyze this PLOT OUTLINE against {framework}. Output Structural Health Score, Gap Analysis, and Pacing Check.\n\nTEXT: {text}"
    model = genai.GenerativeModel('gemini-flash-latest')
    return model.generate_content(prompt).text

# --- UI START ---
st.markdown("""
<style>
    /* Make headers Teal */
    h1, h2, h3 { color: #008080 !important; }
    
    /* Style the big buttons */
    div.stButton > button:first-child {
        border-radius: 10px;
        font-weight: bold;
        border: 2px solid #008080;
    }
    
    /* Make the metrics stand out */
    div[data-testid="stMetricValue"] {
        color: #008080;
    }
</style>
""", unsafe_allow_html=True)

# --- UI START ---

# 1. SIDEBAR (The Control Room)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2038/2038263.png", width=50) # Optional Icon
    st.title("Navigator")
    
    # Project Selection with clear visual grouping
    st.markdown("### 🗂️ Active Project")
    selected_project_name = st.selectbox("Select Book/Series", list(PROJECTS.keys()), label_visibility="collapsed")
    
    # Load Config
    current_config = PROJECTS[selected_project_name]
    current_base_id = current_config["base_id"]
    current_tables = current_config["tables"]

    st.divider()
    
    st.markdown("### ⚙️ Analysis Config")
    selected_genre = st.selectbox("Genre", ["Action/Thriller", "Love Story", "Horror", "Mystery/Crime", "Sci-Fi/Fantasy", "Drama", "Non-Fiction"])
    selected_framework = st.selectbox("Framework", ["None (Pure Story Grid)", "Save the Cat!", "Dan Harmon's Story Circle", "Fichtean Curve"])
    
    st.divider()
    
    # Metrics in Sidebar
    scene_count = len(st.session_state.chapter_log)
    st.metric("Scenes Logged", scene_count, delta=f"+{1 if scene_count > 0 else 0} this session")
    
    if st.button("🗑️ Clear Session Data"):
        st.session_state.chapter_log = []
        st.rerun()

# 2. MAIN DASHBOARD HEADER
st.title(f"{selected_project_name}")
st.caption(f"Story Grid Analyzer Pro • {selected_genre} • {selected_framework}")

# Top Metric Row (The "Command Center" feel)
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("World Status", "Connected", "Online")
with m2: st.metric("Bible Entries", "Live", "Airtable")
with m3: st.metric("Scenes Tracked", scene_count)
with m4: st.metric("Draft Health", "Pending Analysis")

st.markdown("---")

# 3. TABS (Clean & Logical)
tab1, tab2, tab3 = st.tabs(["🩺 Outline Doctor", "🔬 Scene Logger", "📚 World Codex"])

# === TAB 1: OUTLINE DOCTOR ===
with tab1:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("#### 📄 Upload Manuscript")
        uploaded_outline = st.file_uploader("Drop your full outline or synopsis here", type=["docx", "txt"], key="outline_file")
        outline_text_area = read_file(uploaded_outline) if uploaded_outline else ""
        
    with c2:
        st.info("💡 **Pro Tip:** Paste your entire 'Foolscap' or beat sheet here for a structural check-up.")
        
    outline_input = st.text_area("Or paste text directly:", value=outline_text_area, height=300)
    
    if st.button("✨ Run Structural Diagnosis", type="primary", use_container_width=True):
        if outline_input:
            with st.spinner("🤖 Reading your story structure..."):
                try:
                    diagnosis = analyze_outline(outline_input, selected_genre, selected_framework)
                    st.markdown(diagnosis)
                    st.balloons() # <--- BELLS AND WHISTLES!
                except Exception as e: st.error(f"Error: {e}")
        else:
            st.warning("Please upload or paste text first.")

# === TAB 2: SCENE LOGGER ===
with tab2:
    st.markdown("#### 🎬 Scene Analysis Engine")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Group inputs in a nice container
        with st.container(border=True):
            chapter_title = st.text_input("Chapter / Scene Title", placeholder="e.g. Chapter 1: The Arrival")
            uploaded_scene = st.file_uploader("Upload Scene Document", type=["docx", "txt"], key="scene_file")
            
            scene_text_area = read_file(uploaded_scene) if uploaded_scene else ""
            scene_input = st.text_area("Scene Text", value=scene_text_area, height=250, placeholder="Paste scene text here...")
            
            # The Big Button
            if st.button("🚀 Analyze Scene", type="primary", use_container_width=True):
                if scene_input:
                    with st.spinner("Analyzing beats and commandments..."):
                        try:
                            report = analyze_scene(scene_input, selected_genre, selected_framework, "General Scene")
                            st.session_state.current_report = report
                            st.toast("Analysis Complete! 🍞", icon="✅") # <--- MODERN TOAST POPUP
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
                else:
                    st.toast("Please enter text first", icon="⚠️")

    with col2:
        st.markdown("**Beat Settings**")
        selected_beat = st.pills("Scene Type", ["Action", "Reactive", "Inciting Incident", "Climax"], selection_mode="single")
        
        if st.session_state.current_report:
            st.success("✅ Report Ready")
            if st.button("➕ Add to Project Log", use_container_width=True):
                st.session_state.chapter_log.append({"Chapter": chapter_title, "Analysis": st.session_state.current_report})
                st.toast("Saved to Project Table!", icon="💾")
            
            st.download_button("📥 Download HTML", create_html_report(st.session_state.current_report, chapter_title), "report.html", use_container_width=True)

    # Report Display Area
    if st.session_state.current_report:
        with st.expander("📝 View Full Analysis Report", expanded=True):
            st.markdown(st.session_state.current_report)

# === TAB 3: WORLD CODEX (MULTI-BASE SUPPORT) ===
with tab3:
    # Layout: Sidebar navigation for the Codex on the left, Content on the right
    col_a, col_b = st.columns([1, 4])
    
    with col_a:
        st.markdown("#### 📖 Library")
        # Fancy radio buttons
        selected_table_key = st.radio("Select Category:", list(current_tables.keys()), label_visibility="collapsed")
        selected_table_id = current_tables[selected_table_key]
    
    with col_b:
        # Fetch Data
        df_airtable = fetch_airtable_data(current_base_id, selected_table_id)
        
        if df_airtable is not None and not df_airtable.empty:
            # Search bar with a magnifying glass icon
            search_query = st.text_input(f"Search {selected_table_key}...", placeholder=f"Find in {selected_project_name}...", label_visibility="collapsed")
            
            if search_query:
                mask = df_airtable.apply(lambda x: x.astype(str).str.contains(search_query, case=False).any(), axis=1)
                display_df = df_airtable[mask]
            else:
                display_df = df_airtable

            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(display_df)} records • Live from Airtable")
        else:
            if "REPLACE" in selected_table_id:
                st.warning("⚠️ Configuration Needed in app.py")
            else:
                st.info(f"No records found in {selected_table_key}.")

# === GLOBAL PROJECT TABLE (Footer) ===
st.divider()
if len(st.session_state.chapter_log) > 0:
    st.subheader("📊 Session Log")
    df = pd.DataFrame(st.session_state.chapter_log)
    st.dataframe(df, use_container_width=True)
    st.download_button("📥 Download Excel Log", to_excel(df), "story_grid_project.xlsx", type="primary")
else:
    st.caption("Start analyzing scenes to build your session log.")