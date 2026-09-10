# 🦋 MSN Conversinhas
https://terapia-rs.onrender.com/
<img width="473" height="599" alt="image" src="https://github.com/user-attachments/assets/7535626f-e617-41ba-81dd-5d64723e11a5" />


Releitura nostálgica do **MSN / Windows Live Messenger 2009** (auge no Brasil 🇧🇷) feita com **Python + Flask + Socket.IO** no servidor e **HTML + CSS + JS puro** no cliente. Sem senha: é só escolher um apelido e entrar.

## ✨ O que tem

- **Visual WLM 2009** — display pictures quadradas com moldura e gem de status, frase pessoal com `♪ Ouvindo:`, grupos Favoritos/Online/Ocupado/Ausente, fonte Segoe UI, header azul Luna
- **Chat em grupo em tempo real** — mensagens, fotos, indicador "digitando…", histórico persistido
- **Chamar atenção (Nudge)** — ⚡ treme a janela com som, igual ao original
- **Formatação estilo Messenger Plus!** — `**negrito**`, `//itálico//`, `__sublinhado__` + botões B/I/U
- **Emoticons clássicos** — `:)` `:D` `;)` `:P` `<3` + seletor de emojis
- **Fotos** — pelo botão 📷, arrastando pra janela ou `Ctrl+V` (até 4 por vez)
- **Notificações em 3 camadas**
  - 🔊 sons sintetizados (mensagem, nudge, login/logout)
  - 💬 toast interno que sobe no canto (com foto e nome de quem mandou)
  - 🪟 **pop-up do Windows estilo Teams** quando você está em outra guia/app (botão 🔔 Avisos pede a permissão)
- **Título piscando** com contador de não-lidas `(2) Nova mensagem!`

## 🛠️ Tecnologias

| Parte | Stack |
|---|---|
| Servidor | Flask 3 + Flask-SocketIO 5 |
| Cliente | HTML + CSS + JS (sem framework) + socket.io |
| Persistência | `data/history.json` (últimas 2000 mensagens) |

## 🚀 Como rodar

```bash
cd Chat_2
pip install -r requirements.txt
python server.py
```

Abre `http://127.0.0.1:5000` — chama um amigo na mesma Wi-Fi com `http://SEU-IP:5000`.

> 💡 O **pop-up do Windows** só funciona em contexto seguro (`localhost` ou `HTTPS`). Via `http://192.168...` o navegador bloqueia — aí vale só o toast dentro da página.

## ☁️ Como publicar (Render, grátis)

1. Suba o código pro GitHub (`git push origin main`)
2. Em `render.com` → New → Web Service → conecte o repositório
3. Build: `pip install -r requirements.txt` · Start: `python server.py` · plano Free
4. Pronto: você ganha um `https://...onrender.com` com HTTPS (pop-up funcionando)

⚠️ No plano grátis o disco é efêmero: o `history.json` zera a cada restart/redeploy e o serviço dorme sem uso.

## 📁 Estrutura

```
Chat_2/
├── server.py          # Flask + Socket.IO (login, mensagens, nudge, perfis, histórico)
├── requirements.txt
├── static/
│   ├── index.html     # login (só apelido) + lista de contatos + conversa
│   ├── style.css      # tema WLM 2009
│   ├── app.js         # Socket.IO, toasts, Notification API, drag-drop, formatação
│   └── lib/socket.io.min.js
└── data/history.json  # histórico (gerado em execução)
```


---

Feito com nostalgia 🦋 — *conectando pessoas desde 1998*.
