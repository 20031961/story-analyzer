import streamlit as st
import google.generativeai as genai

# Configure the API key securely
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def analyze_story(story_text):
    # This is the "Brain Upgrade" - specific Story Grid instructions
    prompt = """
    You are an expert Story Grid editor. Analyze the submitted scene and identify the 5 Commandments of Storytelling. 
    
    For each commandment, provide:
    1. The specific text/quote from the story that represents it.
    2. A brief explanation of why it fits that commandment.

    Please format your response as a structured report covering:
    
    1. **Inciting Incident** (Is it Causal or Coincidental?)
    2. **Turning Point** (Is it Action or Revelation? How does the value shift?)
    3. **Crisis** (Is it a Best Bad Choice or Irreconcilable Goods?)
    4. **Climax** (What is the active choice made?)
    5. **Resolution** (What is the new status quo?)

    Story text:
    """ + story_text
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# Page Layout
st.title("Story Grid Analyzer 2.0")
st.markdown("### The 5 Commandments Detector")
st.write("Paste your scene below to identify the Inciting Incident, Turning Point, Crisis, Climax, and Resolution.")

story_input = st.text_area("Your Story Scene", height=300)

if st.button("Analyze Scene"):
    if story_input:
        with st.spinner("Searching for the 5 Commandments..."):
            try:
                report = analyze_story(story_input)
                st.markdown(report)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please paste a scene first.")