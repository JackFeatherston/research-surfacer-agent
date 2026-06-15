// Research Radar for Notion — highlight text, click the icon, read related research.

const STANCE_BADGE = {
  supports: "🟢 This study supports this claim.",
  contradicts: "🔴 This study contradicts this claim.",
  neutral: "⚪ This study is neutral and/or adds nuance to this claim.",
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
    icon.title = "Surface res";
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

// Popup body
function openPopup(rect) {
  removePopup();
  popup = document.createElement("div");
  popup.className = "rr-popup";

  const margin = 12;
  const spaceBelow = window.innerHeight - rect.bottom - margin;
  const spaceAbove = rect.top - margin;
  let top, maxHeight;
  if (spaceBelow >= 180 || spaceBelow >= spaceAbove) {
    top = rect.bottom + 8;
    maxHeight = spaceBelow - 8;
  } else {
    maxHeight = spaceAbove - 8;
    top = rect.top - maxHeight - 8;
  }

  popup.style.top = `${top}px`;
  popup.style.left = `${Math.min(rect.left, window.innerWidth - 380)}px`;
  popup.style.maxHeight = `${Math.max(maxHeight, 180)}px`;
  popup.innerHTML = `
    <div class="rr-popup-header">
      <span class="rr-header">Surfaced Insights</span>
      <button class="rr-close" title="Close">×</button>
    </div>
    <div class="rr-body"><div class="rr-spinner">Scanning past research…</div></div>`;
  popup.querySelector(".rr-close").addEventListener("click", removePopup);
  document.body.appendChild(popup);
  makeDraggable(popup);
  return popup.querySelector(".rr-body");
}

// Draggable functionality for insights popup
function makeDraggable(el) {
  let startX, startY, startLeft, startTop, dragging = false;

  el.addEventListener("mousedown", (e) => {
    if (e.target.closest("a, button")) return;
    dragging = true;
    startX = e.clientX;
    startY = e.clientY;
    startLeft = parseInt(el.style.left, 10);
    startTop = parseInt(el.style.top, 10);
    e.preventDefault();
  });

  document.addEventListener("mousemove", (e) => {
    if (!dragging) return;
    el.style.left = `${startLeft + e.clientX - startX}px`;
    el.style.top = `${startTop + e.clientY - startY}px`;
  });

  document.addEventListener("mouseup", () => { dragging = false; });
}

// trigger for pipeline
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

// Either state that the highlighted text has no relevance or display the matched results.
function render(body, digest) {
  if (digest.gap) {
    body.innerHTML = `
      <div class="rr-gap-title">Not enough information.</div>
      <div class="rr-gap-text">${escapeHtml(digest.suggestion)}</div>`;
    return;
  }

  body.innerHTML = digest.matches.map(cardHtml).join("");
}

// Surfaced source with title, quote, and LLM decision  
function cardHtml(m) {
  const flags = m.flags.map((f) => `<div class="rr-flag">⚠️ ${escapeHtml(f)}</div>`).join("");
  return `
    <div class="rr-card">
      <a class="rr-title" href="${m.url}" target="_blank" rel="noopener">${escapeHtml(m.title)}</a>
      <div class="rr-meta">${escapeHtml(m.team)} · ${m.date} · relevance ${m.relevance}/10</div>
      <div class="rr-summary">${escapeHtml(m.relevance_summary)}</div>
      ${m.quote ? `<blockquote class="rr-quote">${escapeHtml(m.quote.text)}</blockquote>` : ""}
      <div class="rr-stance rr-${m.stance}">${STANCE_BADGE[m.stance]} — ${escapeHtml(m.stance_note)}</div>
      ${flags}
    </div>`;
}

// helper function
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
