# agent.py
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

def load_environment():
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
    team_id = os.getenv('HOLISTIC_AI_TEAM_ID')
    api_token = os.getenv('HOLISTIC_AI_API_TOKEN')
    api_url = os.getenv('HOLISTIC_AI_API_URL')
    return bool(team_id and api_token and api_url)

class HolisticAIBedrockChat:
    def __init__(self, model_name="anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.model_name = model_name
        self.team_id = os.getenv('HOLISTIC_AI_TEAM_ID')
        self.api_token = os.getenv('HOLISTIC_AI_API_TOKEN')
        self.api_url = os.getenv('HOLISTIC_AI_API_URL')
    
    def invoke(self, messages):
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        headers = {"Content-Type": "application/json", "X-Api-Token": self.api_token}
        payload = {
            "team_id": self.team_id,
            "api_token": self.api_token,
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2048
        }
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = ""
        if 'content' in result and isinstance(result['content'], list):
            content = result['content'][0].get('text', '')
        elif 'choices' in result:
            content = result['choices'][0]['message']['content']
        elif 'completion' in result:
            content = result['completion']
        else:
            content = str(result)
        return content

def get_chat_model():
    return HolisticAIBedrockChat()

class PharmacyAgent:
    def __init__(self):
        self.llm = get_chat_model()
        self.total_cost = 0.0
        self.query_count = 0
    
    def ask(self, question: str) -> str:
        self.query_count += 1
        system_context = """You are a knowledgeable pharmacy assistant. 
You provide helpful information about medications, drug interactions, 
dosages, and general pharmaceutical guidance. 

Always remind users to consult with their healthcare provider for 
medical advice and never diagnose conditions."""
        full_prompt = f"{system_context}\n\nUser question: {question}"
        response = self.llm.invoke(full_prompt)
        return response
