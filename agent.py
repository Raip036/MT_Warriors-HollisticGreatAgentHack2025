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
    
    # Verify credentials
    print("\n🔑 API Key Status:")
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
        print("     Please set HOLISTIC_AI_TEAM_ID, HOLISTIC_AI_API_TOKEN, and HOLISTIC_AI_API_URL in .env")
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
        
        # Convert string to proper message format if needed
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
        
        # Debug: Print payload structure
        print(f"\n🔍 Debug - Payload keys: {list(payload.keys())}")
        print(f"   team_id: {payload['team_id']}")
        print(f"   api_token: {payload['api_token'][:10]}...")
        print(f"   model: {payload['model']}")
        print(f"   messages: {len(payload['messages'])} message(s)")
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Debug: Show what we received
            print(f"   ✅ Response received")
            if 'metadata' in result:
                metadata = result['metadata']
                print(f"   💰 Cost: ${metadata.get('cost_usd', 0):.6f}")
                print(f"   📊 Tokens: {metadata.get('usage', {}).get('total_tokens', 'N/A')}")
                print(f"   💵 Remaining Budget: ${metadata.get('remaining_quota', {}).get('remaining_budget', 'N/A'):.2f}")
            
            # Return in LangChain-compatible format
            class Response:
                def __init__(self, content, metadata=None):
                    self.content = content
                    self.metadata = metadata
            
            # Handle the response format from AWS Bedrock
            if 'content' in result and isinstance(result['content'], list):
                # Extract text from content array
                content = result['content'][0].get('text', '')
                return Response(content, result.get('metadata'))
            elif 'choices' in result:
                # OpenAI-style response
                content = result['choices'][0]['message']['content']
                return Response(content, result.get('metadata'))
            elif 'completion' in result:
                # Alternative format
                content = result['completion']
                return Response(content, result.get('metadata'))
            else:
                # Fallback
                content = str(result)
                return Response(content, result.get('metadata'))
            
        except requests.exceptions.ConnectionError as e:
            print(f"\n❌ Connection Error: Could not reach {self.api_url}")
            print(f"   Error: {str(e)}")
            print("\n💡 Troubleshooting steps:")
            print("   1. Check your internet connection")
            print("   2. Verify the API URL is correct")
            print("   3. Contact hackathon organizers if issue persists")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error: {e}")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            if response.status_code == 401:
                print("\n   💡 Authentication failed - check your API token and team ID")
            elif response.status_code == 429:
                print("\n   💡 Rate limit exceeded - you may have hit your $50 budget")
            raise
        except Exception as e:
            print(f"\n❌ Unexpected Error: {e}")
            raise
    
    def bind_tools(self, tools):
        """Bind tools to the model (for ReAct agent)"""
        return self

def get_chat_model(model_name: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"):
    """Get a chat model instance"""
    return HolisticAIBedrockChat(model_name)

# ============================================
# Test Connection Function
# ============================================
def test_connection():
    """Test the API connection with detailed diagnostics"""
    print("\n" + "="*70)
    print("🔍 TESTING API CONNECTION")
    print("="*70)
    
    try:
        llm = get_chat_model()
        print("\n✅ Model initialized successfully")
        
        print("\n📤 Sending test message...")
        response = llm.invoke("Say 'Hello, I am working!' in one sentence.")
        
        print(f"\n✅ SUCCESS! Received response:")
        print(f"   {response.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed")
        return False

# ============================================
# Pharmacy Agent
# ============================================
class PharmacyAgent:
    """Basic pharmacy consultation agent"""
    
    def __init__(self):
        """Initialize the pharmacy agent"""
        self.llm = get_chat_model()
        self.total_cost = 0.0
        self.query_count = 0
        print("\n🏥 Pharmacy Agent initialized")
        print(f"   Model: Claude 3.5 Sonnet")
        print(f"   Tools: None (basic agent)")
        print(f"   Budget: $50 limit")
    
    def ask(self, question: str) -> str:
        """Ask the agent a question"""
        self.query_count += 1
        print(f"\n{'='*70}")
        print(f"❓ Question #{self.query_count}: {question}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        # Create pharmacy-focused prompt
        system_context = """You are a knowledgeable pharmacy assistant. 
You provide helpful information about medications, drug interactions, 
dosages, and general pharmaceutical guidance. 

Always remind users to consult with their healthcare provider for 
medical advice and never diagnose conditions."""
        
        full_prompt = f"{system_context}\n\nUser question: {question}"
        
        try:
            response = self.llm.invoke(full_prompt)
            elapsed = time.time() - start_time
            
            # Track cost
            if hasattr(response, 'metadata') and response.metadata:
                cost = response.metadata.get('cost_usd', 0)
                self.total_cost += cost
            
            print(f"\n💬 Response:")
            print(f"   {response.content}")
            print(f"\n⏱️  Time: {elapsed:.2f}s")
            print(f"💰 Session Cost: ${self.total_cost:.6f}")
            
            return response.content
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            raise

# ============================================
# Main Function
# ============================================
def main():
    """Run the pharmacy agent demo"""
    
    print("="*70)
    print("🏥 PHARMACY AGENT - Basic Setup")
    print("="*70)
    print("Budget: $50 | Model: Claude 3.5 Sonnet")
    print("="*70)
    
    # Load environment
    if not load_environment():
        print("\n❌ Setup failed - please check your .env file")
        return
    
    print("\n✅ Environment loaded successfully!")
    
    # Test connection first
    print("\n" + "="*70)
    print("Step 1: Testing API Connection")
    print("="*70)
    
    if not test_connection():
        print("\n" + "="*70)
        print("⚠️  CONNECTION TEST FAILED")
        print("="*70)
        print("\n💡 Please check:")
        print("   1. Is your internet connection working?")
        print("   2. Are your credentials correct in .env?")
        print("   3. Have you exceeded the $50 budget?")
        print("\n📝 Required .env variables:")
        print("   HOLISTIC_AI_TEAM_ID=team_the_great_hack_2025_008")
        print("   HOLISTIC_AI_API_TOKEN=VViwYCXJSkQXTE4kjoMVTzMnXfUELpKP4ghiHEOw3X0")
        print("   HOLISTIC_AI_API_URL=https://ctwa92wg1b.execute-api.us-east-1.amazonaws.com/prod/invoke")
        return
    
    # Create agent
    print("\n" + "="*70)
    print("Step 2: Creating Pharmacy Agent")
    print("="*70)
    
    try:
        agent = PharmacyAgent()
    except Exception as e:
        print(f"\n❌ Failed to create agent: {e}")
        return
    
    # Example questions
    print("\n" + "="*70)
    print("Step 3: Running Example Queries")
    print("="*70)
    
    questions = [
        "What is ibuprofen used for?",
        "Can you explain the difference between generic and brand-name drugs?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n\n📌 EXAMPLE {i}:")
        try:
            agent.ask(question)
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            print("   Stopping demo to preserve budget...")
            break
        
        if i < len(questions):
            print("\n⏸️  Pausing before next query...")
            time.sleep(1)
    
    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70)
    print("\n💡 Next steps:")
    print("   • Add tools (drug database search, interaction checker)")
    print("   • Integrate ReAct agent for multi-step reasoning")
    print("   • Add conversation memory")
    print("   • Monitor your $50 budget usage")

if __name__ == "__main__":
    main()