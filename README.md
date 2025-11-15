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
   python APItest.py
   ```

6. **Run the agent**
   ```bash
   python agent.py
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

| Variable                | Description                                         | Required               |
| ----------------------- | --------------------------------------------------- | ---------------------- |
| `HOLISTIC_AI_TEAM_ID`   | Your team identifier                                | ✅ Yes                  |
| `HOLISTIC_AI_API_TOKEN` | API authentication token                            | ✅ Yes                  |
| `HOLISTIC_AI_API_URL`   | AWS API Gateway endpoint for your Holistic AI agent | ✅ Yes                  |
| `VALYU_API_KEY`         | API key for Valyu model access                      | ⚠️ Only if using Valyu |

### Budget Management

The agent tracks spending in real-time:
- **Budget Limit**: $50.00
- **Cost per Query**: ~$0.0002 - $0.001
- **Estimated Queries**: 50,000 - 250,000 queries

Monitor your budget with each query response:
```
💰 Cost: $0.000207
💵 Remaining Budget: $49.22

