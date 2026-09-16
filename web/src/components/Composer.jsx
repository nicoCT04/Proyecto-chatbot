import { useRef } from "react";

export default function Composer({ value, onChange, onSend, disabled }) {
  const textareaRef = useRef(null);

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!disabled && value.trim()) onSend();
    }
  }

  return (
    <div className="composer">
      <textarea
        ref={textareaRef}
        className="composer__input"
        placeholder="Ask about fields, harvest plans, payments… (Shift+Enter for a new line)"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        aria-label="Message"
      />
      <button
        className="composer__send"
        onClick={onSend}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
      >
        {disabled ? "…" : "Send"}
      </button>
    </div>
  );
}
