"""
OpenAI LLM Client
Handles all AI/LLM operations using OpenAI API
"""

import os
import time
from typing import Tuple, Optional


class LLMClient:
    """Client for OpenAI API interactions."""
    
    def __init__(self, enabled: bool = True, model: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            enabled: Whether AI is enabled
            model: Model to use (default: gpt-4o-2024-08-06)
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
        self.enabled = enabled and bool(self.api_key)
        self.import_ok = True
        self.supports_structured_outputs = False
        
        if self.enabled:
            try:
                from openai import OpenAI  # noqa
                if "gpt-4o" in self.model or "gpt-4o-mini" in self.model:
                    self.supports_structured_outputs = True
            except Exception:
                self.import_ok = False
                self.enabled = False
    
    def status_label(self) -> str:
        """Get a status label for the LLM."""
        if not self.api_key:
            return "AI: OFF (no key)"
        if not self.import_ok:
            return "AI: OFF (install openai)"
        suffix = " [Structured]" if self.supports_structured_outputs else ""
        return f"AI: ON ({self.model}{suffix})" if self.enabled else "AI: OFF"
    
    def complete_json(
        self, 
        sys_prompt: str, 
        user_prompt: str, 
        max_tokens: int = 2000, 
        retries: int = 2, 
        pydantic_model=None
    ) -> Tuple[str, Optional[str]]:
        """
        Send a request to the LLM and get JSON response.
        
        Args:
            sys_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens in response
            retries: Number of retries on failure
            pydantic_model: Optional Pydantic model for structured outputs
            
        Returns:
            Tuple of (response_text, error_message)
        """
        if not self.enabled:
            return ("", "AI disabled or missing key/openai")
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
        except Exception as e:
            return ("", f"OpenAI import failed: {e}")
        
        last_err = None
        for attempt in range(retries + 1):
            try:
                kwargs = dict(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                # Use Structured Outputs if pydantic model provided and supported
                try:
                    from pydantic import BaseModel
                    PYDANTIC_AVAILABLE = True
                except ImportError:
                    PYDANTIC_AVAILABLE = False
                
                if pydantic_model and self.supports_structured_outputs and PYDANTIC_AVAILABLE:
                    print(f"DEBUG: Using Structured Outputs with {pydantic_model.__name__}")
                    kwargs["response_format"] = pydantic_model
                    
                    if self.model.startswith(("o1",)):
                        kwargs["max_completion_tokens"] = max_tokens
                    else:
                        kwargs["max_tokens"] = max_tokens
                        kwargs["temperature"] = 0.0
                        kwargs["seed"] = 12345
                    
                    resp = client.beta.chat.completions.parse(**kwargs)
                    
                    if resp.choices[0].message.refusal:
                        return ("", f"Model refused: {resp.choices[0].message.refusal}")
                    
                    parsed = resp.choices[0].message.parsed
                    if parsed:
                        return (parsed.model_dump_json(indent=2), None)
                    else:
                        return ("", "No parsed response from structured output")
                
                else:
                    # Fallback to regular JSON mode
                    print("DEBUG: Using regular JSON mode")
                    kwargs["response_format"] = {"type": "json_object"}
                    
                    if self.model.startswith(("o1",)):
                        kwargs["max_completion_tokens"] = max_tokens
                    else:
                        kwargs["max_tokens"] = max_tokens
                        kwargs["temperature"] = 0.0
                        kwargs["seed"] = 12345
                        kwargs["top_p"] = 1.0
                    
                    resp = client.chat.completions.create(**kwargs)
                    return ((resp.choices[0].message.content or "").strip(), None)
                    
            except Exception as e:
                msg = str(e)
                last_err = msg
                print(f"DEBUG: API call failed (attempt {attempt+1}): {msg}")
                
                if "unsupported" in msg.lower() or "parse" in msg.lower():
                    try:
                        kwargs["response_format"] = {"type": "json_object"}
                        if "max_completion_tokens" in kwargs:
                            kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")
                        resp = client.chat.completions.create(**kwargs)
                        return ((resp.choices[0].message.content or "").strip(), None)
                    except Exception as e2:
                        last_err = str(e2)
                
                time.sleep(0.8 * (attempt + 1))
        
        return ("", last_err or "Unknown OpenAI error")
    
    def analyze_images(self, images: list, context: str) -> str:
        """
        Analyze images using GPT-4 Vision.
        
        Args:
            images: List of image data URLs
            context: Context about the images
            
        Returns:
            Analysis text
        """
        if not self.enabled:
            return ""
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            # Build message content with images
            content = [
                {
                    "type": "text",
                    "text": f"Analyze these images in the context of: {context}\n\nProvide detailed insights about what's shown in the images."
                }
            ]
            
            for img in images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": img["data_url"]
                    }
                })
            
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=2000
            )
            
            return resp.choices[0].message.content or ""
            
        except Exception as e:
            print(f"DEBUG: Image analysis failed: {e}")
            return f"Error analyzing images: {e}"