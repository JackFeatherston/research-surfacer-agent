// Research Radar for Notion — highlight text, click the icon, read related research.

const STANCE_BADGE = {
  supports: "🟢 Supports your assumption",
  contradicts: "🔴 Contradicts your assumption",
  neutral: "⚪ Neutral / adds nuance",
};

let icon = null;
let popup = null;
let selectedText = "";
let selectedRect = null;

// Show or move the floating icon whenever the user finishes a selection.
document.addEventListener("mouseup", (event) => {
  if (icon && icon.contains(event.target)) return;
  if (popup && popup.contains(event.target)) return;

  const selection = window.getSelection();
  const text = selection.toString().trim();

  if (!text) {
    removeIcon();
    removePopup();
    return;
  }

  selectedText = text;
  selectedRect = selection.getRangeAt(0).getBoundingClientRect();
  showIcon(selectedRect);
});

// research icon button
function showIcon(rect) {
  if (!icon) {
    icon = document.createElement("button");
    icon.className = "rr-icon";
    icon.textContent = "🔍";
    icon.title = "Scan with Research Radar";
    icon.addEventListener("click", scan);
    document.body.appendChild(icon);
  }
  icon.style.top = `${rect.top - 40}px`;
  icon.style.left = `${rect.right - 16}px`;
}

function removeIcon() {
  if (icon) icon.remove();
  icon = null;
}

function removePopup() {
  if (popup) popup.remove();
  popup = null;
}

function openPopup(rect) {
  removePopup();
  popup = document.createElement("div");
  popup.className = "rr-popup";
  popup.style.top = `${rect.bottom + 8}px`;
  popup.style.left = `${Math.min(rect.left, window.innerWidth - 380)}px`;
  popup.innerHTML = `
    <button class="rr-close" title="Close">×</button>
    <div class="rr-header">Surfaced Insights</div>
    <div class="rr-body"><div class="rr-spinner">Scanning past research…</div></div>`;
  popup.querySelector(".rr-close").addEventListener("click", removePopup);
  document.body.appendChild(popup);
  return popup.querySelector(".rr-body");
}

async function scan() {
  const body = openPopup(selectedRect);
  removeIcon();

  const result = await chrome.runtime.sendMessage({ text: selectedText });
  if (!result.ok) {
    body.innerHTML = `<div class="rr-error">API error ${result.status}</div>`;
    return;
  }
  render(body, result.data);
}

// If the highlighted text has no relevance. 
function render(body, digest) {
  if (digest.gap) {
    body.innerHTML = `
      <div class="rr-gap-title">Not enough information.</div>
      <div class="rr-gap-text">${escapeHtml(digest.suggestion)}</div>`;
    return;
  }

  body.innerHTML = digest.matches.map(cardHtml).join("");
}

function cardHtml(m) {
  const flags = m.flags.map((f) => `<div class="rr-flag">⚠️ ${escapeHtml(f)}</div>`).join("");
  return `
    <div class="rr-card">
      <a class="rr-title" href="${m.url}" target="_blank" rel="noopener">${escapeHtml(m.title)}</a>
      <div class="rr-meta">${escapeHtml(m.team)} · ${m.date} · relevance ${m.relevance}/10</div>
      <div class="rr-summary">${escapeHtml(m.relevance_summary)}</div>
      <div class="rr-stance rr-${m.stance}">${STANCE_BADGE[m.stance]} — ${escapeHtml(m.stance_note)}</div>
      ${flags}
    </div>`;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
