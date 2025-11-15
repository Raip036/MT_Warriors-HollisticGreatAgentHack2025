"""
Pharmacy Agent - Basic Setup with Holistic AI Bedrock
A simple ReAct agent for pharmacy-related queries
Budget: $50 limit
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
import requests

# ============================================
# Load Environment Variables
# ============================================
def load_environment():
    """Load API credentials from .env file"""
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print("📄 Loaded configuration from .env file")
    else:
        print("⚠️  No .env file found - using environment variables")
    
    team_id = os.getenv('HOLISTIC_AI_TEAM_ID')
    api_token = os.getenv('HOLISTIC_AI_API_TOKEN')
    api_url = os.getenv('HOLISTIC_AI_API_URL')
    
    if team_id and api_token and api_url:
        print(f"  ✅ Holistic AI Bedrock credentials loaded")
        print(f"     Team ID: {team_id}")
        print(f"     API URL: {api_url}")
        print(f"     Budget Limit: $50")
    else:
        print("  ❌ Holistic AI Bedrock credentials not found!")
        return False
    
    return True

# ============================================
# Holistic AI Bedrock Chat Model
# ============================================
class HolisticAIBedrockChat:
    """Chat model that uses Holistic AI Bedrock Proxy"""
    
    def __init__(self, model_name: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.model_name = model_name
        self.team_id = os.getenv('HOLISTIC_AI_TEAM_ID')
        self.api_token = os.getenv('HOLISTIC_AI_API_TOKEN')
        self.api_url = os.getenv('HOLISTIC_AI_API_URL')
        
        if not self.team_id or not self.api_token or not self.api_url:
            raise ValueError("Missing Holistic AI credentials in environment")
        
        print(f"\n🔧 Initializing with:")
        print(f"   API URL: {self.api_url}")
        print(f"   Model: {self.model_name}")
        print(f"   Team: {self.team_id}")
    
    def invoke(self, messages):
        """Send a message and get response"""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        elif hasattr(messages, 'content'):
            messages = [{"role": "user", "content": messages.content}]
        
        headers = {
            "Content-Type": "application/json",
            "X-Api-Token": self.api_token
        }
        
        payload = {
            "team_id": self.team_id,
            "api_token": self.api_token,
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 2048
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            class Response:
                def __init__(self, content, metadata=None):
                    self.content = content
                    self.metadata = metadata
            
            if 'content' in result and isinstance(result['content'], list):
                content = result['content'][0].get('text', '')
                return Response(content, result.get('metadata'))
            elif 'choices' in result:
                content = result['choices'][0]['message']['content']
                return Response(content, result.get('metadata'))
            elif 'completion' in result:
                content = result['completion']
                return Response(content, result.get('metadata'))
            else:
                content = str(result)
                return Response(content, result.get('metadata'))
            
        except Exception as e:
            print(f"\n❌ Error invoking model: {e}")
            raise

def get_chat_model(model_name: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
    return HolisticAIBedrockChat(model_name)

# ============================================
# Test Connection Function
# ============================================
def test_connection():
    print("\n🔍 TESTING API CONNECTION")
    try:
        llm = get_chat_model()
        print("✅ Model initialized successfully")
        response = llm.invoke("Say 'Hello, I am working!' in one sentence.")
        print(f"✅ SUCCESS! Received response: {response.content}")
        return True
    except Exception:
        print("❌ Connection test failed")
        return False

# ============================================
# Pharmacy Agent
# ============================================
class PharmacyAgent:
    """Basic pharmacy consultation agent"""
    
    def __init__(self):
        self.llm = get_chat_model()
        self.total_cost = 0.0
        self.query_count = 0
        print("\n🏥 Pharmacy Agent initialized")
        print(f"   Model: Claude 3.5 Sonnet")
        print(f"   Budget: $50 limit")
    
    def ask(self, question: str) -> str:
        self.query_count += 1
        print(f"\n{'='*70}")
        print(f"❓ Question #{self.query_count}: {question}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        system_context = """You are a knowledgeable pharmacy assistant. 
You provide helpful information about medications, drug interactions, 
dosages, and general pharmaceutical guidance. 

Always remind users to consult with their healthcare provider for 
medical advice and never diagnose conditions."""
        
        full_prompt = f"{system_context}\n\nUser question: {question}"
        
        response = self.llm.invoke(full_prompt)
        elapsed = time.time() - start_time
        
        if hasattr(response, 'metadata') and response.metadata:
            cost = response.metadata.get('cost_usd', 0)
            self.total_cost += cost
        
        print(f"\n💬 Response: {response.content}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"💰 Session Cost: ${self.total_cost:.6f}")
        
        return response.content

# ============================================
# Interactive User Input
# ============================================
def run_interactive_session(agent: PharmacyAgent):
    print("\n💬 Interactive Pharmacy Agent Session")
    print("Type 'exit' to quit")
    
    while True:
        user_input = input("\n❓ Your question: ").strip()
        if user_input.lower() in ('exit', 'quit'):
            print("👋 Exiting session. Stay safe!")
            break
        if not user_input:
            print("⚠️  Please enter a valid question.")
            continue
        try:
            agent.ask(user_input)
        except Exception as e:
            print(f"❌ Error: {e}")

# ============================================
# Main Function
# ============================================
def main():
    if not load_environment():
        return
    if not test_connection():
        return
    agent = PharmacyAgent()
    run_interactive_session(agent)

if __name__ == "__main__":
    main()
