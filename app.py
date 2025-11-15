import streamlit as st
import os
import re
import chardet
import numpy as np
import plotly.graph_objects as go
from groq import Groq
from dotenv import load_dotenv
from fpdf import FPDF
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import time


# --- 1. Initialization ---
st.set_page_config(page_title="NX CodeBot Pro", page_icon="🔩", layout="wide")
load_dotenv()


groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY") or st.secrets.get("HUGGINGFACE_API_KEY")


if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found. Please set it in your environment or Streamlit secrets.")
    st.stop()


groq_client = Groq(api_key=groq_api_key)


EXAMPLES_DIR = "nx_examples"

# Enhanced system prompt with strict requirements for production-ready code
MASTER_SYSTEM_PROMPT_BASE = """You are an expert Siemens NX automation engineer specializing in NXOpen Python API development.

CRITICAL REQUIREMENTS FOR CODE GENERATION:
1. Generate COMPLETE, PRODUCTION-READY code that can run WITHOUT modifications
2. Follow NXOpen API best practices exactly as shown in the reference examples
3. Include ALL necessary imports (NXOpen, NXOpen.Features, etc.)
4. Use proper error handling with try-except blocks
5. Include proper session management (theSession, workPart)
6. Follow this EXACT structure:
   - Import statements
   - main() function with all logic
   - Proper feature builder pattern (Create → Set Parameters → Commit → Destroy)
   - if __name__ == '__main__' block
7. Use {param1}, {param2}, etc. as placeholders for user parameters
8. Include proper unit handling (millimeters by default)
9. Add descriptive variable names matching NX conventions
10. Ensure all builders are properly destroyed after commit

MANDATORY CODING PATTERNS:
- Always use: theSession = NXOpen.Session.GetSession()
- Always use: workPart = theSession.Parts.Work
- Always create features through builders
- Always commit and destroy builders
- Always return created feature objects from main()

Generate code that an NX user can copy-paste and run immediately."""


# --- 2. Session State ---
if "generated_data" not in st.session_state:
    st.session_state.generated_data = {
        "code": None,
        "explanation": None,
        "similarity_explanation": None,
        "figure": None,
        "image_url": None,
        "report": None,
        "params": [],
        "example_name": "",
        "raw_ai_response": "",
        "closest_example_name": None,
        "closest_example_similarity": None
    }


# --- 3. Example Loading and Retrieval ---
@st.cache_data
def load_examples(ex_dir):
    names = []
    codes = []
    if not os.path.isdir(ex_dir):
        return names, codes
    for fname in os.listdir(ex_dir):
        if fname.endswith(".py"):
            fpath = os.path.join(ex_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                names.append(fname)
                codes.append(txt)
            except Exception as e:
                st.warning(f"Error reading example {fname}: {e}")
    return names, codes


@st.cache_data
def build_vectorizer_and_matrix(docs):
    if not docs:
        return None, None
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.95,
        sublinear_tf=True
    )
    matrix = vectorizer.fit_transform(docs)
    return vectorizer, matrix


def extract_keywords_from_prompt(prompt):
    """Extract meaningful keywords from user prompt."""
    prompt_lower = prompt.lower()
    
    shape_keywords = [
        "block", "cube", "box", "cylinder", "pipe", "tube", 
        "sphere", "ball", "cone", "edge", "blend", "fillet",
        "hole", "boss", "extrude", "revolve", "sweep", "loft",
        "chamfer", "draft", "shell", "pattern", "mirror"
    ]
    
    filename_match = re.search(r"(\w+)\.py", prompt_lower)
    if filename_match:
        return filename_match.group(1)
    
    for keyword in shape_keywords:
        if keyword in prompt_lower:
            return keyword
    
    words = re.findall(r'\b[a-z]{3,}\b', prompt_lower)
    return words[0] if words else prompt_lower


def find_nearest_example(user_prompt, vectorizer, matrix, names, codes):
    """Enhanced similarity matching with multiple strategies."""
    if not vectorizer or matrix is None:
        return None, None, None
    
    prompt_lower = user_prompt.lower()
    
    # Strategy 1: Direct filename match
    for i, name in enumerate(names):
        name_without_ext = name.replace('.py', '').lower()
        if name_without_ext in prompt_lower or prompt_lower in name_without_ext:
            return names[i], codes[i], 0.95
    
    # Strategy 2: Keyword-based matching
    keyword = extract_keywords_from_prompt(user_prompt)
    for i, name in enumerate(names):
        name_without_ext = name.replace('.py', '').lower()
        if keyword and keyword in name_without_ext:
            return names[i], codes[i], 0.85
    
    # Strategy 3: Enhanced TF-IDF
    expanded_prompt = user_prompt
    if len(user_prompt.split()) < 5:
        expanded_prompt = f"{user_prompt} create generate NXOpen python code CAD feature primitive"
    
    prompt_vec = vectorizer.transform([expanded_prompt])
    sims = cosine_similarity(matrix, prompt_vec).flatten()
    
    idx = int(sims.argmax())
    base_similarity = float(sims[idx])
    
    keyword = extract_keywords_from_prompt(user_prompt)
    if keyword and keyword in codes[idx].lower():
        base_similarity = min(0.95, base_similarity + 0.3)
    
    if base_similarity < 0.5 and keyword:
        for i, code in enumerate(codes):
            if keyword in code.lower() or keyword in names[i].lower():
                return names[i], codes[i], 0.75
    
    return names[idx], codes[idx], base_similarity


def extract_code_patterns(example_code):
    """Extract key patterns from example code for better AI learning."""
    patterns = {
        "imports": [],
        "session_init": "",
        "builder_pattern": "",
        "commit_pattern": "",
        "parameter_usage": []
    }
    
    # Extract import statements
    import_lines = re.findall(r'^import .*$|^from .* import .*$', example_code, re.MULTILINE)
    patterns["imports"] = import_lines
    
    # Extract session initialization
    session_match = re.search(r'theSession\s*=\s*NXOpen\.Session\.GetSession\(\)', example_code)
    if session_match:
        patterns["session_init"] = session_match.group(0)
    
    # Extract builder creation pattern
    builder_match = re.search(r'(\w+Builder\d*\s*=\s*\w+\.Create\w+Builder\([^)]*\))', example_code)
    if builder_match:
        patterns["builder_pattern"] = builder_match.group(0)
    
    # Extract commit pattern
    commit_match = re.search(r'(\w+\.Commit\(\)[\s\S]*?\w+\.Destroy\(\))', example_code)
    if commit_match:
        patterns["commit_pattern"] = commit_match.group(0)
    
    # Extract parameter placeholders
    param_matches = re.findall(r'\{param\d+\}', example_code)
    patterns["parameter_usage"] = list(set(param_matches))
    
    return patterns


def create_augmented_prompt(user_prompt, example_code, example_name):
    """Create enhanced prompt with code patterns and strict requirements."""
    
    patterns = extract_code_patterns(example_code)
    
    return f"""
{MASTER_SYSTEM_PROMPT_BASE}

# REFERENCE EXAMPLE: {example_name}
Study this working example carefully and replicate its patterns EXACTLY:

{example_code}

# KEY PATTERNS TO FOLLOW FROM THIS EXAMPLE:
1. Imports used: {', '.join(patterns['imports'][:3]) if patterns['imports'] else 'Standard NXOpen imports'}
2. Session initialization: {patterns['session_init'] or 'theSession = NXOpen.Session.GetSession()'}
3. Parameter placeholders: {', '.join(patterns['parameter_usage']) if patterns['parameter_usage'] else '{param1}, {param2}, etc.'}

# USER REQUEST:
{user_prompt}

# YOUR TASK:
Generate COMPLETE, PRODUCTION-READY NXOpen Python code that:
1. Uses the EXACT same coding style as the example above
2. Follows the EXACT same structure (imports, main(), builder pattern)
3. Includes ALL necessary error handling
4. Can be run IMMEDIATELY without modifications (except parameter values)
5. Uses proper NXOpen API calls as shown in the example

IMPORTANT: 
- Copy the example's structure precisely
- Use the same builder create → set parameters → commit → destroy pattern
- Include proper type conversions and unit handling
- Add comments explaining each major step
- Return the created feature from main()

Generate ONLY the complete Python code, no explanations outside the code."""


# --- 4. Utilities ---
@st.cache_data(show_spinner="Reading script...")
def read_script_auto_encode(path):
    try:
        with open(path, "rb") as f:
            raw_data = f.read()
        detected = chardet.detect(raw_data).get('encoding', 'utf-8') or 'utf-8'
        return raw_data.decode(detected, errors="ignore")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


def get_code_description(client, code_snippet):
    """Generate detailed explanation of NXOpen code."""
    
    if code_snippet is None:
        return "❌ ERROR: Code is None - no code was generated or loaded."
    
    code_str = str(code_snippet).strip()
    
    if len(code_str) == 0:
        return "❌ ERROR: Code string is empty - no code content to explain."
    
    if len(code_str) < 10:
        return f"❌ ERROR: Code is too short ({len(code_str)} chars) - possibly incomplete: `{code_str}`"
    
    sys_prompt = """You are a world-class Siemens NX CAD automation expert with deep knowledge of NXOpen API.

Your task is to explain NXOpen Python code clearly and thoroughly.

EXPLANATION STRUCTURE:
1. **Overview**: Brief description of what the code does
2. **Key Components**: Explain major NXOpen objects used
3. **Step-by-Step Breakdown**: Explain each section's purpose
4. **Parameters**: List any parameter placeholders and their purpose
5. **Usage Notes**: Any important considerations for running the code

Be specific about NXOpen classes, methods, and best practices."""
    
    user_content = f"""Analyze and explain this NXOpen Python code in detail:

{code_str}

Provide a comprehensive, production-focused explanation."""
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2,
            max_tokens=2000
        )
        
        explanation = completion.choices[0].message.content
        
        if not explanation or len(explanation.strip()) < 20:
            return "⚠️ AI returned an empty or very short explanation. Please try regenerating."
        
        return explanation
        
    except Exception as e:
        return f"⚠️ API Error while generating explanation: {str(e)}"


def generate_similarity_explanation(client, user_prompt, example_name, example_code, similarity_score):
    """Generate detailed similarity analysis."""
    
    sys_prompt = """You are an expert at analyzing CAD code patterns and explaining similarities.
Focus on technical accuracy and practical application."""
    
    user_content = f"""User's Request: "{user_prompt}"

Matched Example: "{example_name}" (Similarity Score: {similarity_score:.2%})

Example Code Snippet:
{example_code[:800]}

Explain:
1. **Why This Example Matches**: What specific aspects align?
2. **Key NXOpen Patterns**: What API patterns/methods are relevant?
3. **Code Reusability**: What parts can be directly reused?
4. **Adaptations Needed**: What specific changes are required?

Be technical and specific about NXOpen API usage."""
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        
        return completion.choices[0].message.content or "No similarity explanation generated."
        
    except Exception as e:
        return f"⚠️ Error generating similarity explanation: {str(e)}"


def validate_generated_code(code):
    """Validate that generated code meets minimum requirements."""
    
    validation_results = {
        "has_imports": False,
        "has_main_function": False,
        "has_session": False,
        "has_builder": False,
        "has_commit": False,
        "has_destroy": False,
        "quality_score": 0
    }
    
    if not code:
        return validation_results, "No code generated"
    
    code_lower = code.lower()
    
    # Check for required components
    validation_results["has_imports"] = "import nxopen" in code_lower
    validation_results["has_main_function"] = "def main(" in code_lower
    validation_results["has_session"] = "getsession()" in code_lower
    validation_results["has_builder"] = "builder" in code_lower
    validation_results["has_commit"] = ".commit()" in code_lower
    validation_results["has_destroy"] = ".destroy()" in code_lower
    
    # Calculate quality score
    quality_score = sum([
        validation_results["has_imports"] * 20,
        validation_results["has_main_function"] * 20,
        validation_results["has_session"] * 15,
        validation_results["has_builder"] * 15,
        validation_results["has_commit"] * 15,
        validation_results["has_destroy"] * 15
    ])
    
    validation_results["quality_score"] = quality_score
    
    if quality_score >= 90:
        message = "✅ High-quality production-ready code"
    elif quality_score >= 70:
        message = "⚠️ Good code but may need minor adjustments"
    else:
        message = "❌ Code quality below standard - missing critical components"
    
    return validation_results, message


def extract_code_from_response(response_text):
    """Extract Python code from AI response with multiple fallback methods."""
    
    if not response_text:
        return None
    
    # Method 1: Try to find code block with ```
    pattern1 = re.search(r"``````", response_text, re.DOTALL | re.IGNORECASE)
    if pattern1:
        code = pattern1.group(1).strip()
        if len(code) > 50:
            return code
    
    # Method 2: Try to find any code block with ```
    pattern2 = re.search(r"``````", response_text, re.DOTALL)
    if pattern2:
        code = pattern2.group(1).strip()
        if len(code) > 50:
            return code
    
    # Method 3: Look for code between specific markers
    pattern3 = re.search(r"(?:GENERATED CODE|CODE:|Generated NXOpen Code)(.*?)(?:EXPLANATION|$)", 
                        response_text, re.DOTALL | re.IGNORECASE)
    if pattern3:
        code_section = pattern3.group(1)
        code_block = re.search(r"``````", code_section, re.DOTALL)
        if code_block:
            code = code_block.group(1).strip()
            if len(code) > 50:
                return code
    
    # Method 4: If response looks like code, extract it
    if any(keyword in response_text for keyword in ["import NXOpen", "def main", "theSession =", "theSession="]):
        lines = response_text.split('\n')
        code_lines = []
        in_code = False
        for line in lines:
            if 'import' in line.lower() or in_code:
                in_code = True
                code_lines.append(line)
        
        potential_code = '\n'.join(code_lines).strip()
        if len(potential_code) > 50:
            return potential_code
    
    return None


def generate_code_with_example(client, user_prompt, example_code, example_name):
    """Generate production-ready code using example as template."""
    
    augmented_prompt = create_augmented_prompt(user_prompt, example_code, example_name)
    
    try:
        completion = client.chat.completions.create(
            model="groq/compound",
            messages=[
                {"role": "user", "content": augmented_prompt}
            ],
            temperature=0.05,  # Very low for consistency
            max_tokens=4000
        )
        response_text = completion.choices[0].message.content or ""
        
        code = extract_code_from_response(response_text)
        
        return code, response_text
        
    except Exception as e:
        return None, f"API Error: {str(e)}"


def generate_code_from_prompt(client, user_prompt):
    """Generate code without example context."""
    
    prompt = f"""{MASTER_SYSTEM_PROMPT_BASE}

User Request: {user_prompt}

Generate complete, production-ready NXOpen Python code.
Follow all requirements in the system prompt above.
Provide ONLY the Python code in a code block."""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.05,
            max_tokens=3000
        )
        response_text = completion.choices[0].message.content or ""
        
        code = extract_code_from_response(response_text)

        return code, response_text
    except Exception as e:
        return None, f"API Error: {str(e)}"


def replace_params_in_code(code, params):
    if not code:
        return code
    for i, p in enumerate(params, start=1):
        code = code.replace(f"{{param{i}}}", str(p))
    return re.sub(r"\{param\d+\}", "0", code)


def try_guess_shape_and_params(code, prompt):
    """Enhanced shape detection with better pattern matching."""
    
    code_lower = (code or "").lower()
    prompt_lower = (prompt or "").lower()
    
    shape_patterns = {
        "cylinder": ["cylinder", "cylindrical", "pipe", "tube"],
        "block": ["block", "box", "rectangular", "cuboid"],
        "cube": ["cube", "cubic"],
        "sphere": ["sphere", "ball", "spherical"],
        "cone": ["cone", "conical", "taper"],
        "edge_blend": ["edge", "blend", "fillet", "round"],
        "hole": ["hole", "drilling", "bore"],
        "boss": ["boss", "protrusion", "extrude"],
    }
    
    found_shape = None
    
    for shape, aliases in shape_patterns.items():
        for alias in aliases:
            if alias in code_lower or alias in prompt_lower:
                found_shape = shape
                break
        if found_shape:
            break
    
    if not found_shape:
        if "createcylinder" in code_lower:
            found_shape = "cylinder"
        elif "createblock" in code_lower:
            found_shape = "block"
        elif "createsphere" in code_lower:
            found_shape = "sphere"
        elif "createcone" in code_lower:
            found_shape = "cone"
    
    nums = re.findall(r"\d+\.?\d*", code or prompt or "")
    params = [n for n in nums[:5] if n]
    
    if not params:
        params = ["50", "100", "30"]
    
    return found_shape, params


def plot_block(x=50, y=50, z=50):
    x0, x1 = 0, float(x)
    y0, y1 = 0, float(y)
    z0, z1 = 0, float(z)
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    xs, ys, zs = zip(*verts)
    i = [0, 0, 0, 1, 1, 2, 4, 5, 6, 7, 3, 2]
    j = [1, 2, 3, 5, 6, 6, 5, 6, 7, 4, 6, 7]
    k = [2, 3, 0, 6, 7, 4, 0, 1, 2, 5, 7, 4]
    fig = go.Figure(data=[go.Mesh3d(x=xs, y=ys, z=zs, i=i, j=j, k=k, opacity=0.6, color="#1f77b4")])
    fig.update_layout(title_text="Block Preview", scene=dict(aspectmode="data"))
    return fig


def plot_cylinder(radius=25, height=100):
    radius = float(radius)
    height = float(height)
    theta = np.linspace(0, 2 * np.pi, 60)
    z_coords = np.linspace(0, height, 30)
    theta, z_coords = np.meshgrid(theta, z_coords)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    fig = go.Figure(data=[go.Surface(x=x, y=y, z=z_coords, colorscale="Blues")])
    fig.update_layout(title_text="Cylinder Preview", scene=dict(aspectmode="data"))
    return fig


def render_3d_preview(shape, params):
    try:
        if shape in ("block", "cube"):
            dims = [float(p) for p in params[:3]] if len(params) >= 3 else [50.0, 50.0, 50.0]
            return plot_block(*dims)
        elif shape == "cylinder":
            r = float(params[0]) if len(params) > 0 else 25.0
            h = float(params[1]) if len(params) > 1 else 100.0
            return plot_cylinder(r, h)
    except Exception:
        return None
    return None


def create_placeholder_image(shape_name, params):
    """Create a professional placeholder concept art image."""
    
    img = Image.new('RGB', (1024, 1024), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([10, 10, 1014, 1014], outline='#1f77b4', width=5)
    
    for i in range(0, 1024, 50):
        draw.line([(i, 0), (i, 1024)], fill='#e0e0e0', width=1)
        draw.line([(0, i), (1024, i)], fill='#e0e0e0', width=1)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 30)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    title = f"NX CAD: {shape_name.upper()}"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    text_width = bbox[2] - bbox[0]
    draw.text(((1024 - text_width) // 2, 400), title, fill='#1f77b4', font=font_large)
    
    param_text = f"Params: {', '.join(params)}"
    bbox2 = draw.textbbox((0, 0), param_text, font=font_small)
    text_width2 = bbox2[2] - bbox2[0]
    draw.text(((1024 - text_width2) // 2, 500), param_text, fill='#666666', font=font_small)
    
    note = "Concept Preview (PlaceHolder)"
    bbox3 = draw.textbbox((0, 0), note, font=font_small)
    text_width3 = bbox3[2] - bbox3[0]
    draw.text(((1024 - text_width3) // 2, 600), note, fill='#999999', font=font_small)
    
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return buf


def generate_ai_image(api_key, shape_name, params):
    """Always returns a placeholder."""
    
    if not shape_name or shape_name.strip() == "":
        shape_name = "mechanical part"
    
    return create_placeholder_image(shape_name, params)


class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'NX CodeBot Pro Report', 0, 0, 'C')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        safe_title = title.encode('latin-1', 'replace').decode('latin-1')
        self.cell(0, 10, safe_title, 0, 1, 'L')
        self.ln(4)
    def chapter_body(self, content, is_code=False):
        font = 'Courier' if is_code else 'Arial'
        size = 8 if is_code else 11
        self.set_font(font, '', size)
        safe_content = content.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, safe_content)
        self.ln()


def generate_pdf_report(data):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title(f"1. NXOpen Python Code: {data.get('example_name','Script')}")
    pdf.chapter_body(data.get('code',''), is_code=True)
    pdf.chapter_title("2. Code Quality Assessment")
    pdf.chapter_body(data.get("quality_message", "No quality assessment available."))
    pdf.chapter_title("3. Similarity Analysis")
    pdf.chapter_body(data.get("similarity_explanation") or "No similarity analysis available.")
    pdf.chapter_title("4. Code Explanation")
    pdf.chapter_body(data.get("explanation") or "No explanation available.")
    return bytes(pdf.output(dest='S').encode('latin-1', 'replace'))


# --- Load and vectorize examples ---
example_names, example_codes = load_examples(EXAMPLES_DIR)
if example_codes:
    vectorizer, vec_matrix = build_vectorizer_and_matrix(example_codes)
else:
    vectorizer, vec_matrix = None, None


# --- Streamlit UI ---
st.title("🔩 NX CodeBot Pro")
st.markdown("Generate **production-ready** NXOpen Python code from examples or create new scripts with AI.")


with st.sidebar:
    st.header("⚙️ Controls")

    st.markdown("### Generate from Examples")
    example_selected = st.selectbox("Select a CAD Operation:", example_names if example_names else [])
    param_input = st.text_input("Enter Parameters (comma-separated)", "50,80,30")

    if st.button("🚀 Generate from Example") and example_selected:
        fpath = os.path.join(EXAMPLES_DIR, example_selected)
        raw_code = read_script_auto_encode(fpath)
        
        if raw_code and len(raw_code.strip()) > 0:
            params = [p.strip() for p in param_input.split(",") if p.strip()]
            final_code = replace_params_in_code(raw_code, params)

            with st.spinner("🔄 Generating explanation..."):
                explanation = get_code_description(groq_client, final_code)

            shape_guess = example_selected.replace(".py", "")
            fig = render_3d_preview(shape_guess, params)
            
            with st.spinner("🎨 Generating concept art..."):
                img_url = generate_ai_image(huggingface_api_key, shape_guess, params)

            st.session_state.generated_data = {
                "code": final_code,
                "params": params,
                "example_name": example_selected,
                "explanation": explanation,
                "similarity_explanation": None,
                "figure": fig,
                "image_url": img_url,
                "report": None,
                "raw_ai_response": "",
                "closest_example_name": None,
                "closest_example_similarity": None,
                "quality_message": "✅ Example code (pre-validated)"
            }
            st.success("✅ Generated from example.")
        else:
            st.error("❌ Failed to load code from example file.")

    st.markdown("---")

    st.markdown("### 🤖 AI Code Generator")
    ai_prompt = st.text_area("Enter your request here:", "Create NXOpen python code for a cylinder with radius {param1} and height {param2}", height=140)

    if st.button("✨ Generate from AI") and ai_prompt.strip():
        with st.spinner("🔍 Finding similar examples..."):
            if not vectorizer or not example_codes:
                nearest_name = None
                nearest_code = None
                similarity = None
                st.sidebar.info("No examples available for similarity matching.")
            else:
                nearest_name, nearest_code, similarity = find_nearest_example(
                    ai_prompt, vectorizer, vec_matrix, example_names, example_codes
                )
                if nearest_name:
                    st.sidebar.success(f"✅ Found: {nearest_name} ({similarity*100:.1f}% match)")

        if nearest_name and nearest_code:
            with st.spinner("✨ Generating production-ready code..."):
                generated_code, raw_ai_response = generate_code_with_example(
                    groq_client, ai_prompt, nearest_code, nearest_name
                )
        else:
            with st.spinner("✨ Generating code from scratch..."):
                generated_code, raw_ai_response = generate_code_from_prompt(groq_client, ai_prompt)

        if not generated_code or len(generated_code.strip()) < 50:
            st.error(f"❌ AI generation failed or returned invalid code.")
            with st.expander("🔍 Debug: View Raw Response"):
                st.code(raw_ai_response, language="text")
            st.stop()

        # Validate generated code
        validation_results, quality_message = validate_generated_code(generated_code)
        quality_score = validation_results["quality_score"]
        
        if quality_score >= 70:
            st.sidebar.success(f"✅ Code Quality: {quality_score}/100")
        else:
            st.sidebar.warning(f"⚠️ Code Quality: {quality_score}/100 - May need adjustments")
        
        st.sidebar.info(quality_message)

        similarity_explanation = None
        if nearest_name and nearest_code:
            with st.spinner("🔍 Analyzing similarity..."):
                similarity_explanation = generate_similarity_explanation(
                    groq_client, ai_prompt, nearest_name, nearest_code, similarity
                )

        with st.spinner("🔄 Generating detailed explanation..."):
            explanation = get_code_description(groq_client, generated_code)

        with st.spinner("🔍 Detecting shape and parameters..."):
            shape_name, params = try_guess_shape_and_params(generated_code, ai_prompt)
            
            if shape_name:
                st.sidebar.info(f"🔍 Detected shape: {shape_name}")
                st.sidebar.info(f"📏 Parameters: {', '.join(params)}")
            else:
                st.sidebar.warning("⚠️ Could not detect shape automatically")
                shape_name = ai_prompt.split()[0] if ai_prompt else "part"
        
        fig = render_3d_preview(shape_name, params)
        
        with st.spinner("🎨 Generating concept art..."):
            img_url = generate_ai_image(huggingface_api_key, shape_name, params)

        st.session_state.generated_data = {
            "code": generated_code,
            "params": params,
            "example_name": f"AI Generated Script (Based on {nearest_name})" if nearest_name else "AI Generated Script",
            "similarity_explanation": similarity_explanation,
            "explanation": explanation,
            "figure": fig,
            "image_url": img_url,
            "report": None,
            "raw_ai_response": raw_ai_response,
            "closest_example_name": nearest_name,
            "closest_example_similarity": similarity,
            "quality_message": quality_message,
            "quality_score": quality_score
        }
        st.success(f"✅ AI generation completed! Quality Score: {quality_score}/100")

    if st.session_state.generated_data.get("code"):
        st.markdown("---")
        st.header("📄 Download Report")
        if st.button("Generate PDF Report"):
            with st.spinner("Building PDF..."):
                try:
                    st.session_state.generated_data["report"] = generate_pdf_report(st.session_state.generated_data)
                    st.success("PDF built successfully.")
                except Exception as e:
                    st.error(f"Failed to build PDF: {e}")
        if st.session_state.generated_data.get("report"):
            st.download_button("Click to Download PDF", st.session_state.generated_data["report"], "NX_CodeBot_Report.pdf", "application/pdf")


# --- Main tabs ---
if st.session_state.generated_data.get("code"):
    data = st.session_state.generated_data
    
    # Show quality indicator at the top
    if data.get("quality_score"):
        quality_score = data["quality_score"]
        if quality_score >= 90:
            st.success(f"🎯 **Production-Ready Code** (Quality: {quality_score}/100)")
        elif quality_score >= 70:
            st.info(f"✅ **Good Quality Code** (Quality: {quality_score}/100) - Minor adjustments may be needed")
        else:
            st.warning(f"⚠️ **Code Needs Review** (Quality: {quality_score}/100)")
    
    tabs = st.tabs([
        "📜 Code",
        "🎯 Similarity Match",
        "🔎 Similarity Analysis",
        "📖 AI Explanation",
        "🧊 3D Preview",
        "🎨 Concept Art",
        "📝 Raw AI Output"
    ])

    with tabs[0]:
        st.subheader("Generated NXOpen Python Code")
        if data.get("closest_example_name"):
            st.info(f"📌 **Based on Example:** `{data['closest_example_name']}`")
        
        # Show code quality checklist
        if data.get("quality_score"):
            with st.expander("🔍 Code Quality Checklist"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("✅ Has imports" if "import" in data["code"].lower() else "❌ Missing imports")
                    st.write("✅ Has main function" if "def main" in data["code"].lower() else "❌ Missing main function")
                    st.write("✅ Has session management" if "getsession" in data["code"].lower() else "❌ Missing session")
                with col2:
                    st.write("✅ Uses builders" if "builder" in data["code"].lower() else "❌ No builders found")
                    st.write("✅ Has commit" if ".commit()" in data["code"].lower() else "❌ Missing commit")
                    st.write("✅ Has destroy" if ".destroy()" in data["code"].lower() else "❌ Missing destroy")
        
        st.code(data["code"], language="python")
        
        st.download_button(
            label="💾 Download Python Script",
            data=data["code"],
            file_name=f"{data.get('example_name', 'nxopen_script').replace('.py', '')}_generated.py",
            mime="text/x-python"
        )

    with tabs[1]:
        st.subheader("🎯 Similarity Match Analysis")
        if data.get("closest_example_name") and data.get("closest_example_similarity") is not None:
            similarity_pct = data['closest_example_similarity'] * 100
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.metric(
                    label="Match Percentage",
                    value=f"{similarity_pct:.1f}%",
                    delta="High Relevance" if similarity_pct > 50 else "Moderate Relevance"
                )
            
            st.progress(data['closest_example_similarity'])
            
            if similarity_pct >= 70:
                st.success(f"🎯 **Excellent Match** - The example `{data['closest_example_name']}` is highly relevant. Generated code should work with minimal changes.")
            elif similarity_pct >= 40:
                st.info(f"✅ **Good Match** - The example `{data['closest_example_name']}` provides solid patterns. Review generated code before use.")
            else:
                st.warning(f"⚠️ **Moderate Match** - The example `{data['closest_example_name']}` partially matches. Verify generated code carefully.")
            
            st.markdown(f"""
            **Matched Example:** `{data['closest_example_name']}`  
            **Similarity Score:** {similarity_pct:.2f}%  
            **Relevance:** {'High' if similarity_pct > 50 else 'Moderate'}  
            **Code Quality:** {data.get('quality_score', 'N/A')}/100
            """)
        else:
            st.info("No similarity matching was performed (generated from scratch).")

    with tabs[2]:
        st.subheader("🔎 Similarity Analysis")
        if data.get("similarity_explanation"):
            st.markdown(data["similarity_explanation"])
        else:
            st.info("No similarity analysis available. This code was generated without an example context.")

    with tabs[3]:
        st.subheader("📖 AI-Powered Code Explanation")
        explanation_text = data.get("explanation", "No explanation available.")
        st.markdown(explanation_text)

    with tabs[4]:
        st.subheader("🧊 Interactive 3D Preview")
        if data.get("figure"):
            st.plotly_chart(data["figure"], use_container_width=True)
        else:
            st.info("No 3D preview available for this code.")

    with tabs[5]:
        st.subheader("🎨 Part Concept Visualization")
        img_data = data.get("image_url")
        
        if img_data:
            st.image(img_data, caption="CAD Part Concept Preview", use_column_width=True)
            st.info("📌 Showing professional placeholder with shape details")
        else:
            st.warning("⚠️ No concept art was generated.")

    with tabs[6]:
        st.subheader("📝 Raw AI Model Output")
        st.code(data.get("raw_ai_response", "No raw output available"), language="text")
else:
    st.info("⬅️ Select an example or enter a prompt to generate **production-ready** NXOpen Python code.")
