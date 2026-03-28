/**
 * Content script — injects "Launch This" button on supported coding platforms.
 * Runs on: Lovable, Replit, Cursor (web), Vercel, Netlify
 */

const SUPPORTED_PLATFORMS = [
  { host: "lovable.app", name: "Lovable" },
  { host: "replit.app", name: "Replit" },
  { host: "replit.com", name: "Replit" },
  { host: "vercel.app", name: "Vercel" },
  { host: "netlify.app", name: "Netlify" },
];

function getCurrentPlatform() {
  return SUPPORTED_PLATFORMS.find((p) => window.location.hostname.includes(p.host));
}

function injectLaunchButton() {
  const platform = getCurrentPlatform();
  if (!platform) return;

  // Don't inject twice
  if (document.getElementById("vibe-launcher-btn")) return;

  const button = document.createElement("button");
  button.id = "vibe-launcher-btn";
  button.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"/>
    </svg>
    Launch on X
  `;

  Object.assign(button.style, {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    zIndex: "99999",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "10px 16px",
    background: "linear-gradient(135deg, #f97316, #ea580c)",
    color: "white",
    border: "none",
    borderRadius: "12px",
    fontSize: "13px",
    fontWeight: "600",
    fontFamily: "system-ui, sans-serif",
    cursor: "pointer",
    boxShadow: "0 4px 20px rgba(249, 115, 22, 0.4)",
    transition: "all 0.2s ease",
  });

  button.onmouseenter = () => {
    button.style.transform = "translateY(-2px)";
    button.style.boxShadow = "0 6px 24px rgba(249, 115, 22, 0.5)";
  };

  button.onmouseleave = () => {
    button.style.transform = "translateY(0)";
    button.style.boxShadow = "0 4px 20px rgba(249, 115, 22, 0.4)";
  };

  button.onclick = handleLaunchClick;
  document.body.appendChild(button);
}

async function handleLaunchClick() {
  const btn = document.getElementById("vibe-launcher-btn") as HTMLButtonElement;
  if (btn) {
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite">
        <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-dasharray="60" stroke-dashoffset="60"/>
      </svg>
      Capturing...
    `;
    btn.disabled = true;
  }

  // Capture page data
  const pageData = await capturePageData();

  // Send to web app
  const vibleLauncherUrl = "http://localhost:3000";
  const params = new URLSearchParams();
  if (pageData.url) params.set("url", pageData.url);
  if (pageData.transcript) params.set("transcript", pageData.transcript.slice(0, 5000));

  // Open Vibe Launcher in new tab
  window.open(`${vibleLauncherUrl}?${params.toString()}`, "_blank");

  if (btn) {
    btn.innerHTML = `✓ Opened Vibe Launcher`;
    setTimeout(() => {
      btn.innerHTML = `Launch on X`;
      btn.disabled = false;
    }, 3000);
  }
}

async function capturePageData(): Promise<{
  url: string;
  title: string;
  transcript: string;
}> {
  const url = window.location.href;
  const title = document.title;

  // Try to capture chat transcript (Lovable, Replit have chat UIs)
  let transcript = "";

  // Generic: grab all visible text from chat-like elements
  const chatSelectors = [
    '[class*="chat"]',
    '[class*="message"]',
    '[class*="conversation"]',
    '[data-testid*="message"]',
  ];

  for (const selector of chatSelectors) {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 3) {
      const texts = Array.from(elements)
        .map((el) => el.textContent?.trim())
        .filter(Boolean)
        .slice(-50); // last 50 messages
      transcript = texts.join("\n");
      break;
    }
  }

  return { url, title, transcript };
}

// Inject button when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", injectLaunchButton);
} else {
  injectLaunchButton();
}

// Re-inject on navigation (SPAs)
const observer = new MutationObserver(() => {
  if (!document.getElementById("vibe-launcher-btn")) {
    injectLaunchButton();
  }
});

observer.observe(document.body, { childList: true, subtree: true });
