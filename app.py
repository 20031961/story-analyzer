import streamlit as st
import requests
import pandas as pd

# ==========================================
# 1. APP CONFIGURATION & SETUP
# ==========================================
st.set_page_config(
    page_title="Story Analyzer",
    page_icon="❄️",
    layout="wide"
)

# Initialize Session State for Login
if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "chapter_log" not in st.session_state:
    st.session_state.chapter_log = []

# Load Secrets
try:
    config = {
        "api_key": st.secrets["AIRTABLE_API_KEY"],
        "base_id": st.secrets["AIRTABLE_BASE_ID"],
        "codex_table_id": st.secrets["AIRTABLE_TABLE_ID"],
        "project_name": "Chione Trilogy",
        "icon": "❄️",
        "language": "American English"
    }
except Exception as e:
    st.error(f"❌ Configuration Error: {e}")
    st.stop()

# ==========================================
# 2. HELPER FUNCTIONS (The Engine Room)
# ==========================================
@st.cache_data(ttl=60)
def fetch_master_codex(base_id, table_id):
    """Fetches all records from Airtable."""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    all_records = []
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_records.extend(data.get('records', []))
        
        while 'offset' in data:
            params = {'offset': data['offset']}
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            all_records.extend(data.get('records', []))
            
        return all_records
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return []

def add_to_codex(base_id, table_id, name, category, description):
    """Writes a new record to Airtable."""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "Name": name,
            "Category": category,
            "Description": description,
            "Role": "New Entry" # Default status
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Save Failed: {e}")
        return False

# ==========================================
# 3. AUTHENTICATION (The Gatekeeper)
# ==========================================
def check_password():
    # If already logged in, pass
    if st.session_state.user_role:
        return True

    st.title("🔒 Codex Access")
    
    with st.form("login_form"):
        password = st.text_input("Enter Password", type="password")
        submitted = st.form_submit_button("Enter")
        
        if submitted:
            if password == "Helle":
                st.session_state.user_role = "admin"
                st.rerun()
            elif password == "Guest":
                st.session_state.user_role = "guest"
                st.rerun()
            else:
                st.error("⛔ Password incorrect.")
                
    return False

# Stop app if not logged in
if not check_password():
    st.stop()

# Define permission variable
is_admin = (st.session_state.user_role == "admin")

# ==========================================
# 4. SIDEBAR (Unified Config & Tools)
# ==========================================
with st.sidebar:
       st.title("Navigator")
    
    # --- A. Status Badge ---
    if is_admin:
        st.success(f"🔑 **Admin Mode**\n\nActive: {config['project_name']}")
    else:
        st.info("👀 **Guest Mode**\n\nViewing: Safe Demo")

    st.divider()

    # --- B. Analysis Config (Visible to All) ---
    st.markdown("### ⚙️ Analysis Config")
    selected_genre = st.selectbox("Genre", ["Action/Thriller", "Love Story", "Horror", "Mystery/Crime", "Sci-Fi/Fantasy", "Western"])
    selected_framework = st.selectbox("Framework", ["None (Pure Story Grid)", "Save the Cat!", "Romancing the Beat", "Hero's Journey"])
    
    st.metric("Scenes Logged", len(st.session_state.chapter_log))
    
    if st.button("🗑️ Clear Session Data"):
        st.session_state.chapter_log = []
        st.rerun()

    # --- C. CREATOR TOOLS (ADMIN ONLY) ---
    if is_admin:
        st.divider()
        st.markdown("### ✍️ Creator Tools")
        with st.expander("➕ Quick Add to Codex", expanded=False):
            with st.form("add_record_form", clear_on_submit=True):
                new_name = st.text_input("Name", placeholder="e.g. The Crystal Key")
                new_cat = st.selectbox("Category", ["Character", "Location", "Lore", "Item", "Faction"])
                new_desc = st.text_area("Description", placeholder="A brief summary...")
                
                if st.form_submit_button("Save to Airtable"):
                    if add_to_codex(config["base_id"], config["codex_table_id"], new_name, new_cat, new_desc):
                        st.toast(f"Saved {new_name}!", icon="💾")
                        fetch_master_codex.clear()
                        st.rerun()

# ==========================================
# 5. MAIN PAGE LOGIC (Fork in the Road)
# ==========================================

# --- PATH A: GUEST VIEW (Safe Mode) ---
if not is_admin:
    st.title("👋 Welcome to Story Analyzer")
    st.markdown("""
    ### You are currently in Guest Mode.
    
    This is a safe, read-only demonstration of the Story Analyzer app. 
    The Admin's active project data (The Chione Trilogy) is **hidden** to prevent spoilers.
    
    #### 🚀 How to use this App:
    1.  **Check the Sidebar:** You can see the configuration options on the left.
    2.  **Coming Soon:** We are building a 'Dummy Project' for you to explore here.
    3.  **Login:** If you are the Creator, please refresh and log in as 'Helle'.
    """)
    st.divider()
    st.caption("🔒 Restricted Access: Read-Only")
    st.stop() # <--- STOPS APP HERE FOR GUESTS


# --- PATH B: ADMIN VIEW (Real App) ---
# 1. Main Headers
col_h1, col_h2 = st.columns([1, 6])
with col_h1: st.write("") # Spacer
with col_h2: 
    st.title(config["project_name"])
    st.caption(f"Story Grid Analyzer Pro • {selected_genre} • {config['language']}")

# 2. Metrics
codex = fetch_master_codex(config["base_id"], config["codex_table_id"])
scenes_tracked = len(st.session_state.chapter_log)

m1, m2, m3, m4 = st.columns(4)
m1.metric("World Status", "Online", delta="Connected")
m2.metric("Codex Items", len(codex), delta="Read/Write") 
m3.metric("Scenes Tracked", scenes_tracked)
m4.metric("Draft Health", "In Progress")

st.divider()

# 3. The Tabs
tab1, tab2, tab3 = st.tabs(["📝 Outline Drafter", "🔮 Scene Logger", "🌍 World Codex"])

with tab1:
    st.info("Drag and drop your text file here for a check-up.")
    uploaded_file = st.file_uploader("Upload Chapter", type=["txt", "md"])

with tab2:
    st.write("### Scene Logger")
    st.write("Scene logging tools will appear here.")

with tab3:
    # CODEX SEARCH & DISPLAY
    categories = set([r['fields'].get('Category') for r in codex])
    valid_categories = sorted([c for c in categories if c and isinstance(c, str)])
    
    if not valid_categories:
        st.warning("No categories found.")
    else:
        sub_tabs = st.tabs(valid_categories)
        for i, cat in enumerate(valid_categories):
            with sub_tabs[i]:
                # Filter strictly by category
                df_filtered = [r for r in codex if r['fields'].get('Category') == cat]
                
                # Search Bar
                search = st.text_input(f"Search {cat}...", key=f"search_{cat}")
                
                # Render Cards
                if not df_filtered:
                    st.info(f"No {cat} entries found.")
                else:
                    for item in df_filtered:
                        fields = item['fields']
                        name = fields.get('Name', 'Unnamed')
                        
                        # Apply Search Filter
                        if search and search.lower() not in name.lower():
                            continue
                            
                        role = fields.get('Role', '')
                        display_name = f"{name} ({role})" if role else name
                        
                        st.subheader(display_name)
                        if 'Description' in fields:
                            st.write(fields['Description'])
                        if 'Details' in fields:
                            st.markdown(fields['Details'])
                        st.markdown("---")