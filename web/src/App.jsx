import { useEffect, useRef, useState } from "react";
import Message from "./components/Message.jsx";
import LogPanel from "./components/LogPanel.jsx";
import Composer from "./components/Composer.jsx";
import { BrandMark, BotIcon, SunIcon, MoonIcon } from "./components/icons.jsx";
import {
  fetchServers,
  fetchUsage,
  resetConversation,
  sendMessage,
  setModel as apiSetModel,
} from "./api.js";

const EXAMPLES = [
  "List the fields that are ready to cut.",
  "I have 20000 tons of milling capacity this week — what should I cut?",
  "Create a README.md in the workspace, commit it, and show the git log.",
  "For field F-14, register a lab sample with pol 14.2 and brix 16.7.",
];

// Pull the tool names out of a turn's log delta (the tools/call requests we sent).
function toolsFromLog(log) {
  return log
    .filter((e) => e.direction === "send" && e.method === "tools/call")
    .map((e) => e.payload?.params?.name)
    .filter(Boolean);
}

// Build a human-readable trace of the last turn: host -> model -> tools -> back.
function buildFlow(log, serverMap, model) {
  const steps = [
    { kind: "you", title: "You", detail: "your message enters the host" },
    { kind: "llm", title: "Gemini", detail: model },
  ];
  const calls = log.filter(
    (e) => e.direction === "send" && e.method === "tools/call"
  );
  if (calls.length === 0) {
    steps.push({
      kind: "note",
      title: "No MCP tools used",
      detail: "answered from the model's own knowledge",
    });
  } else {
    for (const e of calls) {
      const name = e.payload?.params?.name;
      const srv = serverMap[e.server] || {};
      const place = srv.where === "remote" ? srv.location : "local process";
      steps.push({
        kind: "tool",
        title: name,
        detail: `${e.server} · ${srv.source || ""} · ${place}`,
      });
    }
  }
  steps.push({ kind: "llm", title: "Gemini", detail: "composed the reply" });
  return steps;
}

function ToolsPopover({ servers }) {
  return (
    <span className="tools-pop" tabIndex={0}>
      <span className="topbar__meta">
        {servers.servers.length} servers · {servers.tool_count} tools ▾
      </span>
      <div className="tools-pop__panel" role="tooltip">
        {servers.servers.map((server) => (
          <div className="tools-pop__server" key={server.name}>
            <div className="tools-pop__srv-head">
              <span className="tools-pop__srv-name">{server.name}</span>
              <span className={`tools-pop__badge tools-pop__badge--${server.where}`}>
                {server.where}
              </span>
              <span className="tools-pop__srv-count">{server.tools.length}</span>
            </div>
            <div className="tools-pop__tools">
              {server.tools.map((tool) => (
                <code className="tools-pop__tool" key={tool}>{tool}</code>
              ))}
            </div>
          </div>
        ))}
      </div>
    </span>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [log, setLog] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [servers, setServers] = useState(null);
  const [usage, setUsage] = useState(null);
  const [flow, setFlow] = useState([]);
  const [model, setModelState] = useState("");
  const [showLog, setShowLog] = useState(true);
  const [theme, setTheme] = useState(
    () => localStorage.getItem("theme") || "dark"
  );
  const scrollRef = useRef(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  useEffect(() => {
    fetchServers()
      .then((s) => {
        setServers(s);
        setModelState(s.model);
      })
      .catch(() => setServers(null));
    fetchUsage().then(setUsage).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  const serverMap = Object.fromEntries((servers?.servers || []).map((s) => [s.name, s]));

  async function handleSend(text) {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: content }]);
    setLoading(true);
    try {
      const data = await sendMessage(content);
      setLog((prev) => [...prev, ...data.log]);
      setFlow(buildFlow(data.log, serverMap, model));
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: data.reply || "(no answer)", tools: toolsFromLog(data.log) },
      ]);
      fetchUsage().then(setUsage).catch(() => {});
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", text: `Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleModelChange(next) {
    setModelState(next);
    try {
      await apiSetModel(next);
    } catch {
      /* keep UI selection; backend will report on next call */
    }
  }

  async function handleReset() {
    await resetConversation().catch(() => {});
    setMessages([]);
    setFlow([]);
  }

  const connected = servers && servers.servers?.length > 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__logo" aria-hidden="true">
            <BrandMark />
          </span>
          <div>
            <h1>Sugar Mill MCP Chatbot</h1>
            <p className="topbar__sub">
              Console host + MCP servers over hand-written JSON-RPC
            </p>
          </div>
        </div>

        <div className="topbar__status">
          <span className={`dot ${connected ? "dot--on" : "dot--off"}`} />
          {servers ? (
            <ToolsPopover servers={servers} />
          ) : (
            <span className="topbar__meta">connecting…</span>
          )}

          {servers?.available_models && (
            <select
              className="model-select"
              value={model}
              onChange={(e) => handleModelChange(e.target.value)}
              aria-label="Model"
              title="LLM model"
            >
              {servers.available_models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          )}

          <button
            className="icon-btn"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
            title="Toggle light/dark"
          >
            {theme === "dark" ? <SunIcon /> : <MoonIcon />}
          </button>
          <button className="ghost-btn" onClick={() => setShowLog((v) => !v)}>
            {showLog ? "Hide log" : "Show log"}
          </button>
          <button className="ghost-btn" onClick={handleReset}>
            Reset
          </button>
        </div>
      </header>

      <main className={`layout ${showLog ? "" : "layout--nolog"}`}>
        <section className="chat">
          <div className="chat__scroll" ref={scrollRef}>
            {messages.length === 0 ? (
              <div className="empty">
                <h2>Talk to the sugar mill assistant</h2>
                <p>
                  It plans harvests by cane maturity, computes producer payments
                  by cane quality, and can drive the filesystem and git servers.
                </p>
                <div className="empty__examples">
                  {EXAMPLES.map((ex) => (
                    <button key={ex} className="example" onClick={() => handleSend(ex)}>
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => (
                <Message key={i} role={m.role} text={m.text} tools={m.tools} />
              ))
            )}
            {loading && (
              <div className="message message--bot">
                <div className="message__avatar" aria-hidden="true">
                  <BotIcon />
                </div>
                <div className="message__body">
                  <div className="typing">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}
          </div>
          <Composer
            value={input}
            onChange={setInput}
            onSend={() => handleSend()}
            disabled={loading}
          />
        </section>

        {showLog && <LogPanel log={log} flow={flow} usage={usage} />}
      </main>
    </div>
  );
}
