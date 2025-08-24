# ChatBot-UERJ

Este projeto é uma API Django para perguntas e respostas sobre documentos jurídicos, utilizando técnicas de RAG (Retrieval Augmented Generation) e integração com IA (Gemini). Os documentos são indexados e buscados por similaridade semântica, permitindo respostas precisas e contextualizadas.

## Principais Funcionalidades
- Upload de documentos jurídicos
- Indexação e chunking dos documentos para busca eficiente
- Perguntas sobre documentos específicos ou sobre toda a base
- Busca semântica usando FAISS e embeddings (HuggingFace)
- Resposta gerada por IA (Gemini)
- Monitoramento de tempo de execução via middleware
- Logs detalhados de requisições e respostas
- Testes unitários e de integração com pytest

## Estrutura do Projeto
```
ChatBot-UERJ/
├── myapi/
│   ├── manage.py
│   ├── myapi/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── documents/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── ia_service.py
│   │   ├── helpers/
│   │   │   ├── chunk_helper.py
│   │   │   ├── normalize.py
│   │   │   └── tests/
│   │   │       ├── test_chunk_helper_pytest.py
│   │   │       └── test_normalize_pytest.py
│   │   └── ...
│   ├── middleware/
│   │   └── execution_time.py
│   └── ...
├── faiss_index/
├── requirements.txt
└── README.md
```

## Passo a passo para rodar o projeto

1. **Crie e ative o ambiente virtual:**
   ```sh
   python -m venv venv
   # No Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # No Windows CMD:
   venv\Scripts\activate.bat
   # No Linux/Mac:
   source venv/bin/activate
   ```

2. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Obtenha sua chave GEMINI_API_KEY:**
   - Crie uma conta ou acesse o painel do Google Gemini.
   - Gere uma chave de API e copie o valor.

4. **Crie o arquivo `.env` na raiz do projeto e adicione sua chave:**
   ```
   GEMINI_API_KEY=coloque_sua_chave_aqui
   ```

5. **Realize as migrações do banco de dados:**
   ```sh
   cd myapi
   python manage.py migrate
   ```

6. **Rode o servidor Django:**
   ```sh
   python manage.py runserver 0.0.0.0:8000
   ```

Pronto! O projeto estará rodando em http://localhost:8000

## Como rodar os testes

### Testes unitários com pytest (helpers)
Na raiz do projeto:
```sh
pytest
```
Ou para um teste específico:
```sh
pytest myapi/documents/helpers/tests/test_chunk_helper_pytest.py
pytest myapi/documents/helpers/tests/test_normalize_pytest.py
```

---

Para dúvidas ou sugestões, entre em contato com o mantenedor do projeto.