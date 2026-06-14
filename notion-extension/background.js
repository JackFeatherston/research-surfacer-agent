// Runs the /scan request outside the page so Notion's CSP doesn't block it.

const API_URL = "http://localhost:8000";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  scan(message.text).then(sendResponse);
  return true; // keep the channel open for the async response
});

async function scan(text) {
  const resp = await fetch(`${API_URL}/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return { ok: resp.ok, status: resp.status, data: resp.ok ? await resp.json() : null };
}
