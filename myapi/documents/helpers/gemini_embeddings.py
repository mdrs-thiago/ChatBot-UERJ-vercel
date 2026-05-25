import os
from django.conf import settings
from google import genai
from langchain_core.embeddings import Embeddings

class GeminiEmbeddings(Embeddings):
    """
    Custom LangChain-compatible Embeddings class using the new google-genai SDK.
    Generates 3072-dimensional embeddings using the 'gemini-embedding-2' model.
    """
    def __init__(self):
        # Load API key from settings or environment safely
        if settings.configured:
            api_key = getattr(settings, "GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        else:
            api_key = os.environ.get("GEMINI_API_KEY")
            
        if not api_key:
            # Fallback to local settings load_dotenv in case settings isn't bootstrapped
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("GEMINI_API_KEY")
            
        self.client = genai.Client(api_key=api_key)
        if settings.configured:
            self.model = getattr(settings, "GEMINI_EMBEDDING_MODEL", os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2"))
        else:
            self.model = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

    def embed_documents(self, texts):
        if not texts:
            return []
        
        import time
        from google.genai.errors import ClientError
        import re
        
        embeddings = []
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            retries = 5
            success = False
            while retries > 0:
                try:
                    response = self.client.models.embed_content(
                        model=self.model,
                        contents=batch,
                        config={"output_dimensionality": 768},
                    )
                    embeddings.extend([e.values for e in response.embeddings])
                    success = True
                    break
                except ClientError as e:
                    if e.code == 429:
                        retries -= 1
                        if retries == 0:
                            raise e
                        # Try to parse suggested retry delay from error message
                        wait_time = 15.0
                        error_msg = str(e)
                        m = re.search(r'retry in ([\d\.]+)s', error_msg)
                        if m:
                            wait_time = float(m.group(1)) + 1.0
                        elif 'retryDelay' in error_msg:
                            # Try searching for seconds in other formats
                            m2 = re.search(r'retryDelay[^0-9]+(\d+)', error_msg)
                            if m2:
                                wait_time = float(m2.group(1)) + 1.0
                        
                        print(f"Rate limited (429). Retrying in {wait_time:.1f} seconds... ({retries} retries left)")
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
            
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config={"output_dimensionality": 768},
        )
        return response.embeddings[0].values
