import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import openai
from sqlalchemy.orm import Session
from .db import engine, SessionLocal
from .models import Base, Message

# Carrega .env se existir
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️  Aviso: variável OPENAI_API_KEY não encontrada. Configure-a antes de rodar.")
openai.api_key = OPENAI_API_KEY

# Cria DB / tabelas
Base.metadata.create_all(bind=engine)

app = Flask(__name__)
CORS(app)  # permitir requests do front-end

# Prompt system base para manter neutralidade e função educativa
SYSTEM_PROMPT = (
    "Você é um assistente educacional neutro especializado em política. "
    "Seu objetivo é explicar conceitos, processos, instituições e ideologias "
    "de forma clara e imparcial para estudantes. Não promova candidatos, "
    "partidos ou posições políticas. Responda em português e com linguagem acessível."
)

def save_message(db: Session, role: str, content: str, session_id: str = "default"):
    msg = Message(role=role, content=content, session_id=session_id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Envia uma mensagem do usuário, chama a OpenAI e retorna resposta.
    Body JSON:
    {
      "message": "Pergunta do usuário",
      "session_id": "id opcional para agrupar conversas"
    }
    """
    data = request.json
    user_msg = data.get("message", "")
    session_id = data.get("session_id", "default")

    if not user_msg:
        return jsonify({"error": "message is required"}), 400

    # Salva a mensagem do usuário
    db = SessionLocal()
    save_message(db, "user", user_msg, session_id)

    # Monta o histórico para enviar ao modelo (puxamos últimos 10)
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
    # Build messages: start with system prompt
    chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in msgs[-10:]:
        role = "assistant" if m.role == "assistant" else "user"
        chat_history.append({"role": role, "content": m.content})

    # Gera a resposta com OpenAI
    try:
        # Ajuste o model conforme sua conta (ex: "gpt-4o-mini" ou outro disponível)
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=chat_history,
            max_tokens=500,
            temperature=0.2
        )
        assistant_text = resp.choices[0].message.content.strip()
    except Exception as e:
        assistant_text = "Desculpe, ocorreu um erro ao gerar a resposta: " + str(e)

    # Salva a resposta
    save_message(db, "assistant", assistant_text, session_id)
    db.close()

    return jsonify({"reply": assistant_text})

@app.route("/api/history", methods=["GET"])
def history():
    """
    Retorna histórico (últimas mensagens) de uma sessão.
    Query params: session_id (opcional), limit (opcional)
    """
    session_id = request.args.get("session_id", "default")
    limit = int(request.args.get("limit", 100))
    db = SessionLocal()
    msgs = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).limit(limit).all()
    out = [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs]
    db.close()
    return jsonify({"messages": out})

@app.route("/api/clear", methods=["POST"])
def clear_history():
    """
    Limpa histórico de uma sessão.
    Body JSON: { "session_id": "default" }
    """
    data = request.json or {}
    session_id = data.get("session_id", "default")
    db = SessionLocal()
    cnt = db.query(Message).filter(Message.session_id == session_id).delete()
    db.commit()
    db.close()
    return jsonify({"cleared": cnt})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
