/* ===================== MSN MESSENGER — frontend ===================== */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const esc = (s) =>
    (s == null ? "" : String(s)).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  const STATUS = { online: "Online", ausente: "Ausente", ocupado: "Ocupado" };
  const STATUS_LABEL = { online: "Online", ausente: "Ausente", ocupado: "Ocupado" };
  const ST = { online: "s-online", ausente: "s-away", ocupado: "s-busy" };

  /* ---------------- emoticons (clássico MSN) ---------------- */
  const EMO_MAP = {
    ":-)": "😊", ":)": "😊", ":-D": "😄", ":D": "😄", ";-）": "😉", ";-)": "😉", ";)": "😉",
    "-_-": "😑", ":-|": "😐", ":|": "😐", ":-/": "😕", ":/": "😕", ":-P": "😛", ":P": "😛",
    ":-O": "😮", ":O": "😮", ":-*": "😘", ":*": "😘", ":-@": "😡", ":@": "😡", ":-$": "😳", ":$": "😳",
    ">:(": "😠", "(Y)": "👍", "(N)": "👎", ":(": "😢", "<3": "❤️", "8)": "😎", "(H)": "😎",
    ":dance": "🕺", ":party": "🎉", ":lol": "😂", ":cry": "😭", ":love": "😍",
  };
  for (const k of Object.keys(EMO_MAP)) EMO_MAP[esc(k)] = EMO_MAP[k];

  function reEsc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  const EMO_RE = new RegExp(
    Object.keys(EMO_MAP).sort((a, b) => b.length - a.length).map(reEsc).join("|"),
    "g"
  );

  function parseEmoticons(text) {
    return text.replace(EMO_RE, (m) => `<span class="em-char">${EMO_MAP[m]}</span>`);
  }

  const PICKER_EMOTICONS = [
    "😊", "😄", "😉", "😛", "😢", "😡", "😮", "😘",
    "😳", "🙂", "😑", "😎", "❤️", "👍", "👎", "🕺",
    "🎉", "😂", "😭", "😍", "🎵", "⭐", "🔥", "🌹",
  ];

  /* ---------------- sons clássicos (WebAudio) ---------------- */
  let audioCtx = null;
  function ctx() {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();
    return audioCtx;
  }
  function tone(freq, start, dur, type = "sine", gain = 0.14) {
    const c = ctx();
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = type; osc.frequency.value = freq;
    g.gain.setValueAtTime(0, c.currentTime + start);
    g.gain.linearRampToValueAtTime(gain, c.currentTime + start + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + start + dur);
    osc.connect(g); g.connect(c.destination);
    osc.start(c.currentTime + start); osc.stop(c.currentTime + start + dur + 0.02);
  }
  const SOUND = {
    message() { tone(880, 0, 0.09); tone(1318, 0.11, 0.14); },
    nudge() { [180, 150].forEach((f, i) => tone(f, i * 0.16, 0.22, "sawtooth", 0.12)); },
    login() { [660, 880, 1100].forEach((f, i) => tone(f, i * 0.09, 0.12)); },
    logout() { [1100, 880, 660].forEach((f, i) => tone(f, i * 0.09, 0.12)); },
  };

  /* ---------------- estado global ---------------- */
  let me = null;            // perfil próprio (com sid)
  const users = {};         // sid -> perfil
  const socket = io({ transports: ["websocket", "polling"] });
  let lastGroup = null;     // {sid, time, el}
  let typingTimer = null;
  let nickColor = "#2F5FAD";
  let loginAvatar = null;

  /* ---------------- avatar helpers ---------------- */
  const AVATAR_COLORS = ["#2F5FAD", "#008844", "#9933CC", "#C25A14", "#cc3150", "#2a7d8f", "#5a6aa8", "#e06600"];

  function avatarHTML(profile, initSizePx = 20) {
    const st = profile && profile.status ? profile.status : "online";
    const name = profile && profile.name ? profile.name : "?";
    const color = AVATAR_COLORS[(name.charCodeAt(0) || 0) % AVATAR_COLORS.length];
    if (profile && profile.avatar) {
      return `<img src="${profile.avatar}" alt="">`;
    }
    return `<div class="init" style="background:${color}; font-size:${initSizePx}px;">${esc(name[0].toUpperCase())}</div>`;
  }

  function setAvatar(el, profile, initSizePx) {
    if (!el) return;
    const st = profile && profile.status ? profile.status : "online";
    const sizeCls = Array.from(el.classList).find((c) => c.startsWith("av-"));
    el.className = `avatar-frame st-${st} ${sizeCls || ""}`;
    el.innerHTML = avatarHTML(profile, initSizePx);
  }

  function readGravityPreview() { /* placeholder para futura extensão */ }

  function readImage(file, cb, opts = {}) {
    if (!file || !file.type.startsWith("image/")) return;
    const max = opts.max || 96;
    const mime = opts.type || "image/png";
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        let { width: w, height: h } = img;
        if (w > max || h > max) {
          const r = Math.min(max / w, max / h);
          w = Math.round(w * r); h = Math.round(h * r);
        }
        const cv = document.createElement("canvas");
        cv.width = w; cv.height = h;
        cv.getContext("2d").drawImage(img, 0, 0, w, h);
        cb(cv.toDataURL(mime, mime === "image/jpeg" ? 0.85 : undefined));
      };
      img.src = reader.result;
    };
    reader.readAsDataURL(file);
  }

  function lettersAvatar(name, color) {
    const cv = document.createElement("canvas");
    cv.width = 96; cv.height = 96;
    const g = cv.getContext("2d");
    g.beginPath(); g.arc(48, 48, 46, 0, Math.PI * 2);
    g.fillStyle = color; g.fill();
    g.fillStyle = "#ffffff";
    g.font = "bold 44px Tahoma";
    g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText((name[0] || "?").toUpperCase(), 48, 50);
    return cv.toDataURL("image/png");
  }

  /* ---------------- tempo ---------------- */
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function fmtTime(ms) {
    const d = new Date(ms);
    const today = new Date();
    const sameDay = d.toDateString() === today.toDateString();
    const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
    return sameDay ? hm : `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${hm}`;
  }

  /* ==================== RENDER: MENSAGENS ==================== */
  const conv = $("conversation");

  function newGroup(entry) {
    const g = document.createElement("div");
    g.className = "msg-group";

    const av = document.createElement("div");
    av.className = "msg-group g-avatar avatar-frame st-online av-34";
    const p = users[entry.sid] || { name: entry.sender, status: "online", avatar: null };
    av.className = `avatar-frame st-${p.status || "online"} g-avatar av-34`;
    av.innerHTML = avatarHTML(p, 13);

    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    const hdr = document.createElement("div");
    hdr.className = "msg-header";
    hdr.innerHTML = `<span class="t">${fmtTime(entry.time)}</span><span class="n" style="color:${entry.color || p.color || "#2F5FAD"}">${esc(entry.sender)} diz:</span>`;
    bubble.appendChild(hdr);
    g.appendChild(av);
    g.appendChild(bubble);
    conv.appendChild(g);

    lastGroup = { sid: entry.sid, time: entry.time, bubble, group: g };
    return { g, bubble };
  }

  function addMessage(entry) {
    const nearBottom = conv.scrollHeight - conv.scrollTop - conv.clientHeight < 120;

    if (entry.type === "system") {
      lastGroup = null;
      const d = document.createElement("div");
      d.className = "msg-system"; d.id = "sys-" + entry.time + "-" + Math.random();
      d.innerHTML = `<span class="t">[${fmtTime(entry.time)}]</span> ${esc(entry.text)}`;
      conv.appendChild(d);
    } else if (entry.type === "nudge") {
      lastGroup = null;
      const d = document.createElement("div");
      d.className = "msg-nudge";
      d.innerHTML = `⚡ <b>${esc(entry.sender)}</b> enviou um Nudge! às ${fmtTime(entry.time)}`;
      conv.appendChild(d);
      if (entry.sid !== mySid()) { triggerNudge(); SOUND.nudge(); }
    } else {
      const sameUser = lastGroup && lastGroup.sid === entry.sid;
      const within = lastGroup && entry.time - lastGroup.time < 10 * 60 * 1000;
      let bubble;
      if (sameUser && within) {
        lastGroup.time = entry.time;
        bubble = lastGroup.bubble;
      } else {
        const { bubble: b } = newGroup(entry);
        bubble = b;
      }
      if (entry.text) {
        const body = document.createElement("div");
        body.className = "msg-body";
        body.innerHTML = parseEmoticons(esc(entry.text));
        bubble.appendChild(body);
      }
      if (entry.image) {
        const imgEl = document.createElement("img");
        imgEl.className = "msg-img";
        imgEl.src = entry.image;
        imgEl.title = "Clique para ampliar";
        imgEl.onclick = () => openImageViewer(entry.image);
        bubble.appendChild(imgEl);
      }
      if (entry.sid && entry.sid !== mySid()) SOUND.message();
    }
    if (nearBottom) autoScroll();
    if (entry.sid && entry.sid === mySid()) autoScroll();
  }

  function autoScroll() { conv.scrollTop = conv.scrollHeight; }

  function mySid() { return (me && me.sid) || null; }

  /* ==================== RENDER: CONTATOS ==================== */
  function onlineUsers() {
    return Object.values(users).filter((u) => u.status === "online" && (me && u.sid !== me.sid));
  }
  function otherUsers() {
    return Object.values(users).filter(
      (u) => u.status !== "online" && (me && u.sid !== me.sid)
    );
  }

  function renderContacts() {
    const favEl = $("online-contacts");
    const allEl = $("all-contacts");
    const empty = $("contacts-empty");
    favEl.innerHTML = "";
    allEl.innerHTML = "";

    const on = onlineUsers();
    const off = otherUsers();

    favList(on, favEl);
    favList(off, allEl);

    $("contact-list").querySelectorAll(".contact-group .cnt")[0].textContent = `(${on.length})`;
    $("contact-list").querySelectorAll(".contact-group .cnt")[1].textContent = `(${off.length})`;

    empty.classList.toggle("hidden", on.length + off.length > 0);
    $("ch-sub").textContent = `${Object.keys(users).length - (me ? 1 : 0)} contato(s) online`;
  }

  function favList(list, container) {
    for (const p of list.sort((a, b) => a.name.localeCompare(b.name))) {
      const row = document.createElement("div");
      row.className = "contact";
      row.dataset.sid = p.sid;
      row.innerHTML = `
        <div class="avatar-frame st-${p.status} av-34" style="pointer-events:none">${avatarHTML(p, 13)}</div>
        <div class="cinfo">
          <div class="cname" style="color:${p.color || "#2F5FAD"}">${esc(p.name)}</div>
          <div class="cmsg">${p.message ? esc(p.message) : "—"}</div>
        </div>
        <div class="cdot sdonline" style="background:${p.status === "online" ? "var(--online)" : p.status === "ausente" ? "var(--away)" : "var(--busy)"}"></div>`;
      row.addEventListener("click", () => {
        container.querySelectorAll(".contact").forEach((r) => r.classList.remove("active"));
        row.classList.add("active");
      });
      container.appendChild(row);
    }
  }

  /* ==================== MEU PERFIL (UI) ==================== */
  function renderMe() {
    if (!me) return;
    setAvatar($("me-avatar"), me, 13);
    $("me-name").textContent = me.name;
    $("me-name").style.color = me.color || "#000";
    $("me-personal").textContent = me.message || "Clique para adicionar uma mensagem pessoal";
    $("status-label").textContent = STATUS_LABEL[me.status] || "Online";
    $("status-select").querySelector(".sdot").className = "sdot " + ST[me.status];
    // detalhe: o contador da lista
    renderContacts();
  }

  /* ==================== LOGIN ==================== */
  function generateSwatches(container, active) {
    container.innerHTML = "";
    for (const c of ["#2F5FAD", "#008844", "#CC0000", "#9933CC", "#FF8C00", "#E06600", "#5A5A5A", "#C25A14"]) {
      const s = document.createElement("span");
      s.className = "swatch" + (c === active ? " active" : "");
      s.style.background = c;
      s.onclick = () => {
        container.querySelectorAll(".swatch").forEach((x) => x.classList.remove("active"));
        s.classList.add("active");
        if (container.id === "name-colors") nickColor = c;
        if (container.id === "modal-colors") modalColor = c;
      };
      container.appendChild(s);
    }
  }
  generateSwatches($("name-colors"), nickColor);
  let modalColor = nickColor;

  function loginAvatarChanged(url) {
    loginAvatar = url;
    setAvatar($("login-avatar-preview"), { status: "online", avatar: url, name: $("login-name").value || "?" }, 22);
  }

  $("login-avatar-btn").onclick = () => $("login-avatar-input").click();
  $("login-avatar-input").onchange = (e) => {
    const f = e.target.files[0];
    if (f) readImage(f, loginAvatarChanged);
  };
  $("login-avatar-clear").onclick = () => loginAvatarChanged(null);
  $("login-name").oninput = () => {
    setAvatar($("login-avatar-preview"), { status: "online", avatar: loginAvatar, name: $("login-name").value || "?" }, 22);
  };

  $("login-submit").onclick = doLogin;
  $("login-name").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });

  function doLogin() {
    const name = $("login-name").value.trim();
    if (!name) { $("login-name").focus(); return; }
    const profile = {
      name,
      color: nickColor,
      avatar: null,
      message: $("login-message").value.trim(),
      status: $("login-status").value,
    };
    if (loginAvatar) profile.avatar = loginAvatar;
    socket.emit("login", profile);
    sessionStorage.setItem("msn_profile", JSON.stringify(profile));
  }

  /* ==================== SOCKET ==================== */
  socket.on("connect", () => {
    const saved = sessionStorage.getItem("msn_profile");
    if (saved) {
      try { socket.emit("login", JSON.parse(saved)); } catch (e) {}
    }
  });

  socket.on("you", (p) => {
    me = p;
    $("login-screen").classList.add("hidden");
    $("app").classList.remove("hidden");
    renderMe();
  });

  socket.on("history", (list) => {
    conv.innerHTML = "";
    lastGroup = null;
    for (const m of list) addMessage(m);
    conv.scrollTop = conv.scrollHeight;
  });

  socket.on("users", (list) => {
    for (const sid of Object.keys(users)) delete users[sid];
    for (const p of list) users[p.sid] = p;
    renderContacts();
  });

  socket.on("message", (entry) => addMessage(entry));

  socket.on("user_renamed", ({ old, now: newName, sid }) => {
    if (users[sid]) users[sid].name = newName;
  });

  socket.on("nudge", () => { triggerNudge(); SOUND.nudge(); });

  socket.on("typing", ({ name, sid }) => {
    if (sid === mySid()) return;
    const row = $("typing-row");
    row.textContent = "";
    const sp = document.createElement("span");
    sp.textContent = `${name} está digitando…`;
    row.appendChild(sp);
    row.classList.remove("hidden");
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
      row.classList.add("hidden");
      row.textContent = "";
    }, 2500);
  });

  /* ==================== ENVIO ==================== */
  function openImageViewer(src) {
    const ov = document.createElement("div");
    ov.className = "img-viewer";
    const img = document.createElement("img");
    img.src = src;
    ov.appendChild(img);
    ov.onclick = () => ov.remove();
    document.body.appendChild(ov);
  }

  $("image-send-btn").onclick = () => $("image-input").click();
  $("image-input").onchange = (e) => {
    const f = e.target.files[0];
    e.target.value = "";
    if (!f) return;
    readImage(f, (url) => socket.emit("message", { image: url }), {
      max: 900,
      type: "image/jpeg",
    });
  };

  function send() {
    const input = $("message-input");
    const text = input.value.trim();
    if (!text) return;
    socket.emit("message", { text });
    input.value = "";
    input.style.height = "auto";
    input.focus();
  }
  $("send-btn").onclick = send;
  $("message-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  });
  $("message-input").addEventListener("input", () => {
    socket.emit("typing", {});
    $("message-input").style.height = "auto";
    $("message-input").style.height = Math.min($("message-input").scrollHeight, 96) + "px";
  });

  /* ==================== NUDGE ==================== */
  function triggerNudge() {
    const app = $("app");
    app.classList.remove("shaking");
    void app.offsetWidth;
    app.classList.add("shaking");
    const ov = $("nudge-overlay");
    ov.classList.add("boom");
    setTimeout(() => ov.classList.remove("boom"), 350);
  }
  $("chat-window").querySelector(".act[title='Nudge! Chamar atenção']").onclick = () => socket.emit("nudge", {});

  /* ==================== EMOTICONS ==================== */
  const picker = $("emoticon-picker");
  picker.innerHTML = "";
  for (const em of PICKER_EMOTICONS) {
    const b = document.createElement("button");
    b.className = "em-btn";
    b.textContent = em;
    b.onclick = () => {
      const input = $("message-input");
      input.value += (input.value.endsWith(" ") || !input.value ? "" : " ") + em + " ";
      input.focus(); picker.classList.add("hidden");
    };
    picker.appendChild(b);
  }
  $("chat-window").querySelector(".act[title='Emoticons']").onclick = (e) => {
    picker.classList.toggle("hidden");
    e.stopPropagation();
  };
  document.addEventListener("click", (e) => {
    if (!picker.contains(e.target)) picker.classList.add("hidden");
  });

  /* ==================== FUNDO DA CONVERSA ==================== */
  const BG = [
    "repeating-linear-gradient(0deg, #fbfdff, #fbfdff 2px, #f2f7fc 2px, #f2f7fc 2.5px)",
    "linear-gradient(180deg, #eaf6ff, #ffffff)",
    "linear-gradient(180deg, #fffbe8, #ffffff)",
    "linear-gradient(180deg, #ffeef5, #ffffff)",
    "linear-gradient(180deg, #eafff0, #ffffff)",
  ];
  let bgIndex = 0;
  $("chat-window").querySelector(".act[title='Alterar cor do fundo']").onclick = () => {
    bgIndex = (bgIndex + 1) % BG.length;
    conv.style.background = BG[bgIndex];
  };

  /* ==================== LIMPAR CONVERSA (local) ==================== */
  $("chat-window").querySelector(".act[title='Limpar conversa']").onclick = () => {
    conv.innerHTML = ""; lastGroup = null;
  };

  /* ==================== ME-BAR: status e editar perfil ==================== */
  $("status-select").onclick = (e) => {
    e.stopPropagation();
    $("status-menu").classList.toggle("hidden");
  };
  document.addEventListener("click", () => $("status-menu").classList.add("hidden"));

  $("status-menu").querySelectorAll(".si[data-status]").forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      socket.emit("update_profile", { status: btn.dataset.status, message: me.message, name: me.name, color: me.color, avatar: me.avatar });
      $("status-menu").classList.add("hidden");
    };
  });
  $("sign-out").onclick = (e) => {
    e.stopPropagation();
    sessionStorage.removeItem("msn_profile");
    location.reload();
  };

  $("profile-edit-btn").onclick = openProfileModal;
  $("me-avatar").onclick = openProfileModal;
  $("me-card").onclick = openProfileModal;

  /* ==================== MODAL PERFIL ==================== */
  function openProfileModal() {
    if (!me) return;
    setAvatar($("modal-avatar-preview"), me, 24);
    $("modal-name").value = me.name;
    $("modal-message").value = me.message || "";
    $("modal-status").value = me.status;
    modalColor = me.color || "#2F5FAD";
    generateSwatches($("modal-colors"), modalColor);
    $("profile-modal").classList.remove("hidden");
  }

  $("modal-avatar-btn").onclick = () => $("modal-avatar-input").click();
  $("modal-avatar-input").onchange = (e) => {
    const f = e.target.files[0];
    if (f) readImage(f, (url) => {
      me.avatar = url;
      setAvatar($("modal-avatar-preview"), me, 24);
    });
  };
  $("modal-avatar-clear").onclick = () => {
    me.avatar = null;
    setAvatar($("modal-avatar-preview"), me, 24);
  };

  $("modal-cancel").onclick = () => $("profile-modal").classList.add("hidden");
  $("modal-save").onclick = () => {
    const p = {
      name: $("modal-name").value.trim() || me.name,
      color: modalColor,
      message: $("modal-message").value.trim(),
      status: $("modal-status").value,
      avatar: me.avatar || null,
    };
    socket.emit("update_profile", p);
    const saved = sessionStorage.getItem("msn_profile");
    if (saved) {
      const sp = JSON.parse(saved);
      sessionStorage.setItem("msn_profile", JSON.stringify({ ...sp, ...p }));
    }
    $("profile-modal").classList.add("hidden");
  };

  /* startup */
  const saved = sessionStorage.getItem("msn_profile");
  if (saved) {
    try {
      const p = JSON.parse(saved);
      $("login-name").value = p.name;
      $("login-message").value = p.message || "";
      $("login-status").value = p.status || "online";
      nickColor = p.color || "#2F5FAD";
      generateSwatches($("name-colors"), nickColor);
      loginAvatar = p.avatar || null;
      loginAvatarChanged(loginAvatar);
      $("login-submit").textContent = "Conectando…";
    } catch (e) {}
  }
  $("login-name").focus();
})();
