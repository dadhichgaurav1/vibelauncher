/**
 * Background service worker.
 * Dual role:
 * 1. Maintains WebSocket connection to backend for browser-use commands
 * 2. Injects "Launch This" button logic and manages side panel
 */

const BACKEND_WS = "ws://localhost:8000";

let backendWs: WebSocket | null = null;
let currentLaunchId: string | null = null;

// ─── Backend WebSocket ────────────────────────────────────────────────────────

function connectToBackend(launchId: string) {
  currentLaunchId = launchId;

  if (backendWs) {
    backendWs.close();
  }

  backendWs = new WebSocket(`${BACKEND_WS}/ws/extension/${launchId}`);

  backendWs.onopen = () => {
    console.log("[VibeLauncher] Extension connected to backend");
  };

  backendWs.onmessage = async (event) => {
    const msg = JSON.parse(event.data);
    await handleBrowserCommand(msg);
  };

  backendWs.onclose = () => {
    console.log("[VibeLauncher] Extension WebSocket closed");
    backendWs = null;
  };
}

// ─── Browser-use command handler ──────────────────────────────────────────────

async function handleBrowserCommand(command: {
  action: string;
  url?: string;
  query?: string;
}) {
  let result: unknown = null;

  switch (command.action) {
    case "fetch_page":
      result = await fetchPageContent(command.url!);
      break;

    case "search_twitter":
      result = await searchTwitter(command.query!);
      break;

    case "get_page":
      result = await fetchPageContent(command.url!);
      break;
  }

  if (backendWs && backendWs.readyState === WebSocket.OPEN) {
    backendWs.send(
      JSON.stringify({
        type: "browser_result",
        data: result,
      })
    );
  }
}

async function fetchPageContent(url: string): Promise<{ content: string }> {
  return new Promise((resolve) => {
    chrome.tabs.create({ url, active: false }, (tab) => {
      const tabId = tab.id!;

      // Wait for tab to load then extract content
      chrome.tabs.onUpdated.addListener(function listener(updatedTabId, info) {
        if (updatedTabId === tabId && info.status === "complete") {
          chrome.tabs.onUpdated.removeListener(listener);

          chrome.scripting.executeScript(
            {
              target: { tabId },
              func: () => document.body?.innerText ?? "",
            },
            (results) => {
              const content = results?.[0]?.result ?? "";
              chrome.tabs.remove(tabId);
              resolve({ content: content.slice(0, 10000) });
            }
          );
        }
      });
    });
  });
}

async function searchTwitter(
  query: string
): Promise<{ tweets: Array<{ text: string; author: string; likes: number }> }> {
  return new Promise((resolve) => {
    const searchUrl = `https://twitter.com/search?q=${encodeURIComponent(query)}&f=top`;

    chrome.tabs.create({ url: searchUrl, active: false }, (tab) => {
      const tabId = tab.id!;

      chrome.tabs.onUpdated.addListener(function listener(updatedTabId, info) {
        if (updatedTabId === tabId && info.status === "complete") {
          chrome.tabs.onUpdated.removeListener(listener);

          // Wait a bit for JS to render
          setTimeout(() => {
            chrome.scripting.executeScript(
              {
                target: { tabId },
                func: extractTwitterSearchResults,
              },
              (results) => {
                const tweets = results?.[0]?.result ?? [];
                chrome.tabs.remove(tabId);
                resolve({ tweets });
              }
            );
          }, 3000);
        }
      });
    });
  });
}

function extractTwitterSearchResults(): Array<{
  text: string;
  author: string;
  likes: number;
}> {
  const tweets: Array<{ text: string; author: string; likes: number }> = [];

  // Twitter's DOM selectors for tweet content
  const tweetElements = document.querySelectorAll('[data-testid="tweet"]');

  tweetElements.forEach((el) => {
    const textEl = el.querySelector('[data-testid="tweetText"]');
    const authorEl = el.querySelector('[data-testid="User-Name"]');
    const likesEl = el.querySelector('[data-testid="like"] span');

    if (textEl) {
      tweets.push({
        text: textEl.textContent ?? "",
        author: authorEl?.textContent ?? "",
        likes: parseInt(likesEl?.textContent?.replace(/[^0-9]/g, "") ?? "0"),
      });
    }
  });

  return tweets.slice(0, 15);
}

// ─── Message handling from popup/content scripts ──────────────────────────────

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "CONNECT_LAUNCH") {
    connectToBackend(msg.launchId);
    sendResponse({ ok: true });
  }

  if (msg.type === "GET_PAGE_CONTENT") {
    // Content script asking background to capture current tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (!tab?.id) return sendResponse({ content: "" });

      chrome.scripting.executeScript(
        {
          target: { tabId: tab.id },
          func: () => ({
            url: window.location.href,
            title: document.title,
            content: document.body?.innerText?.slice(0, 15000) ?? "",
          }),
        },
        (results) => {
          sendResponse(results?.[0]?.result ?? { content: "" });
        }
      );
    });
    return true; // async
  }

  if (msg.type === "OPEN_SIDE_PANEL") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.windowId) {
        (chrome.sidePanel as unknown as { open: (opts: { windowId: number }) => void }).open({
          windowId: tabs[0].windowId,
        });
      }
    });
    sendResponse({ ok: true });
  }
});
