# AI Village Farming Assistant

A farmer-first multilingual, multimodal AI assistant built with React, FastAPI, MySQL, LangChain, LangGraph, Chroma, Groq and free/open-source supporting services.

## Current features

- Farmer registration and login
- JWT authentication
- Farmer/admin authorization
- Per-user conversation ownership
- ChatGPT-style recent conversations in the sidebar
- New Chat in the sidebar
- User messages right / assistant messages left
- Dark and light mode
- Responsive/mobile layout
- Farmer profile and farm context
- English, Hindi and Marathi text interaction
- Voice input
- Voice output through browser SpeechSynthesis
- Crop image upload and visual analysis
- Agricultural RAG with local multilingual embeddings
- Weather lookup
- Mandi/market price lookup
- Government scheme search
- Web search
- Source references

## Voice pipeline

The voice system supports `Auto`, `Marathi`, `Hindi` and `English`.

For the highest reliability, select the language you are about to speak. In `Auto` mode the backend lets Whisper detect the language first. When detection returns an unsupported language such as Gujarati/Italian or looks low-confidence, the system retries only with Marathi, Hindi and English and resolves close candidates when necessary.

The backend also adds agriculture-specific transcription prompts and records confidence metadata. The agent sanitizes historic LangChain message content before it reaches Groq so multimodal/list content cannot cause the Groq `messages[n].content must be a string` 400 error.

## Structure

```text
AI-Village-Farming-Assistant/
│
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── data/
│   │   └── knowledge/
│   ├── scripts/
│   │   ├── create_admin.py
│   │   ├── ingest_knowledge.py
│   │   └── migrate_security.py
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
│
└── requirements.txt
```

## Backend setup

Create MySQL database:

```sql
CREATE DATABASE farming_assistant
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Copy `.env.example` to `.env` inside `backend/` and add your own credentials.

Generate a JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Install dependencies from the project root:

```bash
pip install -r requirements.txt
```

Or:

```bash
cd backend
pip install -r requirements.txt
```

Run the security/database preparation scripts:

```bash
cd backend
python scripts/migrate_security.py
python scripts/create_admin.py
python scripts/ingest_knowledge.py
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

API docs in development:

```text
http://127.0.0.1:8000/docs
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Then open the Vite URL, normally:

```text
http://localhost:5173
```

## Environment files

Never commit real `.env` files or API keys. Use the included `.env.example` files.

## Notes

The project is designed around free tiers and open-source/local components. Provider/model availability and quotas can change over time, so verify active provider configuration before deployment.
