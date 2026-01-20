import streamlit as st
import google.generativeai as genai

# 1. Setup
st.title("System Diagnostic Tool")
st.write("Inspecting server status...")

# 2. Check Library Version
try:
    version = genai.__version__
    st.success(f"Library Version: {version}")
    if version < "0.8.0":
        st.error("❌ Version is too old! We need at least 0.8.0")
    else:
        st.info("✅ Version is good.")
except Exception as e:
    st.error(f"Could not read version: {e}")

# 3. Check Connection & Models
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    st.write("Attempting to connect to Google...")
    
    # Ask Google for a list of available models
    models = list(genai.list_models())
    
    st.write("### Available Models found:")
    found_flash = False
    
    for m in models:
        # Print the exact name the computer wants
        st.text(f"- {m.name}")
        if "flash" in m.name:
            found_flash = True
            
    if found_flash:
        st.success("✅ The server SEES the Flash model!")
    else:
        st.error("❌ The server cannot find Flash. Access might be restricted.")

except Exception as e:
    st.error(f"⚠️ Connection Failed: {e}")
    st.write("Double check your API Key in Secrets.")