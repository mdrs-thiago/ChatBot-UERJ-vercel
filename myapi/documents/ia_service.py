import os
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
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=f"Contexto: {context}\n\nPergunta: {question}\n\nResponda com base no contexto."
        )

        return response.text if response.text else "Não foi possível gerar uma resposta."

    except Exception as e:
        return f"Erro ao obter resposta da IA: {str(e)}"
