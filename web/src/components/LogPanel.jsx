// Live view of every JSON-RPC message exchanged with the MCP servers
// (feature 3 of the project, made visible). Each row can be expanded to see
// the full payload.

import { useState } from "react";

const KIND_LABEL = {
  request: "request",
  response: "response",
  notification: "notify",
  error: "error",
};

function LogRow({ entry }) {
  const [open, setOpen] = useState(false);
  const outbound = entry.direction === "send";
  const label = entry.method || `id=${entry.id}`;
  return (
    <li className={`log-row log-row--${entry.kind}`}>
      <button
        className="log-row__head"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="log-row__time">{entry.time.split("T")[1]}</span>
        <span className="log-row__server">{entry.server}</span>
        <span className={`log-row__flow ${outbound ? "out" : "in"}`}>
          {outbound ? "▲ host→srv" : "▼ srv→host"}
        </span>
        <span className={`log-row__kind kind--${entry.kind}`}>
          {KIND_LABEL[entry.kind] || entry.kind}
        </span>
        <span className="log-row__method">{label}</span>
      </button>
      {open && (
        <pre className="log-row__payload">
          {JSON.stringify(entry.payload, null, 2)}
        </pre>
      )}
    </li>
  );
}

export default function LogPanel({ log }) {
  return (
    <aside className="logpanel" aria-label="MCP JSON-RPC traffic">
      <header className="logpanel__head">
        <h2>MCP traffic</h2>
        <span className="logpanel__count">{log.length} messages</span>
      </header>
      {log.length === 0 ? (
        <p className="logpanel__empty">
          No JSON-RPC messages yet. Ask something that uses a tool.
        </p>
      ) : (
        <ul className="logpanel__list">
          {log.map((entry, i) => (
            <LogRow entry={entry} key={i} />
          ))}
        </ul>
      )}
    </aside>
  );
}
