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

function DataFlow({ flow }) {
  if (!flow || flow.length === 0) return null;
  return (
    <div className="flow">
      <h3 className="flow__title">Data flow · last turn</h3>
      <ol className="flow__list">
        {flow.map((step, i) => (
          <li key={i} className={`flow__step flow__step--${step.kind}`}>
            <span className="flow__dot" />
            <div className="flow__body">
              <span className="flow__name">{step.title}</span>
              <span className="flow__detail">{step.detail}</span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

function UsageFooter({ usage }) {
  if (!usage) return null;
  const u = usage.usage || {};
  const limits = usage.limits || {};
  return (
    <div className="usage">
      <div className="usage__head">
        <span>API usage · this session</span>
        <code>{usage.model}</code>
      </div>
      <div className="usage__grid">
        <div><b>{u.requests ?? 0}</b><span>requests</span></div>
        <div><b>{u.prompt_tokens ?? 0}</b><span>in tokens</span></div>
        <div><b>{u.output_tokens ?? 0}</b><span>out tokens</span></div>
        <div><b>{u.total_tokens ?? 0}</b><span>total tokens</span></div>
      </div>
      {(limits.rpm || limits.rpd) && (
        <p className="usage__limits">
          Free-tier reference: {limits.rpm ?? "—"} req/min · {limits.rpd ?? "—"} req/day
          <span className="usage__note"> (Google does not expose live remaining quota)</span>
        </p>
      )}
    </div>
  );
}

export default function LogPanel({ log, flow, usage }) {
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
      <DataFlow flow={flow} />
      <UsageFooter usage={usage} />
    </aside>
  );
}
