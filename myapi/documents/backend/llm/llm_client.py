import logging
import os

import requests
from documents.decorators.latency_decorator import collect_latency
from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, model_name, provider="gemini", max_tokens=500, temperature=0.6, api_key=None):
        self.model_name = model_name
        self.provider = provider.lower()
        self.max_tokens = max_tokens
        self.temperature = temperature

        if self.provider == "gemini":
            client_key = api_key or os.environ.get("GEMINI_API_KEY")
            client = genai.Client(api_key=client_key)
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

    def _build_history_text(self, conversation_history):
        """Build a formatted conversation history string for prompt injection (Gemini)."""
        if not conversation_history:
            return ""
        lines = ["Histórico da conversa (para contexto):"]
        for entry in conversation_history[-6:]:  # limit to last 6 messages
            role = entry.get("role", "user")
            text = entry.get("text", "")
            label = "Usuário" if role == "user" else "Assistente"
            lines.append(f"{label}: {text}")
        return "\n".join(lines) + "\n\n"

    def _build_messages(self, question, context, conversation_history=None):
        """Build a messages list for chat-completion APIs (MoonshotAI, ZAI)."""
        system_msg = (
            "Você é o Assistente Institucional da UERJ. Responda às perguntas com base "
            "no contexto fornecido sobre regulamentos da universidade. Seja preciso e cite "
            "informações do contexto quando relevante. Se a resposta não estiver no contexto, "
            "diga que não encontrou informação suficiente."
        )
        messages = [{"role": "system", "content": system_msg}]

        # Inject history turns
        if conversation_history:
            for entry in conversation_history[-6:]:
                role = entry.get("role", "user")
                text = entry.get("text", "")
                messages.append({"role": role, "content": text})

        # Add current question with retrieved context
        user_content = f"Contexto dos documentos:\n{context}\n\nPergunta: {question}"
        messages.append({"role": "user", "content": user_content})
        return messages

    @collect_latency()
    def generate(self, question, context, metrics_collector=None, conversation_history=None):
        history_text = self._build_history_text(conversation_history)

        if self.provider == "gemini":
            prompt = (
                "Você é o Assistente Institucional da UERJ. Responda com base no contexto.\n\n"
                f"{history_text}"
                f"Contexto dos documentos:\n{context}\n\n"
                f"Pergunta atual: {question}\n\n"
                "Responda de forma clara e precisa com base no contexto fornecido."
            )
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
                "messages": self._build_messages(question, context, conversation_history),
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
                "messages": self._build_messages(question, context, conversation_history),
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
