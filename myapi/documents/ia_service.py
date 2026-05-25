import logging

logger = logging.getLogger(__name__)
import os

from dotenv import load_dotenv

load_dotenv()

from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def answer_question(question, context):
    """
    Usa a API do Gemini para responder a uma pergunta baseada em um contexto.

    :param question: Pergunta feita pelo usuário.
    :param context: Texto do documento que será usado para responder.
    :return: Resposta gerada pela IA.
    """
    try:
        logger.info(f"[answer_question] Pergunta recebida: {question}")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Contexto: {context}\n\nPergunta: {question}\n\nResponda com base no contexto.",
        )
        if response.text:
            answer = response.text
            logger.info(f"[answer_question] Resposta gerada: {answer[:200]}...")
        else:
            answer = "Não foi possível gerar uma resposta."
        logger.info(f"[answer_question] Resposta gerada: {answer[:200]}...")
        return answer
    except Exception as e:
        logger.error(f"[answer_question] Erro ao obter resposta da IA: {str(e)}")
        return f"Erro ao obter resposta da IA: {str(e)}"
