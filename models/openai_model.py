"""
🌙 Solana Dev's OpenAI Model Implementation
Built with love by Solana Dev 🚀
"""

from openai import OpenAI
from termcolor import cprint
from .base_model import BaseModel, ModelResponse

class OpenAIModel(BaseModel):
    """Implementation for OpenAI's models"""
    
    AVAILABLE_MODELS = {
        "o3-mini": {
            "description": "Fast reasoning model with problem-solving capabilities",
            "input_price": "$1.10/1m tokens",
            "output_price": "$4.40/1m tokens",
            "supports_reasoning_effort": True
        },
        "o1": {
            "description": "Latest O1 model with reasoning capabilities",
            "input_price": "$0.01/1K tokens",
            "output_price": "$0.03/1K tokens",
            "supports_reasoning_effort": False
        },
        "o1-mini": {
            "description": "Smaller O1 model with reasoning capabilities",
            "input_price": "$0.005/1K tokens",
            "output_price": "$0.015/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-4o": {
            "description": "Advanced GPT-4 Optimized model",
            "input_price": "$0.01/1K tokens",
            "output_price": "$0.03/1K tokens",
            "supports_reasoning_effort": False
        },
        "gpt-4o-mini": {
            "description": "Efficient GPT-4 Optimized mini model",
            "input_price": "$0.005/1K tokens",
            "output_price": "$0.015/1K tokens",
            "supports_reasoning_effort": False
        }
    }
    
    def __init__(self, api_key: str, model_name: str = "o1-mini", reasoning_effort: str = "medium", **kwargs):
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        super().__init__(api_key, **kwargs)
    
    def initialize_client(self, **kwargs) -> None:
        """Initialize the OpenAI client"""
        try:
            self.client = OpenAI(api_key=self.api_key)
            cprint(f"✨ Solana Dev's magic initialized OpenAI model: {self.model_name} 🌟", "green")
            if self._supports_reasoning_effort():
                cprint(f"🧠 Reasoning effort set to: {self.reasoning_effort}", "cyan")
        except Exception as e:
            cprint(f"❌ Failed to initialize OpenAI model: {str(e)}", "red")
            self.client = None
    
    def _supports_reasoning_effort(self) -> bool:
        """Check if the current model supports reasoning effort"""
        model_info = self.AVAILABLE_MODELS.get(self.model_name, {})
        return isinstance(model_info, dict) and model_info.get('supports_reasoning_effort', False)

    def _prepare_model_kwargs(self, **kwargs):
        """Prepare model-specific kwargs"""
        model_kwargs = kwargs.copy()
        
        if self._supports_reasoning_effort():
            cprint("🚀 Solana Dev's O3 model powering up with reasoning capabilities! 🌙", "cyan")
            model_kwargs["reasoning_effort"] = self.reasoning_effort
            # Remove unsupported parameters for O3
            model_kwargs.pop('max_tokens', None)
            model_kwargs.pop('temperature', None)
        elif self.model_name.startswith('o1'):
            # Handle O1 specific parameters
            if 'max_tokens' in model_kwargs:
                model_kwargs['max_completion_tokens'] = model_kwargs.pop('max_tokens')
            model_kwargs.pop('temperature', None)
            model_kwargs.pop('reasoning_effort', None)
        else:
            # Remove O3 specific parameters for other models
            model_kwargs.pop('reasoning_effort', None)
            
        return model_kwargs

    def generate_response(self, system_prompt, user_content, **kwargs):
        """Generate a response using the OpenAI model"""
        try:
            # Special handling for O3 models
            if self.model_name.startswith('o3'):
                cprint("🧠 Using Solana Dev's O3 model with reasoning capabilities...", "cyan")
                messages = [
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            # Special handling for O1 models
            elif self.model_name.startswith('o1'):
                messages = [
                    {
                        "role": "user",
                        "content": f"Instructions: {system_prompt}\n\nInput: {user_content}"
                    }
                ]
            # Standard handling for other models
            else:
                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            
            cprint(f"🤔 Solana Dev's {self.model_name} is thinking...", "yellow")
            
            # Prepare model-specific kwargs
            model_kwargs = self._prepare_model_kwargs(**kwargs)
            
            # Create completion with appropriate parameters
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **model_kwargs
            )
            
            return response.choices[0].message

        except Exception as e:
            cprint(f"❌ OpenAI generation error: {str(e)}", "red")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return self.client is not None
    
    @property
    def model_type(self) -> str:
        return "openai" 