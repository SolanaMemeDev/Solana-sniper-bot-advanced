from fastapi import FastAPI, HTTPException
import requests
import json
import time
from typing import Optional

app = FastAPI(title="MoonDev's DeepSeek API 🌙")

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Model mapping
MODEL_MAPPING = {
    "deepseek-chat": "deepseek-v3",  # Map deepseek-chat to v3
    "deepseek-reasoner": "deepseek-r1:70b"  # Map deepseek-reasoner to r1
}

async def retry_request(func, *args, **kwargs) -> Optional[dict]:
    """Helper function to retry failed requests with exponential backoff"""
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                print(f"🔄 Retry attempt {attempt + 1}/{MAX_RETRIES}...")
                print(f"😴 Waiting {RETRY_DELAY} seconds before retry...")
                time.sleep(RETRY_DELAY)
            
            return await func(*args, **kwargs)
            
        except Exception as e:
            last_error = e
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                print(f"🌙 Solana Dev says: Don't worry, we'll try again! 🚀")
            
    print(f"❌ All {MAX_RETRIES} attempts failed. Last error: {str(last_error)}")
    raise last_error

@app.get("/health")
async def health_check():
    try:
        # Test Ollama connection with retry
        async def check_health():
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                return {"status": "healthy", "message": "✨ Ollama is healthy and responding!"}
            return {"status": "unhealthy", "message": "❌ Ollama is not responding correctly"}
            
        return await retry_request(check_health)
    except Exception as e:
        return {"status": "error", "message": f"❌ Error connecting to Ollama: {str(e)}"}

@app.post("/v1/chat/completions")
async def create_chat_completion(request: dict):
    print(f"🤖 Received chat request for model: {request.get('model', 'unknown')}")
    print(f"💬 Messages: {request.get('messages', [])}")
    
    try:
        # Map the model name
        requested_model = request.get('model', 'deepseek-chat')
        ollama_model = MODEL_MAPPING.get(requested_model)
        
        if not ollama_model:
            raise HTTPException(status_code=400, detail=f"❌ Unsupported model: {requested_model}. Use 'deepseek-chat' or 'deepseek-reasoner'")
        
        print(f"🎯 Using Ollama model: {ollama_model}")
        
        async def make_request():
            # Test Ollama connection first
            print("🔍 Testing Ollama connection...")
            test_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            print(f"📡 Ollama Test Response: {test_response.status_code}")
            
            # Just use the last user message
            messages = request.get('messages', [])
            prompt = messages[-1]['content']  # Get just the user's question
            
            print(f"🎯 Sending to Ollama URL: {OLLAMA_BASE_URL}")
            print(f"📝 Prompt: {prompt}")
            
            payload = {
                "model": ollama_model,
                "prompt": prompt,
                "stream": False
            }
            
            print("🌟 Sending request to Ollama...")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=120  # Increased timeout
            )
            
            print(f"📡 Ollama Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✨ Success! Response: {json.dumps(result, indent=2)}")
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": result.get("response", "")
                        }
                    }]
                }
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to generate response")
        
        return await retry_request(make_request)
            
    except requests.Timeout:
        print("⏰ Request timed out waiting for Ollama")
        raise HTTPException(status_code=504, detail="Request timed out after all retries")
    except requests.ConnectionError:
        print("🔌 Connection error reaching Ollama")
        raise HTTPException(status_code=502, detail="Cannot connect to Ollama after all retries")
    except Exception as e:
        print(f"❌ Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MoonDev's DeepSeek API...")
    print("🌟 Supported models:")
    for api_model, ollama_model in MODEL_MAPPING.items():
        print(f"  - {api_model} -> {ollama_model}")
    print(f"⚡ Retry settings: {MAX_RETRIES} attempts with {RETRY_DELAY}s delay")
    uvicorn.run(app, host="0.0.0.0", port=8000)