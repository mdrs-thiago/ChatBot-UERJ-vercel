import logging
import os

import requests
from documents.decorators.latency_decorator import collect_latency
from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, model_name, provider="gemini", max_tokens=500, temperature=0.6):
        self.model_name = model_name
        self.provider = provider.lower()
        self.max_tokens = max_tokens
        self.temperature = temperature

        if self.provider == "gemini":
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            self.gemini_client = client
        elif self.provider == "moonshotai":
            self.moonshot_api_key = os.environ.get("MOONSHOT_API_KEY")
            self.moonshot_api_url = os.environ.get(
                "MOONSHOT_API_URL", "https://api.moonshot.ai/v1/chat/completions"
            )
        elif self.provider == "zai":
            self.zai_api_key = os.environ.get("ZAI_API_KEY")
            self.zai_api_url = os.environ.get(
                "ZAI_API_URL", "https://api.z.ai/api/paas/v4/chat/completions"
            )
        else:
            raise ValueError(f"Provider {provider} não suportado")

    @collect_latency()
    def generate(self, question, context, metrics_collector=None):
        prompt = f"Contexto: {context}\n\nPergunta: {question}\n\nResponda com base no contexto."

        if self.provider == "gemini":
            response = self.gemini_client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return (
                response.text
                if response.text
                else "Não foi possível gerar uma resposta."
            )

        elif self.provider == "moonshotai":
            headers = {
                "Authorization": f"Bearer {self.moonshot_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "Responda com base no contexto."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": self.temperature,
            }
            response = requests.post(
                self.moonshot_api_url, headers=headers, json=payload
            )
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "Não foi possível gerar uma resposta."
            else:
                return f"Erro MoonshotAI: {response.status_code} {response.text}"

        elif self.provider == "zai":
            headers = {
                "Authorization": f"Bearer {self.zai_api_key}",
                "Content-Type": "application/json",
                "Accept-Language": "en-US,en",
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "Responda com base no contexto"},
                    {"role": "user", "content": prompt},
                ],
            }
            response = requests.post(self.zai_api_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "Não foi possível gerar uma resposta."
            else:
                return f"Erro ZAI: {response.status_code} {response.text}"
