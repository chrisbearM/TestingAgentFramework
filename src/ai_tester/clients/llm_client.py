"""
OpenAI LLM Client
Handles all AI/LLM operations using OpenAI API
"""

import os
import time
from typing import Tuple, Optional

from ai_tester.clients.cache_client import CacheClient


class LLMClient:
    """Client for OpenAI API interactions."""

    def __init__(
        self,
        enabled: bool = True,
        model: Optional[str] = None,
        cache_enabled: bool = True,
        redis_url: Optional[str] = None
    ):
        """
        Initialize LLM client.

        Args:
            enabled: Whether AI is enabled
            model: Model to use (default: gpt-4o-2024-08-06)
            cache_enabled: Whether to enable response caching
            redis_url: Redis connection URL (falls back to disk cache if not provided)
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
        self.enabled = enabled and bool(self.api_key)
        self.import_ok = True
        self.supports_structured_outputs = False

        # Initialize cache client
        redis_url = redis_url or os.getenv("REDIS_URL")
        self.cache_client = CacheClient(
            redis_url=redis_url,
            cache_dir=".cache/llm",
            ttl_days=90,  # Increased from 30 to 90 days for better cache retention
            enabled=cache_enabled
        )

        if self.enabled:
            try:
                from openai import OpenAI  # noqa
                if "gpt-4o" in self.model or "gpt-4o-mini" in self.model:
                    self.supports_structured_outputs = True
                print(f"DEBUG LLMClient __init__: model={self.model}, supports_structured_outputs={self.supports_structured_outputs}")
            except Exception as e:
                print(f"DEBUG LLMClient __init__: Exception during initialization: {e}")
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
        pydantic_model=None,
        use_cache: bool = True,
        model: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Send a request to the LLM and get JSON response.

        Args:
            sys_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens in response
            retries: Number of retries on failure
            pydantic_model: Optional Pydantic model for structured outputs
            use_cache: Whether to use caching (default: True)
            model: Optional model override (defaults to self.model)

        Returns:
            Tuple of (response_text, error_message)
        """
        if not self.enabled:
            return ("", "AI disabled or missing key/openai")

        # Use provided model or fall back to default
        model_to_use = model or self.model

        # Check cache first
        if use_cache and self.cache_client.enabled:
            cache_key = self.cache_client._generate_cache_key(
                sys_prompt, user_prompt, max_tokens, model_to_use
            )
            cached_response = self.cache_client.get(cache_key)
            if cached_response is not None:
                print(f"DEBUG: Cache HIT for model {model_to_use} - Saved API call!")
                return cached_response
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
        except Exception as e:
            return ("", f"OpenAI import failed: {e}")
        
        last_err = None
        for attempt in range(retries + 1):
            try:
                kwargs = dict(
                    model=model_to_use,
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
                        response_text = parsed.model_dump_json(indent=2)
                        # Cache successful response
                        if use_cache and self.cache_client.enabled:
                            self.cache_client.set(cache_key, response_text, None)
                        return (response_text, None)
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
                    response_text = (resp.choices[0].message.content or "").strip()
                    # Cache successful response
                    if use_cache and self.cache_client.enabled:
                        self.cache_client.set(cache_key, response_text, None)
                    return (response_text, None)
                    
            except Exception as e:
                msg = str(e)
                last_err = msg
                print(f"DEBUG: API call failed (attempt {attempt+1}): {msg}")
                
                if "unsupported" in msg.lower() or "parse" in msg.lower():
                    try:
                        kwargs["response_format"] = {"type": "json_object"}
                        if "max_completion_tokens" in kwargs:
                            kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")
                        # Ensure consistent temperature in fallback
                        kwargs["temperature"] = 0.3
                        kwargs["seed"] = 12345
                        resp = client.chat.completions.create(**kwargs)
                        response_text = (resp.choices[0].message.content or "").strip()
                        # Cache successful response
                        if use_cache and self.cache_client.enabled:
                            self.cache_client.set(cache_key, response_text, None)
                        return (response_text, None)
                    except Exception as e2:
                        last_err = str(e2)
                
                time.sleep(0.8 * (attempt + 1))
        
        return ("", last_err or "Unknown OpenAI error")

    def analyze_images(self, images: list, context: str) -> str:
        """
        Analyze images using GPT-4 Vision.

        Args:
            images: List of image data URLs or attachment dicts
            context: Context about the images

        Returns:
            Analysis text
        """
        print(f"DEBUG LLM: analyze_images called with {len(images)} images")
        print(f"DEBUG LLM: Enabled: {self.enabled}")

        if not self.enabled:
            print("DEBUG LLM: LLM not enabled, returning empty string")
            return ""

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            print(f"DEBUG LLM: OpenAI client created")

            # Build message content with images
            content = [
                {
                    "type": "text",
                    "text": f"Analyze these images in the context of: {context}\n\nProvide detailed insights about what's shown in the images."
                }
            ]

            for idx, img in enumerate(images):
                print(f"DEBUG LLM: Processing image {idx+1}/{len(images)}")
                # Handle both dict with data_url and direct data_url string
                data_url = img.get("data_url") if isinstance(img, dict) else img
                print(f"DEBUG LLM: Image {idx+1} data_url length: {len(data_url) if data_url else 0}")

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url
                    }
                })

            print(f"DEBUG LLM: Calling GPT-4o-mini vision API...")
            # Use gpt-4o-mini for vision (cost optimization) with reduced tokens (2000 -> 1500)
            resp = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=1500
            )

            result = resp.choices[0].message.content or ""
            print(f"DEBUG LLM: Vision API returned {len(result)} characters")
            return result

        except Exception as e:
            print(f"DEBUG LLM: Image analysis failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return f"Error analyzing images: {e}"