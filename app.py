import streamlit as st
import os
import re
import chardet
import json
import hashlib
import numpy as np
import plotly.graph_objects as go
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

st.title("🤖 NX CodeBot (Python Generator + Explainer + 3D Preview)")
st.write("Generate NXOpen Python code, get AI explanation (with formulas), and visualize in 3D.")

example_selected = st.selectbox("Select an operation:", example_files)

st.write("Optional Parameters (comma-separated, e.g., 100,100,50) for templates with placeholders.")
param_input = st.text_input("Enter parameters separated by comma")

# --------------------------
# Utilities
# --------------------------
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

    system_prompt = """You are an expert Siemens NX CAD assistant. 
    Explain the NXOpen Python code clearly in steps. 
    - If geometric formulas (volume, area, etc.) apply, include them in LaTeX form.
    - Keep explanation concise and easy to follow."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Explain this NXOpen Python code:\n{code_snippet}"}
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
        return f"⚠️ Failed to get explanation from Groq API: {e}"

def replace_params_in_code(code, param_list):
    matches = re.findall(r"\{param(\d+)\}", code)
    max_param = max([int(m) for m in matches], default=0)
    for i in range(1, max_param + 1):
        param_val = param_list[i-1] if len(param_list) >= i else "0"
        code = code.replace(f"{{param{i}}}", param_val)
    return code

# --------------------------
# 3D Shape Visualization
# --------------------------
def plot_block(x=100, y=100, z=100):
    X, Y, Z = np.meshgrid([0, x], [0, y], [0, z])
    fig = go.Figure(data=[go.Mesh3d(
        x=X.flatten(), y=Y.flatten(), z=Z.flatten(),
        color='lightblue', opacity=0.5
    )])
    fig.update_layout(scene=dict(aspectmode="data"))
    return fig

def plot_cylinder(radius=50, height=100):
    theta = np.linspace(0, 2*np.pi, 50)
    z = np.linspace(0, height, 20)
    theta, z = np.meshgrid(theta, z)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    fig = go.Figure(data=[go.Surface(x=x, y=y, z=z, colorscale="Blues")])
    fig.update_layout(scene=dict(aspectmode="data"))
    return fig

def render_3d_preview(filename, params):
    """Simple shape detection based on filename."""
    if "block" in filename.lower():
        dims = [int(p) if p.isdigit() else 50 for p in params[:3]] + [0,0,0]
        return plot_block(dims[0], dims[1], dims[2])
    elif "cylinder" in filename.lower():
        r = int(params[0]) if len(params) > 0 and params[0].isdigit() else 50
        h = int(params[1]) if len(params) > 1 and params[1].isdigit() else 100
        return plot_cylinder(r, h)
    else:
        return None

# --------------------------
# Main Action
# --------------------------
if st.button("Generate Code + Explain + Preview"):
    example_path = os.path.join(EXAMPLES_DIR, example_selected)
    try:
        code = read_script_auto_encode(example_path)
        params = [p.strip() for p in param_input.split(",")] if param_input.strip() else []
        code_with_params = replace_params_in_code(code, params)

        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.subheader("📜 NXOpen Python Code")
            st.code(code_with_params, language="python")

        with col2:
            st.subheader("📖 AI Explanation")
            with st.spinner("Generating explanation..."):
                explanation = get_code_description(code_with_params)
            st.markdown(explanation)

        with col3:
            st.subheader("🖼️ 3D Preview")
            fig = render_3d_preview(example_selected, params)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No 3D preview available for this operation.")

    except FileNotFoundError:
        st.error(f"❌ File not found: {example_selected}")
    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("---")
st.markdown(
    """
    ## How to use
    1. Select an NX operation.
    2. Enter parameters if required (comma-separated).
    3. Click **Generate** to:
       - View generated Python code
       - Get AI explanation with formulas
       - See a 3D preview of the shape
    """
)
