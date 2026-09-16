async function json(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail || detail;
    } catch {
      detail = response.statusText;
    }
    throw new Error(detail);
  }
  return response.json();
}

export function sendMessage(message) {
  return json("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function fetchServers() {
  return json("/api/servers");
}

export function fetchLog() {
  return json("/api/log");
}

export function fetchUsage() {
  return json("/api/usage");
}

export function setModel(model) {
  return json("/api/model", {
    method: "POST",
    body: JSON.stringify({ model }),
  });
}

export function resetConversation() {
  return json("/api/reset", { method: "POST" });
}
