"""
🌙 Solana Dev's DeepSeek Model Implementation
Built with love by Solana Dev 🚀
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class DeepSeekModel(BaseModel):
    """Implementation for DeepSeek's models"""
    
    AVAILABLE_MODELS = {
        "deepseek-chat": "Fast chat model",
        "deepseek-coder": "Code-specialized model",
        "deepseek-reasoner": "Enhanced reasoning model"
    }
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat", base_url: str = "https://api.deepseek.com", **kwargs):
        self.model_name = model_name
        self.base_url = base_url
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the DeepSeek client"""
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            cprint(f"✨ Initialized DeepSeek model: {self.model_name}", "green")
        except Exception as e:
            cprint(f"❌ Failed to initialize DeepSeek model: {str(e)}", "red")
            self.client = None
    
    def generate_response(self, 
        system_prompt: str,
        user_content: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> ModelResponse:
        """Generate a response using DeepSeek"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            return ModelResponse(
                content=response.choices[0].message.content.strip(),
                raw_response=response,
                model_name=self.model_name,
                usage=response.usage.model_dump() if hasattr(response, 'usage') else None
            )
            
        except Exception as e:
            cprint(f"❌ DeepSeek generation error: {str(e)}", "red")
            raise
    
    def is_available(self) -> bool:
        """Check if DeepSeek is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "deepseek" 