import { useEffect, useRef, useState } from "react";
import Message from "./components/Message.jsx";
import LogPanel from "./components/LogPanel.jsx";
import Composer from "./components/Composer.jsx";
import { fetchServers, resetConversation, sendMessage } from "./api.js";

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

export default function App() {
  const [messages, setMessages] = useState([]);
  const [log, setLog] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [servers, setServers] = useState(null);
  const [showLog, setShowLog] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    fetchServers().then(setServers).catch(() => setServers(null));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, loading]);

  async function handleSend(text) {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text: content }]);
    setLoading(true);
    try {
      const data = await sendMessage(content);
      setLog((prev) => [...prev, ...data.log]);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: data.reply || "(no answer)", tools: toolsFromLog(data.log) },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "error", text: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    await resetConversation().catch(() => {});
    setMessages([]);
  }

  const connected = servers && servers.servers?.length > 0;

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__logo" aria-hidden="true">🍬</span>
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
            <span>
              {servers.servers.length} servers · {servers.tool_count} tools ·{" "}
              <code>{servers.model}</code>
            </span>
          ) : (
            <span>connecting…</span>
          )}
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
                    <button
                      key={ex}
                      className="example"
                      onClick={() => handleSend(ex)}
                    >
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
                <div className="message__avatar" aria-hidden="true">🍬</div>
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

        {showLog && <LogPanel log={log} />}
      </main>
    </div>
  );
}
