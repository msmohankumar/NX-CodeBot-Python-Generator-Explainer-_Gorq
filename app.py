import streamlit as st
import os
import re
import chardet
import json
import hashlib
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve Groq API key securely
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY not set in environment variables. Please add it to your .env file.")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

EXAMPLES_DIR = "nx_examples"
IMAGES_DIR = "images"
CACHE_FILE = "description_cache.json"

# Load or initialize explanation cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        description_cache = json.load(f)
else:
    description_cache = {}

example_files = [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".py")]

st.set_page_config(page_title="🤖 NX CodeBot", layout="wide")

st.title("🤖 NX CodeBot (Python Generator + Explainer)")
st.write("Select an operation, provide parameters if needed, then generate NXOpen Python code with AI explanation.")

example_selected = st.selectbox("Select an operation:", example_files)

st.write("Optional Parameters (comma-separated, e.g., 100,100,50) for templates with placeholders.")
param_input = st.text_input("Enter parameters separated by comma")

def read_script_auto_encode(path):
    with open(path, "rb") as f:
        raw_data = f.read()
    detected = chardet.detect(raw_data)
    encoding = detected.get('encoding', 'utf-8') or 'utf-8'
    try:
        return raw_data.decode(encoding)
    except Exception:
        return raw_data.decode("utf-8", errors="ignore")

def get_cache_key(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_code_description(code_snippet):
    cache_key = get_cache_key(code_snippet)
    if cache_key in description_cache:
        return description_cache[cache_key]

    system_prompt = "You are an expert CAD developer assistant. Explain the following Siemens NXOpen Python code snippet in clear, concise steps."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Explain this code:\n{code_snippet}"}
    ]
    try:
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        explanation = chat_completion.choices[0].message.content
        description_cache[cache_key] = explanation
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(description_cache, f, ensure_ascii=False, indent=2)
        return explanation
    except Exception as e:
        return f"Failed to get explanation from Groq API: {e}"

def replace_params_in_code(code, param_list):
    matches = re.findall(r"\{param(\d+)\}", code)
    max_param = max([int(m) for m in matches], default=0)
    for i in range(1, max_param + 1):
        param_val = param_list[i-1] if len(param_list) >= i else "0"
        code = code.replace(f"{{param{i}}}", param_val)
    return code

if st.button("Generate Code and Explain"):
    example_path = os.path.join(EXAMPLES_DIR, example_selected)
    try:
        code = read_script_auto_encode(example_path)
        params = [p.strip() for p in param_input.split(",")] if param_input.strip() else []
        code_with_params = replace_params_in_code(code, params)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Generated NXOpen Python Code")
            st.code(code_with_params, language="python")

        with col2:
            st.subheader("Code Explanation by Groq API")
            with st.spinner("Generating explanation..."):
                explanation = get_code_description(code_with_params)
            st.markdown(explanation)

        # Show related image if exists
        img_file = os.path.join(IMAGES_DIR, example_selected.replace(".py", ".png"))
        if os.path.exists(img_file):
            st.image(img_file, caption=f"Illustration: {example_selected}", use_column_width=True)

    except FileNotFoundError:
        st.error(f"❌ File not found: {example_selected}")
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("---")
st.markdown(
    """
    ## How to use
    - Select an operation.
    - Enter parameters if any.
    - Click the button to generate code and AI explanation.
    - Copy generated code to Siemens NX journal to run.
    """
)
