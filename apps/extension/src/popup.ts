const VIBE_LAUNCHER_URL = "http://localhost:3000";

async function init() {
  const launchBtn = document.getElementById("launchBtn") as HTMLButtonElement;
  const platformName = document.getElementById("platformName")!;
  const statusDot = document.getElementById("statusDot")!;

  // Get current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab?.url ?? "";

  // Detect platform
  const platforms = [
    { host: "lovable.app", name: "Lovable" },
    { host: "replit.app", name: "Replit" },
    { host: "replit.com", name: "Replit" },
    { host: "vercel.app", name: "Vercel" },
    { host: "netlify.app", name: "Netlify" },
    { host: "cursor.sh", name: "Cursor" },
  ];

  const platform = platforms.find((p) => url.includes(p.host));
  platformName.textContent = platform ? platform.name : "Any page";

  // Check if X is connected
  const stored = await chrome.storage.local.get("x_connected");
  if (stored.x_connected) {
    statusDot.classList.add("connected");
  }

  launchBtn.onclick = async () => {
    launchBtn.disabled = true;
    launchBtn.textContent = "Capturing...";

    // Get page content from content script
    let pageData = { url, title: tab?.title ?? "", transcript: "" };

    if (tab?.id) {
      try {
        const result = await chrome.tabs.sendMessage(tab.id, {
          type: "GET_PAGE_CONTENT",
        });
        if (result) pageData = { ...pageData, ...result };
      } catch {
        // Content script not injected — use tab URL only
      }
    }

    // Build URL params
    const params = new URLSearchParams();
    if (pageData.url) params.set("url", pageData.url);
    if (pageData.transcript) params.set("transcript", pageData.transcript.slice(0, 3000));

    // Open Vibe Launcher
    chrome.tabs.create({ url: `${VIBE_LAUNCHER_URL}?${params.toString()}` });
    window.close();
  };
}

init();
