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


 1. **Backend (FastAPI)**

    ```bash
    cd backend
    ```

    Create virtual enviroment
    ```bash
    python3 -m venv venv
    ```

    Create .env file with:
    ### Environment Variables

| Variable                | Description                                         | Required               |
| ----------------------- | --------------------------------------------------- | ---------------------- |
| `HOLISTIC_AI_TEAM_ID`   | Your team identifier                                | ✅ Yes                  |
| `HOLISTIC_AI_API_TOKEN` | API authentication token                            | ✅ Yes                  |
| `HOLISTIC_AI_API_URL`   | AWS API Gateway endpoint for your Holistic AI agent | ✅ Yes                  |
| `VALYU_API_KEY`         | API key for Valyu model access                      | ⚠️ Only if using Valyu |


Start FastAPI from backend folder:
```bash
# From backend folder
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

2. **Front end**

```bash
cd frontend
 Npx create-next-app@latest
```



    



















These steps set up the Python virtual environment and install the required packages.

Navigate to the backend folder:

```bash
cd backend
```
Create a virtual environment:

```bash
python -m venv venv
```
Activate the virtual environment:

On macOS/Linux:

```bash
source venv/bin/activate
```
On Windows (PowerShell):

```bash
.\venv\Scripts\Activate
```
Install dependencies:

```bash
pip install -r requirements.txt
```
6. **Frontend**

These steps install the Node.js packages.

In a new terminal, navigate to the frontend folder:

```bash
cd frontend
```
Install dependencies:

```Bash
npm install
```
🏃 Running the Project
1. Start the Backend Server

Make sure you are in the backend folder and your virtual environment is active.

Run the Uvicorn server:

```Bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```
Your backend API will be running at http://localhost:8000

6. **Start the Frontend App

Make sure you are in the frontend folder.

Run the development server:

```Bash
npm run dev
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

### Example Questions

- "What is ibuprofen used for?"
- "Can you explain the difference between generic and brand-name drugs?"
- "What should I know about antibiotic resistance?"
- "How does acetaminophen work?"

---

## 🔧 Configuration



### Budget Management

The agent tracks spending in real-time:
- **Budget Limit**: $50.00
- **Cost per Query**: ~$0.0002 - $0.001
- **Estimated Queries**: 50,000 - 250,000 queries

Monitor your budget with each query response:
```
💰 Cost: $0.000207
💵 Remaining Budget: $49.22

