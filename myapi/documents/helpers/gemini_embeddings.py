import os
import re
import time
from django.conf import settings
from google import genai
from google.genai.errors import ClientError
from langchain_core.embeddings import Embeddings

class GeminiEmbeddings(Embeddings):
    """
    Custom LangChain-compatible Embeddings class using the new google-genai SDK.
    Supports API key rotation via GEMINI_API_KEYS and configurable output dimension.
    """
    def __init__(self):
        # Fallback load_dotenv in case settings isn't bootstrapped
        if not settings.configured:
            from dotenv import load_dotenv
            load_dotenv()
            
        # Load keys from settings or environment
        api_keys_str = ""
        if settings.configured:
            api_keys_str = getattr(settings, "GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEYS", ""))
        else:
            api_keys_str = os.environ.get("GEMINI_API_KEYS", "")
            
        if api_keys_str:
            self.api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        else:
            self.api_keys = []
            
        # Fallback to GEMINI_API_KEY if list is empty
        if not self.api_keys:
            single_key = ""
            if settings.configured:
                single_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
            else:
                single_key = os.environ.get("GEMINI_API_KEY", "")
            if single_key:
                self.api_keys = [single_key]
                
        if not self.api_keys:
            raise ValueError("No Gemini API keys found in settings or environment (checked GEMINI_API_KEYS and GEMINI_API_KEY)")
            
        self.current_key_idx = 0
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
        
        # Load model and dimension
        if settings.configured:
            self.model = getattr(settings, "GEMINI_EMBEDDING_MODEL", os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2"))
            self.dimension = getattr(settings, "GEMINI_EMBEDDING_DIMENSION", int(os.environ.get("GEMINI_EMBEDDING_DIMENSION", 3072)))
        else:
            self.model = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
            self.dimension = int(os.environ.get("GEMINI_EMBEDDING_DIMENSION", 3072))

    def _rotate_key(self):
        if len(self.api_keys) <= 1:
            return False
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        # Re-initialize client
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
        print(f"rotated_gemini_key: Rotated to API key index {self.current_key_idx} (Key starting with: {self.api_keys[self.current_key_idx][:8]}...)")
        return True

    def embed_documents(self, texts):
        if not texts:
            return []
        
        embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            retries = 5
            success = False
            keys_tried = 0
            while retries > 0:
                try:
                    response = self.client.models.embed_content(
                        model=self.model,
                        contents=batch,
                        config={"output_dimensionality": self.dimension},
                    )
                    embeddings.extend([e.values for e in response.embeddings])
                    success = True
                    break
                except ClientError as e:
                    if e.code == 429:
                        # Try to rotate key first if we haven't tried all keys in this cycle
                        if keys_tried < len(self.api_keys) - 1:
                            if self._rotate_key():
                                keys_tried += 1
                                print("Rate limited (429). Rotated API key. Retrying batch immediately...")
                                continue
                        
                        # Fallback: sleep if all keys have been tried
                        retries -= 1
                        if retries == 0:
                            raise e
                        
                        # Reset keys_tried after sleeping to try the rotation cycle again
                        keys_tried = 0
                        
                        wait_time = 15.0
                        error_msg = str(e)
                        m = re.search(r'retry in ([\d\.]+)s', error_msg)
                        if m:
                            wait_time = float(m.group(1)) + 1.0
                        elif 'retryDelay' in error_msg:
                            m2 = re.search(r'retryDelay[^0-9]+(\d+)', error_msg)
                            if m2:
                                wait_time = float(m2.group(1)) + 1.0
                        
                        print(f"All keys rate limited. Sleeping for {wait_time:.1f} seconds... ({retries} retries left)")
                        time.sleep(wait_time)
                    else:
                        raise e
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise e
                    print(f"Unexpected error: {e}. Retrying in 5 seconds...")
                    time.sleep(5.0)
            
            if not success:
                raise Exception("Failed to embed batch after maximum retries.")

            # Sleep to respect rate limits of Gemini Free Tier
            if i + batch_size < len(texts):
                time.sleep(4.5)
        return embeddings

    def embed_query(self, text):
        if not text:
            return []
            
        retries = 3
        keys_tried = 0
        while retries > 0:
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config={"output_dimensionality": self.dimension},
                )
                return response.embeddings[0].values
            except ClientError as e:
                if e.code == 429:
                    if keys_tried < len(self.api_keys) - 1:
                        if self._rotate_key():
                            keys_tried += 1
                            print("Query rate limited. Rotated key and retrying query immediately...")
                            continue
                    retries -= 1
                    if retries == 0:
                        raise e
                    keys_tried = 0
                    time.sleep(5.0)
                else:
                    raise e
            except Exception as e:
                retries -= 1
                if retries == 0:
                    raise e
                time.sleep(2.0)
        raise Exception("Failed to embed query after maximum retries.")
