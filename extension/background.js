
/* AdSense AI background service worker.
   Ads are displayed only inside popup.html. */

chrome.runtime.onInstalled.addListener(() => {
  console.log("AdSense AI extension installed.");
});

// Record navigation for debugging only.
// Do not read webpage content or inject ads here.
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab?.url) {
    console.log("AdSense AI: Page loaded:", tab.url);
  }
});
