import streamlit as st
import requests
import json
import os
import tempfile
import time
import logging
from dotenv import load_dotenv
import base64
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# HARDCODED API KEYS - DO NOT SHARE THIS FILE
OPENAI_API_KEY =    os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

# Initialize theme in session state if not present
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'

# Set page config
st.set_page_config(
    page_title="Assignment Grader",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for custom styling
def local_css():
    # Base styles
    st.markdown("""
    <style>
        /* General styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Card styling */
        div.stButton > button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            font-weight: 500;
            background: linear-gradient(to right, rgb(24 74 27), rgb(72 148 59), rgb(104 212 109));
            color: white;
            border: none;
            transition: all 0.3s ease;
        }
        
        div.stButton > button:hover {
            background: linear-gradient(to right, #1B5E20, #2E7D32);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            # transform: translateY(-2px);
        }
        
        /* Primary button styling */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(to right, #1565C0, #1976D2);
        }
        
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(to right, #0D47A1, #1565C0);
        }
        
        /* Custom header styling */
        .custom-header {
            background: linear-gradient(to right, #1b5e20, #2e7d32);
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            color: white;
            text-align: center;
        }
        
        /* Custom card styling */
        .custom-card {
            background-color: rgba(46, 125, 50, 0.1);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(46, 125, 50, 0.2);
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(46, 125, 50, 0.05);
            border-radius: 8px 8px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            padding-left: 10px;
            padding-right: 10px;
        }

        .stTabs [aria-selected="true"] {
            background-color: rgba(46, 125, 50, 0.2);
            border-bottom: 2px solid #2e7d32;
        }
        
        /* Light mode overrides */
        .light-mode .custom-header {
            background: linear-gradient(to right, #4CAF50, #2E7D32);
        }
        
        .light-mode .custom-card {
            background-color: #c8e6c9;
            border: 1px solid #a5d6a7;
        }
        
        .light-mode .stTabs [data-baseweb="tab"] {
            background-color: #c8e6c9;
        }
        
        .light-mode .stTabs [aria-selected="true"] {
            background-color: #a5d6a7;
            border-bottom: 2px solid #2E7D32;
        }
        .stSelectbox{
        margin-left: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

# Apply theme class to body based on current theme
def apply_theme():
    if st.session_state['theme'] == 'light':
        st.markdown('<style>body { background-color: #e8f5e9; color: #000000; } .light-mode { display: block; }</style>', unsafe_allow_html=True)
    else:
        st.markdown('<style>body { background-color: #0a1f14; color: #ffffff; } .light-mode { display: none; }</style>', unsafe_allow_html=True)

# Apply CSS
local_css()
apply_theme()

# Custom header with logo and title
st.markdown("""
<div class="custom-header">
    <h1>📝 Assignment Grader</h1>
    <p>Intelligent AI-powered assignment evaluation system</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'api_server_url' not in st.session_state:
    st.session_state['api_server_url'] = "http://localhost:8088"

# Always use our hardcoded keys - don't get them from session_state
st.session_state['openai_api_key'] = OPENAI_API_KEY
st.session_state['google_api_key'] = GOOGLE_API_KEY
st.session_state['google_cx'] = GOOGLE_CX

# Function to call API tools
def call_api_tool(tool_name, data):
    """Call a tool on the API server with hardcoded API keys."""
    url = f"{st.session_state['api_server_url']}/tools/{tool_name}"
    
    # Create a copy of the data
    request_data = data.copy()
    
    # ALWAYS add API keys to EVERY request
    request_data["openai_api_key"] = OPENAI_API_KEY
    request_data["google_api_key"] = GOOGLE_API_KEY
    request_data["search_engine_id"] = GOOGLE_CX
    
    # Log the API call (but hide most of the keys)
    log_data = request_data.copy()
    if "openai_api_key" in log_data:
        key = log_data["openai_api_key"]
        log_data["openai_api_key"] = f"{key[:5]}...{key[-5:]}"
    if "google_api_key" in log_data:
        key = log_data["google_api_key"]
        log_data["google_api_key"] = f"{key[:5]}...{key[-5:]}"
    
    logger.info(f"Calling {tool_name} with data: {json.dumps(log_data)}")
    print(request_data)
            
    try:
        response = requests.post(
            url, 
            json=request_data,
            headers={"Content-Type": "application/json"}, 
            timeout=60
        )
        
        if response.status_code != 200:
            error_message = f"Error {response.status_code} from server: {response.text}"
            logger.error(error_message)
            st.error(error_message)
            return None
            
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text
            
    except Exception as e:
        error_message = f"Error connecting to server: {str(e)}"
        logger.error(error_message)
        st.error(error_message)
        return None

# Sidebar configuration
with st.sidebar:
    # Theme toggle
    st.markdown("### 🎨 Appearance")
    theme_col1, theme_col2 = st.columns([1, 1])
    
    # Custom CSS for theme buttons
    st.markdown("""
    <style>
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:first-child div.stButton > button {
            background: linear-gradient(to right, #1A237E, #283593);
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:last-child div.stButton > button {
            background: linear-gradient(to right, #FF6F00, #FFA000);
            color: #212121;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with theme_col1:
        if st.button("🌙 Dark Mode", use_container_width=True, disabled=st.session_state['theme']=='dark'):
            st.session_state['theme'] = 'dark'
            st.rerun()
    with theme_col2:
        if st.button("☀️ Light Mode", use_container_width=True, disabled=st.session_state['theme']=='light'):
            st.session_state['theme'] = 'light'
            st.rerun()
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Server configuration
    st.markdown("### ⚙️ Server Configuration")
    with st.expander("Server Settings", expanded=True):
        # API server URL
        server_url = st.text_input("API Server URL", value=st.session_state['api_server_url'])
        
        # Save button
        # Custom CSS for server URL save button
        st.markdown("""
        <style>
            div.stExpander div.stButton > button {
                background: linear-gradient(to right, #0277BD, #039BE5);
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("💾 Save Server URL", use_container_width=True):
            st.session_state['api_server_url'] = server_url
            st.success(f"✅ Server URL updated to {server_url}")

# Check server connection
with st.sidebar:
    st.markdown("### 🖥️ Server Status")
    with st.expander("Connection Status", expanded=False):
        # Custom CSS for connection check button
        st.markdown("""
        <style>
            div.stExpander:nth-of-type(2) div.stButton > button {
                background: linear-gradient(to right, #558B2F, #7CB342);
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("🔄 Check Connection", use_container_width=True):
            with st.spinner("Connecting to server..."):
                try:
                    response = requests.get(f"{st.session_state['api_server_url']}/")
                    if response.status_code == 200:
                        st.success("✅ Server is online!")
                        st.json(response.json())
                    else:
                        st.warning(f"⚠️ Server responded with status {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"❌ Failed to connect: {str(e)}")

# Test API keys
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    with st.expander("Test API Keys", expanded=False):
        # Custom CSS for API keys validation button
        st.markdown("""
        <style>
            div.stExpander:nth-of-type(3) div.stButton > button {
                background: linear-gradient(to right, #F57F17, #FBC02D);
                color: #212121;
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("🧪 Validate API Keys", use_container_width=True):
            with st.spinner("Testing API keys..."):
                try:
                    # Test endpoint
                    data = {
                        "openai_api_key": OPENAI_API_KEY,
                        "google_api_key": GOOGLE_API_KEY,
                        "search_engine_id": GOOGLE_CX
                    }
                    
                    response = requests.post(
                        f"{st.session_state['api_server_url']}/test_keys", 
                        json=data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ API keys are valid!")
                        st.json(response.json())
                    else:
                        st.warning(f"⚠️ API key test failed with status {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    st.error(f"❌ Test failed: {str(e)}")
    
    # Add app info and version
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.markdown(f"""<div style='text-align: center; opacity: 0.7;'>
        <p>Version 1.0.0</p>
        <p>Last updated: {datetime.now().strftime('%b %d, %Y')}</p>
    </div>""", unsafe_allow_html=True)

# Create tabs with icons
tab1, tab2, tab3 = st.tabs(["📤 Upload", "⚖️ Grade", "📊 Results"])

# Tab 1: Upload Assignment
with tab1:
    st.markdown("""<div class='custom-card'>
        <h2>📤 Upload Assignment</h2>
        <p>Upload a student assignment file for processing and grading.</p>
    </div>""", unsafe_allow_html=True)
    
    # File upload with custom styling
    st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 20px; border-radius: 10px; border: 1px dashed rgba(46, 125, 50, 0.3);'>
        <h3>Select Assignment File</h3>
    </div>""", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx'])
    
    if uploaded_file is not None:
        # Display file information with better styling
        file_size = len(uploaded_file.getvalue()) / 1024  # KB
        st.markdown(f"""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 20px; border-radius: 10px; border-left: 4px solid #2E7D32; margin-bottom: 15px;'>
            <h3 style='margin-top: 0;'>📄 {uploaded_file.name}</h3>
            <p style='margin-bottom: 5px;'><strong>Size:</strong> {file_size:.1f} KB</p>
            <p style='margin-bottom: 0;'><strong>Uploaded:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>""", unsafe_allow_html=True)
        
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            file_path = tmp_file.name
        
        st.session_state['file_path'] = file_path
        st.session_state['file_name'] = uploaded_file.name
        
        # Process button below the file information
        process_col1, process_col2, process_col3 = st.columns([1, 1, 1])
        with process_col2:
            # Custom CSS for process button
            st.markdown("""
            <style>
                div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) div.stButton > button {
                    background: linear-gradient(to right, #00796B, #009688);
                    font-size: 1.1em;
                    font-weight: bold;
                }
            </style>
            """, unsafe_allow_html=True)
            process_button = st.button("⏳ Process", use_container_width=True)
        
        # Parse the document
        if process_button:
                with st.spinner("Processing document..."):
                    result = call_api_tool("parse_file", {"file_path": file_path})
                    
                    if result is None:
                        st.error("Failed to process document. Check server connection.")
                    elif isinstance(result, str):
                        # If result is a string, it's either the document text or an error message
                        st.session_state['document_text'] = result
                        word_count = len(result.split())
                        
                        # Success and Info cards in a row
                        success_col, info_col = st.columns(2)
                        with success_col:
                            st.markdown(f"""<div style='background-color: rgba(38, 166, 154, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #26a69a;'>
                                <h4 style='margin-top: 0; color: #26a69a;'>✅ Success</h4>
                                <p style='margin-bottom: 0;'>Document processed successfully!</p>
                            </div>""", unsafe_allow_html=True)
                        
                        with info_col:
                            st.markdown(f"""<div style='background-color: rgba(3, 169, 244, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #03a9f4;'>
                                <h4 style='margin-top: 0; color: #03a9f4;'>ℹ️ Info</h4>
                                <p style='margin-bottom: 0;'>Document contains <strong>{word_count}</strong> words.</p>
                            </div>""", unsafe_allow_html=True)
                        
                        # Document Preview section below the status cards
                        st.markdown("<br>", unsafe_allow_html=True)
                        with st.expander("Document Preview", expanded=True):
                            st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 10px;'>
                                <h4 style='margin-top: 0; margin-bottom: 10px;'>Document Content</h4>
                            </div>""", unsafe_allow_html=True)
                            preview = result[:2000] + ("..." if len(result) > 2000 else "")
                            st.text_area("Preview", value=preview, height=400, disabled=True, key="document_preview")
                            
                            # If document is very long, show a warning below the preview
                        if word_count > 5000:
                            st.markdown(f"""<div style='background-color: rgba(255, 152, 0, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #ff9800; margin: 15px 0;'>
                                <h4 style='margin-top: 0; color: #ff9800;'>⚠️ Warning</h4>
                                <p style='margin-bottom: 0;'>Long document detected ({word_count} words). Processing might take longer.</p>
                            </div>""", unsafe_allow_html=True)
                    else:
                        # If result is a dict, might be error information
                        st.session_state['document_text'] = str(result)
                        
                        # Success message
                        st.markdown(f"""<div style='background-color: rgba(38, 166, 154, 0.1); padding: 15px; border-radius: 10px; border-left: 4px solid #26a69a; margin-bottom: 15px;'>
                            <h4 style='margin-top: 0; color: #26a69a;'>✅ Success</h4>
                            <p style='margin-bottom: 0;'>Document processed!</p>
                        </div>""", unsafe_allow_html=True)
                        
                        # Show a preview below the success message
                        with st.expander("Document Preview", expanded=True):
                            st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.05); padding: 10px; border-radius: 8px; margin-bottom: 10px;'>
                                <h4 style='margin-top: 0; margin-bottom: 10px;'>Document Content (JSON Format)</h4>
                            </div>""", unsafe_allow_html=True)
                            st.json(result)

# Tab 2: Grade Assignment
with tab2:
    st.markdown("""<div class='custom-card'>
        <h2>⚖️ Grading Configuration</h2>
        <p>Configure grading parameters and evaluate the uploaded assignment.</p>
    </div>""", unsafe_allow_html=True)
    
    # Check if document is loaded
    if 'document_text' not in st.session_state:
        st.warning("⚠️ Please upload and process a document first.")
    else:
        st.success(f"✅ Document loaded: {st.session_state.get('file_name', 'Unknown')}")
    
    # Rubric input
    st.subheader("Grading Rubric")
    
    # Default rubric templates
    rubric_templates = {
        "Default Academic": """Content (40%): The assignment should demonstrate a thorough understanding of the topic.
Structure (20%): The assignment should be well-organized with a clear introduction, body, and conclusion.
Analysis (30%): The assignment should include critical analysis backed by evidence.
Grammar & Style (10%): The assignment should be free of grammatical errors and use appropriate academic language.""",
        "Technical Report": """Accuracy (35%): Technical details should be accurate and well-explained.
Methodology (25%): The methodology should be appropriate and clearly described.
Results (25%): Results should be presented clearly with appropriate visualizations.
Conclusions (15%): Conclusions should be supported by the data and analysis.""",
        "Creative Writing": """Originality (30%): The work should show creative and original thinking.
Structure (20%): The narrative structure should be effective and appropriate.
Character/Scene Development (30%): Characters or scenes should be well-developed.
Language & Style (20%): The language should be engaging, varied, and appropriate.""",
    }
    
    # Template selector with improved styling
    st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
        <h3>🧩 Rubric Configuration</h3>
    </div>""", unsafe_allow_html=True)
    
    template_choice = st.selectbox(
        "Select a template or create your own:", 
        list(rubric_templates.keys()) + ["Custom"],
        help="Choose a predefined rubric template or create your own custom rubric"
    )
    
    # Get default value based on selection
    default_value = rubric_templates.get(template_choice, "") if template_choice != "Custom" else ""
    
    # Rubric text area
    rubric = st.text_area(
        "Enter your grading rubric here:",
        height=200,
        help="Specify the criteria on which the assignment should be graded",
        value=default_value
    )
    
    # Plagiarism check and grading options
    col1, col2 = st.columns(2)
    with col1:
        check_plagiarism = st.checkbox("Check for plagiarism", value=True)
        
        if check_plagiarism:
            similarity_threshold = st.slider(
                "Similarity threshold (%)", 
                min_value=1, 
                max_value=90, 
                value=40,
                help="Minimum similarity percentage to flag potential plagiarism"
            )
            
    with col2:
        st.markdown("""<div style='border-radius: 10px;'>
            <h5>🤖 Select AI Model</h5>
        </div>""", unsafe_allow_html=True)
        
        grade_model = st.selectbox(
            "AI Model for Grading",
            ["gpt-3.5-turbo", "gpt-4"],
            help="Select the AI model to use for grading (affects accuracy and cost)"
        )
    
    # Grade Assignment button with improved styling
    if 'document_text' in st.session_state:
        st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 15px; border-radius: 10px; margin: 20px 0;'>
            <h3>🚀 Start Grading</h3>
            <p>Click below to begin the grading process using the configured settings.</p>
        </div>""", unsafe_allow_html=True)
        
        # Custom CSS for grade button
        st.markdown("""
        <style>
            div.stButton > button[kind="primary"] {
                background: linear-gradient(to right, #1565C0, #42A5F5);
                font-size: 1.2em;
                font-weight: bold;
                padding: 0.5em 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            div.stButton > button[kind="primary"]:hover {
                background: linear-gradient(to right, #0D47A1, #1976D2);
                box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
            }
        </style>
        """, unsafe_allow_html=True)
        if st.button("🧠 Grade Assignment", type="primary", use_container_width=True):
            # Store rubric in session
            st.session_state['rubric'] = rubric
            
            with st.spinner("Grading in progress..."):
                progress_bar = st.progress(0)
                
                # Optional plagiarism check
                if check_plagiarism:
                    st.info("📊 Checking for plagiarism...")
                    
                    plagiarism_data = {
                        "text": st.session_state['document_text'],
                        "similarity_threshold": similarity_threshold if 'similarity_threshold' in locals() else 40
                    }
                    
                    plagiarism_results = call_api_tool("check_plagiarism", plagiarism_data)
                    st.session_state['plagiarism_results'] = plagiarism_results
                    
                    progress_bar.progress(33)
                else:
                    progress_bar.progress(33)
                
                # Generate grade
                st.info("🧮 Generating grade...")
                
                grade_data = {
                    "text": st.session_state['document_text'], 
                    "rubric": rubric,
                    "model": grade_model if 'grade_model' in locals() else "gpt-3.5-turbo"
                }
                
                grade_results = call_api_tool("grade_text", grade_data)
                st.session_state['grade_results'] = grade_results
                
                progress_bar.progress(66)
                
                # Generate feedback
                st.info("✍️ Generating detailed feedback...")
                
                feedback_data = {
                    "text": st.session_state['document_text'], 
                    "rubric": rubric,
                    "model": grade_model if 'grade_model' in locals() else "gpt-3.5-turbo"
                }
                
                feedback = call_api_tool("generate_feedback", feedback_data)
                st.session_state['feedback'] = feedback
                
                progress_bar.progress(100)
                
                if grade_results is not None or feedback is not None:
                    st.success("✅ Grading completed!")
                    st.balloons()
                else:
                    st.error("❌ Grading process encountered errors. Please check your server connection and API settings.")

# Tab 3: Results
with tab3:
    st.markdown("""<div class='custom-card'>
        <h2>📊 Grading Results</h2>
        <p>View detailed evaluation results and feedback.</p>
    </div>""", unsafe_allow_html=True)
    
    if all(k in st.session_state for k in ['file_name']):
        st.markdown(f"""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h3>📝 Results for: {st.session_state['file_name']}</h3>
            <p>Evaluation completed on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
        </div>""", unsafe_allow_html=True)
        
        # Display grade in a centered layout
        grade_col1, grade_col2, grade_col3 = st.columns([1, 2, 1])
        
        with grade_col2:
            if 'grade_results' in st.session_state and st.session_state['grade_results'] is not None:
                if isinstance(st.session_state['grade_results'], dict):
                    grade = st.session_state['grade_results'].get('grade', 'Not available')
                else:
                    # If it's not a dict, just display the raw result
                    grade = str(st.session_state['grade_results'])
                
                # Display grade in large format with better styling
                grade_color = "#4CAF50" if any(g in grade.upper() for g in ['A', '90', '95']) else \
                             "#8BC34A" if any(g in grade.upper() for g in ['B', '80', '85']) else \
                             "#FFC107" if any(g in grade.upper() for g in ['C', '70', '75']) else \
                             "#FF9800" if any(g in grade.upper() for g in ['D', '60', '65']) else "#F44336"
                
                st.markdown(f"""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 20px; border-radius: 10px; text-align: center;'>
                    <h1 style='font-size: 3.5rem; color: {grade_color};'>{grade[:8]}</h1>
                    <p>Final Grade</p>
                </div>""", unsafe_allow_html=True)
                
                # Generate a visual indicator based on the grade
                try:
                    # Try to convert to numeric format if it's a percentage or out of 100
                    if '%' in grade:
                        numeric_grade = float(grade.replace('%', ''))
                        st.progress(numeric_grade / 100)
                    elif '/' in grade:
                        parts = grade.split('/')
                        numeric_grade = float(parts[0]) / float(parts[1])
                        st.progress(numeric_grade)
                    elif grade.upper() in ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F']:
                        grade_values = {
                            'A+': 0.97, 'A': 0.94, 'A-': 0.90,
                            'B+': 0.87, 'B': 0.84, 'B-': 0.80,
                            'C+': 0.77, 'C': 0.74, 'C-': 0.70,
                            'D+': 0.67, 'D': 0.64, 'D-': 0.60,
                            'F': 0.50
                        }
                        numeric_grade = grade_values.get(grade.upper(), 0)
                        st.progress(numeric_grade)
                except:
                    # If we can't convert, just skip the progress bar
                    pass
            else:
                st.warning("Grade information is not available.")
                st.metric("Grade", "Not available")
        
        # Display feedback below the grade
        st.markdown("<br>", unsafe_allow_html=True)
        if 'feedback' in st.session_state and st.session_state['feedback'] is not None:
            st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
                <h3 style='margin-top: 0;'>Feedback</h3>
            </div>""", unsafe_allow_html=True)
            # st.markdown("""<div style='background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border: 1px solid rgba(46, 125, 50, 0.2);'>""", unsafe_allow_html=True)
            st.markdown(st.session_state['feedback'])
            st.markdown("""</div>""", unsafe_allow_html=True)
        else:
            st.warning("Feedback is not available.")
        
        # Display plagiarism results if available
        if 'plagiarism_results' in st.session_state and st.session_state['plagiarism_results']:
            st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.05); padding: 15px; border-radius: 10px; margin: 20px 0 15px 0;'>
                <h3 style='margin-top: 0;'>Plagiarism Check</h3>
            </div>""", unsafe_allow_html=True)
            results = st.session_state['plagiarism_results']
            
            if results is None:
                st.warning("Plagiarism check results are not available.")
            elif isinstance(results, dict) and 'error' in results:
                st.error(f"Plagiarism check error: {results['error']}")
            elif isinstance(results, dict) and 'results' in results:
                # New API format
                st.markdown("**Similarity matches found:**")
                for item in results['results'][:3]:
                    url = item.get('url', '')
                    similarity = item.get('similarity', 0)
                    
                    if similarity > 70:
                        st.warning(f"⚠️ High similarity ({similarity}%): [{url}]({url})")
                    elif similarity > 40:
                        st.info(f"ℹ️ Moderate similarity ({similarity}%): [{url}]({url})")
                    else:
                        st.success(f"✅ Low similarity ({similarity}%): [{url}]({url})")
            else:
                # Old API format
                st.markdown("**Similarity matches found:**")
                if isinstance(results, dict):
                    for url, similarity in results.items():
                        if similarity > 70:
                            st.warning(f"⚠️ High similarity ({similarity}%): [{url}]({url})")
                        elif similarity > 40:
                            st.info(f"ℹ️ Moderate similarity ({similarity}%): [{url}]({url})")
                        else:
                            st.success(f"✅ Low similarity ({similarity}%): [{url}]({url})")
                else:
                    st.json(results)  # Display raw results if format is unknown
        
        # Export options with better styling
        st.markdown("""<div style='background-color: rgba(46, 125, 50, 0.1); padding: 15px; border-radius: 10px; margin: 20px 0 10px 0;'>
            <h3>💾 Export Options</h3>
            <p>Save or export your grading results</p>
        </div>""", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            # Custom CSS for export button
            st.markdown("""
            <style>
                div[data-testid="column"]:first-child div.stButton > button {
                    background: linear-gradient(to right, #AD1457, #D81B60);
                }
            </style>
            """, unsafe_allow_html=True)
            if st.button("📥 Export to PDF", use_container_width=True):
                st.info("Creating PDF report...")
                # This is where you would implement PDF export
                st.download_button(
                    label="Download PDF",
                    data=b"Placeholder for PDF content",  # Replace with actual PDF data
                    file_name=f"grading_report_{st.session_state['file_name']}.pdf",
                    mime="application/pdf",
                    disabled=True  # Enable when implemented
                )
                st.info("PDF export functionality would go here")
        
        with col2:
            # Custom CSS for save button
            st.markdown("""
            <style>
                div[data-testid="column"]:last-child div.stButton > button {
                    background: linear-gradient(to right, #4527A0, #673AB7);
                }
            </style>
            """, unsafe_allow_html=True)
            if st.button("💾 Save to Database", use_container_width=True):
                st.info("Saving to database...")
                # This is where you would implement database save
                time.sleep(1)
                st.success("Record saved! (This is a placeholder)")
                st.info("Database save functionality would go here")
    else:
        st.info("No grading results available. Please upload and grade an assignment first.")

# Add footer with better styling
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; opacity: 0.7; padding: 20px 0;'>
    <p>📝 Assignment Grader | Powered by FastAPI and OpenAI</p>
    <p>Built with ❤️ for educators and students</p>
</div>
""", unsafe_allow_html=True)