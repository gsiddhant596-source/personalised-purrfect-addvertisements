// content.js

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "inject_ads") {
    renderAds(request.ads);
  }
});

function renderAds(ads) {
  // Prevent duplicate ad injection
  if (document.getElementById("adsense-ai-banner")) return;

  const adContainer = document.createElement("div");
  adContainer.id = "adsense-ai-banner";
  adContainer.innerHTML = `
    <div style="
      position: fixed; bottom: 20px; right: 20px; z-index: 999999;
      background: linear-gradient(135deg, #1e293b, #0f172a);
      color: #fff; padding: 16px; border-radius: 12px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.4); font-family: system-ui, sans-serif;
      border: 1px solid rgba(255,255,255,0.1); max-width: 320px;
    ">
      <span style="font-size: 10px; background: #3b82f6; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">AdSenseAI Match</span>
      <h4 style="margin: 8px 0 4px 0; font-size: 15px; color: #f8fafc;">${ads?.title || "Sponsored Recommendation"}</h4>
      <p style="margin: 0 0 12px 0; font-size: 12px; color: #94a3b8;">${ads?.description || "Tailored perfectly to your current search intent."}</p>
      <a href="${ads?.url || '#'}" target="_blank" style="
        display: inline-block; background: #2563eb; color: white; padding: 6px 12px;
        border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold;
      ">Learn More</a>
      <button id="close-ai-ad" style="
        background: transparent; border: none; color: #94a3b8; float: right; cursor: pointer; font-size: 14px;
      ">✕</button>
    </div>
  `;

  document.body.appendChild(adContainer);

  document.getElementById("close-ai-ad").onclick = () => {
    adContainer.remove();
  };
}