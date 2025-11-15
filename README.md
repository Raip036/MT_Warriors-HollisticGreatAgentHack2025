# 🏥 PharmaMiku AI Agent

> An intelligent pharmacy consultation assistant powered by Claude 3.5 Sonnet via AWS Bedrock

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Claude](https://img.shields.io/badge/Claude-3.5%20Sonnet-purple.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Overview

PharmaMiku AI Agent is a smart assistant that provides reliable information about medications, drug interactions, dosages, and pharmaceutical guidance. Built for the **Great Agent Hack 2025**, this agent leverages the power of Claude 3.5 Sonnet to answer pharmacy- and drug-related questions with accuracy, transparency and care.

### ✨ Key Features

- 🤖 **AI-Powered Responses** - Uses Claude 3.5 Sonnet for intelligent pharmaceutical guidance
- 💰 **Budget Tracking** - Real-time cost monitoring with $50 spending limit
- 🔒 **Secure API Integration** - Custom Holistic AI Bedrock proxy for AWS Bedrock access
- 📊 **Usage Analytics** - Track tokens, costs, and remaining budget per query
- ⚡ **Fast & Reliable** - Sub-second response times for most queries

### ⚠️ Important Disclaimer

This agent provides **general pharmaceutical information only**. Always consult with a qualified healthcare provider for medical advice, diagnoses, or treatment decisions.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- API credentials from The Great Hack 2025

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd pharmacy-agent
   ```

2. **Create a virtual environment**
   ```bash
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.template .env
   ```
   
   Update `.env` with your credentials:
   ```env
   HOLISTIC_AI_TEAM_ID=your_team_id_here
   HOLISTIC_AI_API_TOKEN=your_api_token_here
   HOLISTIC_AI_API_URL=https://ctwa92wg1b.execute-api.us-east-1.amazonaws.com/prod/invoke
   ```

5. **Test the connection**
   ```bash
   python test_api.py
   ```

6. **Run the agent**
   ```bash
   python pharmacy_agent.py
   ```

---

## 📁 Project Structure

```
pharmacy-agent/
├── 📄 pharmacy_agent.py      # Main agent implementation
├── 🧪 test_api.py             # API connection test script
├── 📋 requirements.txt        # Python dependencies
├── 🔐 .env                    # Environment variables (not in git)
├── 📝 .env.template           # Template for .env file
├── 🚫 .gitignore              # Git ignore rules
└── 📖 README.md               # This file
```

---

## 💻 Usage

### Basic Query

```python
from pharmacy_agent import PharmacyAgent

# Initialize the agent
agent = PharmacyAgent()

# Ask a question
response = agent.ask("What is ibuprofen used for?")
print(response)
```

### Interactive Mode

Run the main script for a demo with example queries:

```bash
python pharmacy_agent.py
```

### Example Questions

- "What is ibuprofen used for?"
- "Can you explain the difference between generic and brand-name drugs?"
- "What should I know about antibiotic resistance?"
- "How does acetaminophen work?"

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `HOLISTIC_AI_TEAM_ID` | Your team identifier | ✅ Yes |
| `HOLISTIC_AI_API_TOKEN` | API authentication token | ✅ Yes |
| `HOLISTIC_AI_API_URL` | AWS API Gateway endpoint | ✅ Yes |

### Budget Management

The agent tracks spending in real-time:
- **Budget Limit**: $50.00
- **Cost per Query**: ~$0.0002 - $0.001
- **Estimated Queries**: 50,000 - 250,000 queries

Monitor your budget with each query response:
```
💰 Cost: $0.000207
💵 Remaining Budget: $49.22
```

---

## 🎯 Features Roadmap

### ✅ Current Features
- [x] Basic Q&A with Claude 3.5 Sonnet
- [x] Budget tracking and monitoring
- [x] Error handling and retries
- [x] Cost per query analytics

### 🔄 In Progress
- [ ] ReAct agent with multi-step reasoning
- [ ] Drug interaction checker tool
- [ ] Medication database integration

### 📅 Planned Features
- [ ] Conversation memory
- [ ] Web interface (Streamlit/Gradio)
- [ ] Export conversation history
- [ ] Multi-language support

---

## 🛠️ Development

### Running Tests

```bash
# Test API connection
python test_api.py

# Run with debug output
python pharmacy_agent.py
```

### Adding New Features

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📊 Technical Details

### Technology Stack

- **Language**: Python 3.8+
- **AI Model**: Claude 3.5 Sonnet (via AWS Bedrock)
- **API**: Custom Holistic AI Bedrock Proxy
- **Dependencies**: 
  - `requests` - HTTP client
  - `python-dotenv` - Environment management
  - `langgraph` - Agent framework (planned)
  - `langchain-core` - LLM abstractions (planned)

### API Response Format

```json
{
  "content": [
    {
      "type": "text",
      "text": "Response from Claude..."
    }
  ],
  "usage": {
    "input_tokens": 150,
    "output_tokens": 200,
    "total_tokens": 350
  },
  "metadata": {
    "cost_usd": 0.000207,
    "remaining_budget": 49.218002
  }
}
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Keep commit messages clear and descriptive

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**The Great Hack 2025 - Team 008**

- Developed with ❤️ for healthcare innovation
- Powered by Claude 3.5 Sonnet
- Built with Holistic AI Bedrock Proxy

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [Wiki](https://github.com/your-repo/wiki)
- **Hackathon**: The Great Hack 2025

---

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude AI
- [AWS Bedrock](https://aws.amazon.com/bedrock/) for model hosting
- The Great Hack 2025 organizers
- Holistic AI team for API infrastructure

---

<div align="center">

**[⬆ Back to Top](#-pharmacy-ai-agent)**

Made with 💊 by Team 008

</div>
