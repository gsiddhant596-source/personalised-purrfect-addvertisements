const API_BASE = "http://127.0.0.1:8000";

const consentButton = document.getElementById("consentButton");
const analyseButton = document.getElementById("analyseButton");
const stopButton = document.getElementById("stopButton");
const statusBox = document.getElementById("status");
const adsBox = document.getElementById("ads");

function setStatus(message) {
  statusBox.textContent = message;
}

// Fallback branded banner if an image fails to load
function createAdPlaceholder(adName = "AdSense AI") {
  const placeholder = document.createElement("div");
  placeholder.className = "ad-image-placeholder";

  const icon = document.createElement("div");
  icon.className = "placeholder-icon";
  icon.textContent = "✦";

  const brand = document.createElement("div");
  brand.className = "placeholder-brand";
  brand.textContent = adName;

  placeholder.append(icon, brand);
  return placeholder;
}

function showAds(ads) {
  adsBox.replaceChildren();

  if (!ads.length) {
    setStatus("No matching campaigns found in inventory.");
    return;
  }

  for (const ad of ads) {
    const card = document.createElement("article");
    card.className = "ad-card";

    // 1. Creative banner image (Generated locally by SD-Turbo)
    const imageArea = document.createElement("div");
    if (ad.image_url) {
      const image = document.createElement("img");
      image.alt = ad.name || "Advertisement";
      image.referrerPolicy = "no-referrer";
      image.loading = "eager";
      image.src = ad.image_url;
      image.onerror = () => {
        imageArea.replaceChildren(createAdPlaceholder(ad.name));
      };
      imageArea.appendChild(image);
    } else {
      imageArea.appendChild(createAdPlaceholder(ad.name));
    }
    card.appendChild(imageArea);

    // 2. Card body & details
    const content = document.createElement("div");
    content.className = "ad-content";

    // Intent match percentage
    const matchPercent = Math.max(5, Math.round((ad.similarity || 0.8) * 100));
    const label = document.createElement("div");
    label.className = "sponsored";
    label.textContent = `✦ AI Matched Intent (${matchPercent}%)`;

    // Title and price tag
    const title = document.createElement("h2");
    title.style.display = "flex";
    title.style.justifyContent = "space-between";
    title.style.alignItems = "center";
    title.style.gap = "8px";

    const titleText = document.createElement("span");
    titleText.textContent = ad.name || "Sponsored Recommendation";
    title.appendChild(titleText);

    if (ad.price) {
      const priceTag = document.createElement("span");
      priceTag.textContent = ad.price;
      priceTag.style.fontSize = "12px";
      priceTag.style.color = "#7654e8";
      priceTag.style.fontWeight = "700";
      title.appendChild(priceTag);
    }

    // Description
    const description = document.createElement("p");
    description.textContent = ad.description || "";

    content.append(label, title, description);

    // Outbound link
    if (ad.destination_url) {
      const link = document.createElement("a");
      link.href = ad.destination_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Learn more ↗";
      content.appendChild(link);
    }

    card.appendChild(content);
    adsBox.appendChild(card);
  }

  setStatus(`${ads.length} relevant ad${ads.length === 1 ? "" : "s"} matched & rendered.`);
}

async function readSession() {
  return chrome.storage.session.get(["consent"]);
}

async function refreshControls() {
  const data = await readSession();
  const allowed = data.consent === true;

  consentButton.hidden = allowed;
  analyseButton.disabled = !allowed;
  stopButton.hidden = !allowed;
}

// Enable consent for the browsing session
consentButton.addEventListener("click", async () => {
  await chrome.storage.session.set({ consent: true });
  adsBox.replaceChildren();
  await refreshControls();
  setStatus("Consent active. Click 'Find relevant ads' to inspect page.");
});

// Disable consent and wipe rendered ads
stopButton.addEventListener("click", async () => {
  await chrome.storage.session.set({ consent: false });
  adsBox.replaceChildren();
  await refreshControls();
  setStatus("Consent turned off. No ads will be displayed.");
});

// Scrape active tab and fetch semantic recommendation
analyseButton.addEventListener("click", async () => {
  analyseButton.disabled = true;
  adsBox.replaceChildren();
  setStatus("Extracting active tab content...");

  try {
    const session = await readSession();
    if (session.consent !== true) {
      setStatus("Please grant session permission first.");
      return;
    }

    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    if (!tab || !tab.id || !/^https?:/.test(tab.url || "")) {
      setStatus("Cannot scan internal pages. Open a regular website first.");
      return;
    }

    // Read visible page text safely
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({
        title: document.title || "",
        text: (document.body?.innerText || "").slice(0, 8000)
      })
    });

    const page = results?.[0]?.result;
    if (!page || !page.text.trim()) {
      setStatus("No readable text found on this page.");
      return;
    }

    const pageContent = `${page.title}\n${page.text}`.slice(0, 6000);
    setStatus("Computing embeddings & running SD-Turbo on GPU...");

    const endpoint = new URL(`${API_BASE}/recommend`);
    endpoint.searchParams.set("content", pageContent);

    const response = await fetch(endpoint.toString());
    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const data = await response.json();
    const recommendations = Array.isArray(data) ? data : data.recommendations;

    if (!Array.isArray(recommendations) || recommendations.length === 0) {
      setStatus("No matching ads found in inventory.");
      return;
    }

    showAds(recommendations);
  } catch (error) {
    console.error("AdSense AI error:", error);
    if (error.message?.includes("Failed to fetch")) {
      setStatus("Cannot reach FastAPI. Verify 'python main.py' is running on port 8000.");
    } else {
      setStatus(`Error: ${error.message || "Failed to analyze page."}`);
    }
  } finally {
    analyseButton.disabled = false;
  }
});

// Initialize extension popup controls
refreshControls().then(() => {
  readSession().then(data => {
    if (data.consent === true) {
      setStatus("Ready. Click 'Find relevant ads' to match page content.");
    } else {
      setStatus("Consent is required before analysis.");
    }
  });
});