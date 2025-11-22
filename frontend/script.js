const API_BASE = "http://localhost:5000/api"; // ajustar caso rode em outro host/porta
const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const form = document.getElementById("form");

const sessionId = "session_default"; // você pode gerar id por usuário

function addMessage(text, who="bot"){
  const el = document.createElement("div");
  el.className = "message " + (who === "user" ? "user" : "bot");
  el.innerHTML = `<div>${escapeHtml(text)}</div>`;
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function escapeHtml(unsafe) {
  return unsafe
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;");
}

async function sendMessage(){
  const text = inputEl.value.trim();
  if(!text) return;
  addMessage(text, "user");
  inputEl.value = "";
  // Mostrar placeholder de "digitando..."
  const loading = document.createElement("div");
  loading.className = "message bot";
  loading.id = "loading";
  loading.innerText = "Gerando resposta...";
  chatEl.appendChild(loading);
  chatEl.scrollTop = chatEl.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ message: text, session_id: sessionId })
    });
    const data = await res.json();
    document.getElementById("loading")?.remove();

    if (data.reply) {
      addMessage(data.reply, "bot");
    } else if (data.error) {
      addMessage("Erro: " + data.error, "bot");
    } else {
      addMessage("Resposta inválida do servidor.", "bot");
    }
  } catch (err) {
    document.getElementById("loading")?.remove();
    addMessage("Erro de conexão: " + err.message, "bot");
  }
}

sendBtn.addEventListener("click", sendMessage);
form.addEventListener("submit", (e) => { e.preventDefault(); sendMessage(); });

// opcional: carregar histórico ao abrir
async function loadHistory(){
  try {
    const res = await fetch(`${API_BASE}/history?session_id=${sessionId}&limit=200`);
    const data = await res.json();
    chatEl.innerHTML = "";
    if (data.messages) {
      for (const m of data.messages) {
        addMessage(m.content, m.role === "assistant" ? "bot" : "user");
      }
    }
  } catch (e) {
    console.warn("Não foi possível carregar histórico:", e);
  }
}
loadHistory();
