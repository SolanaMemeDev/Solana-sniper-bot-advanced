"""
🌙 Solana Dev's Gemini Model Implementation
Built with love by Solana Dev 🚀
"""

import google.generativeai as genai
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class GeminiModel(BaseModel):
    """Implementation for Google's Gemini models"""
    
    AVAILABLE_MODELS = {
        "gemini-pro": "Most capable Gemini model",
        "gemini-pro-vision": "Gemini model with vision capabilities"
    }
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro", **kwargs):
        self.model_name = model_name
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model_name)
            cprint(f"✨ Initialized Gemini model: {self.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize Gemini model: {str(e)}", "red")
            self.client = None
    
    def generate_response(self, 
        system_prompt: str,
        user_content: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> ModelResponse:
        """Generate a response using Gemini"""
        try:
            # Combine system prompt and user content since Gemini doesn't have system messages
            combined_prompt = f"{system_prompt}\n\n{user_content}"
            
            response = self.client.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )
            
            return ModelResponse(
                content=response.text.strip(),
                raw_response=response,
                model_name=self.model_name,
                usage=None  # Gemini doesn't provide token usage info
            )
            
        except Exception as e:
            cprint(f"❌ Gemini generation error: {str(e)}", "red")
            raise
    
    def is_available(self) -> bool:
        """Check if Gemini is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "gemini" 