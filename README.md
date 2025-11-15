# 🔩 NX CodeBot Pro

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://nx-codebot-python-generator-explainer-gorq-naqqcmawtuo6y5sagwo.streamlit.app/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI-Powered NXOpen Python Code Generation System for Siemens NX CAD Automation**

NX CodeBot Pro is an advanced AI-powered application that generates production-ready NXOpen Python scripts for Siemens NX CAD automation. Using state-of-the-art large language models and intelligent similarity matching, it helps engineers and developers create high-quality automation scripts with minimal effort.

## 🚀 Live Demo

**Try it now:** [NX CodeBot Pro on Streamlit Cloud](https://nx-codebot-python-generator-explainer-gorq-naqqcmawtuo6y5sagwo.streamlit.app/)

## ✨ Features

### 🎯 Core Capabilities
- **AI-Powered Code Generation**: Leverages Groq API with Llama 3.3 70B model for intelligent code synthesis
- **Example-Based Learning**: Uses similarity matching (TF-IDF + cosine similarity) to find relevant code examples
- **Production-Ready Output**: Generates complete, executable NXOpen scripts following best practices
- **Multi-Strategy Matching**: 
  - Direct filename matching (95% confidence)
  - Keyword-based matching (85% confidence)
  - Semantic similarity analysis (variable confidence)

### 🔍 Code Quality Assurance
- **Automated Validation**: 6-point quality scoring system (0-100)
- **Pattern Recognition**: Extracts and replicates coding patterns from examples
- **Best Practices Enforcement**: Ensures proper builder lifecycle, error handling, and session management

### 📊 Visualization & Analysis
- **Interactive 3D Preview**: Plotly-based real-time visualization of CAD features
- **Similarity Analysis**: Detailed explanations of why examples match user requests
- **AI-Powered Explanations**: Comprehensive code breakdowns and usage instructions

### 📄 Documentation
- **Comprehensive PDF Reports**: 10-page professional reports including:
  - Application overview and workflow
  - Generated code with quality assessment
  - Detailed explanations and similarity analysis
  - Usage instructions and best practices
  - Technical specifications and metadata

### 🎨 User Interface
- **Intuitive Streamlit Interface**: Clean, professional web-based UI
- **Real-Time Feedback**: Progress indicators and quality scores
- **Code Download**: Direct download of generated Python scripts
- **Multi-Tab Organization**: Organized views for code, analysis, previews, and documentation

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **AI Model** | Llama 3.3 70B Versatile (Groq API) |
| **Framework** | Streamlit |
| **Similarity Matching** | Scikit-learn (TF-IDF, Cosine Similarity) |
| **3D Visualization** | Plotly |
| **Image Processing** | Pillow (PIL) |
| **PDF Generation** | FPDF |
| **Language** | Python 3.8+ |
| **CAD API** | Siemens NXOpen Python API |

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Groq API key (free tier available)
- Siemens NX (for running generated scripts)

### Step 1: Clone the Repository
git clone https://github.com/yourusername/nx-codebot-pro.git
cd nx-codebot-pro

### Step 2: Create Virtual Environment
python -m venv venv

Windows
venv\Scripts\activate

Linux/Mac
source venv/bin/activate

### Step 3: Install Dependencies

pip install -r requirements.txt

### Step 4: Configure API Keys

Create a `.env` file in the project root:

GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACE_API_KEY=your_huggingface_token_here # Optional

Or create `.streamlit/secrets.toml`:

GROQ_API_KEY = "your_groq_api_key_here"
HUGGINGFACE_API_KEY = "your_huggingface_token_here" # Optional

### Step 5: Prepare Example Files

Create an `nx_examples` directory and add your NXOpen Python example files:

mkdir nx_examples

Add .py files to nx_examples/

## 🚀 Usage

### Running Locally

streamlit run app.py

The application will open in your default browser at `http://localhost:8501`

### Deploying to Streamlit Cloud

1. Push your repository to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `app.py`
6. Add secrets in "Advanced settings" → "Secrets"
7. Click "Deploy"

## 📖 How to Use

### Method 1: Generate from Examples
1. Select a CAD operation from the dropdown
2. Enter parameters (comma-separated)
3. Click "🚀 Generate from Example"
4. View generated code, explanation, and 3D preview

### Method 2: AI Code Generator
1. Enter your request in natural language
   - Example: "Create a cylinder with radius {param1} and height {param2}"
2. Click "✨ Generate from AI"
3. System finds relevant examples and generates code
4. Review quality score and similarity analysis
5. Download generated script

### Method 3: Download Complete Report
1. After generating code, click "Generate PDF Report"
2. Download comprehensive 10-page documentation
3. Includes code, explanations, usage instructions, and best practices

## 📊 Code Quality Scoring

Generated code is validated against 6 critical components:

| Component | Points | Description |
|-----------|--------|-------------|
| **Imports** | 20 | Proper NXOpen module imports |
| **Main Function** | 20 | Structured main() function |
| **Session Management** | 15 | NXOpen session initialization |
| **Builder Pattern** | 15 | Feature builder usage |
| **Commit Operation** | 15 | Proper builder commit |
| **Cleanup** | 15 | Builder destroy for memory management |

**Quality Levels:**
- 90-100: ✅ Production-Ready
- 70-89: ⚠️ Good (minor adjustments may be needed)
- Below 70: ❌ Needs Review

## 🎯 Similarity Matching Strategies

### Strategy 1: Direct Filename Match (95%)

User Input: "block.py"
Match: block.py → 95% confidence

### Strategy 2: Keyword Match (85%)

User Input: "Create a cylinder feature"
Match: cylinder.py → 85% confidence

### Strategy 3: Semantic Similarity (Variable)

User Input: "Make a box with dimensions..."
TF-IDF Analysis → block.py → 40-95% confidence

## 📁 Project Structure


nx-codebot-pro/
├── app.py # Main Streamlit application
├── requirements.txt # Python dependencies
├── .env # Environment variables (create this)
├── .streamlit/
│ └── secrets.toml # Streamlit secrets (create this)
├── nx_examples/ # NXOpen example scripts
│ ├── block.py
│ ├── cylinder.py
│ ├── sphere.py
│ └── ...
├── README.md # This file
└── .gitignore # Git ignore rules

## 📋 Requirements


streamlit>=1.28.0
groq>=0.4.0
python-dotenv>=1.0.0
plotly>=5.17.0
scikit-learn>=1.3.0
numpy>=1.24.0
Pillow>=10.0.0
fpdf>=1.7.2
chardet>=5.2.0

## 🔑 Getting API Keys

### Groq API (Required)
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create new API key
5. Copy and save in `.env` file

### Hugging Face (Optional - for future features)
1. Visit [Hugging Face](https://huggingface.co/)
2. Create account and login
3. Go to Settings → Access Tokens
4. Create new token with "Inference" permission
5. Copy and save in `.env` file

## 🎓 Example Use Cases

### 1. Rapid Prototyping
- Quickly generate CAD automation scripts for common operations
- Test different parameter combinations
- Validate feature creation logic

### 2. Learning NXOpen API
- Study generated code to understand NXOpen patterns
- Compare different approaches to similar problems
- Build knowledge base of working examples

### 3. Production Automation
- Generate production-ready scripts for repetitive tasks
- Maintain consistent coding standards across team
- Document automation workflows with comprehensive reports

### 4. Code Documentation
- Generate detailed explanations of existing scripts
- Create training materials for new team members
- Maintain documentation alongside code changes

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**

git checkout -b feature/AmazingFeature
3. **Commit your changes**

git commit -m 'Add some AmazingFeature'
4. **Push to the branch**

git push origin feature/AmazingFeature
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to new functions
- Update README for new features
- Test with multiple NX versions
- Ensure backward compatibility

## 🐛 Known Issues & Limitations

- **NX Version Compatibility**: Generated code tested primarily on NX 2007 and NX 2024
- **API Rate Limits**: Groq free tier has rate limiting (consider paid tier for production)
- **Example Dependency**: Code quality depends on quality of example files
- **Image Generation**: Placeholder images used (optional HuggingFace integration available)

## 🗺️ Roadmap

- [ ] Support for more NXOpen feature types
- [ ] Multi-language support (C#, C++, VB.NET)
- [ ] Code refactoring suggestions
- [ ] Integration with NX directly via COM
- [ ] Batch code generation
- [ ] Custom example training interface
- [ ] Version control integration
- [ ] Team collaboration features

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- **Siemens NX**: For the powerful NXOpen API
- **Groq**: For providing fast LLM inference
- **Streamlit**: For the excellent web framework
- **Open Source Community**: For amazing libraries and tools

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/nx-codebot-pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/nx-codebot-pro/discussions)
- **Live App**: [Streamlit Cloud](https://nx-codebot-python-generator-explainer-gorq-naqqcmawtuo6y5sagwo.streamlit.app/)

## 📚 Resources

- [NXOpen API Documentation](https://docs.plm.automation.siemens.com/)
- [Siemens NX Community](https://community.plm.automation.siemens.com/)
- [Groq API Documentation](https://console.groq.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the NX Automation Community**

*Last Updated: November 2025*

This README includes:
✅ Comprehensive project description
✅ Live Streamlit app link with badge
✅ Detailed feature list
✅ Complete installation instructions
✅ Usage examples
✅ Technology stack table
✅ Project structure
✅ API key setup guide
✅ Contributing guidelines
✅ Known issues and roadmap
✅ Professional formatting with emojis
✅ Badges for credibility
✅ Contact and support information
