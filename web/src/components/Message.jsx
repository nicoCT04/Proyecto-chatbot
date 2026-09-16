import { BotIcon, UserIcon } from "./icons.jsx";

function renderInline(text) {
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  const parts = text.split(pattern);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function renderText(text) {
  return text.split("\n").map((line, i) => (
    <span key={i} className="line">
      {renderInline(line)}
    </span>
  ));
}

export default function Message({ role, text, tools = [] }) {
  return (
    <div className={`message message--${role}`}>
      <div className="message__avatar" aria-hidden="true">
        {role === "user" ? <UserIcon /> : <BotIcon />}
      </div>
      <div className="message__body">
        {tools.length > 0 && (
          <div className="message__tools">
            {tools.map((name, i) => (
              <span className="tool-chip" key={`${name}-${i}`}>
                ⚙ {name}
              </span>
            ))}
          </div>
        )}
        <div className="message__text">{renderText(text)}</div>
      </div>
    </div>
  );
}
