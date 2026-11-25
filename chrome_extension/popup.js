const API_BASE = "http://localhost:8000";
let currentPackage = null;
let detectedPlatform = "facebook";

function detectPlatformFromUrl(url = "") {
  const u = url.toLowerCase();
  if (u.includes("kijiji.ca")) return "kijiji";
  if (u.includes("zumper.com")) return "zumper";
  if (u.includes("rentals.ca")) return "rentals_ca";
  return "facebook";
}

function getPayloadForPlatform(pkg, plat) {
  if (!pkg) return null;
  if (plat === "facebook") return Object.assign({ unit_id: pkg.unit_id }, pkg.facebook_marketplace);
  return Object.assign({ unit_id: pkg.unit_id }, pkg[plat] || pkg.facebook_marketplace);
}

async function loadPackage(unitId) {
  const statusEl = document.getElementById("statusMsg");
  document.getElementById("zipBtn").href = `${API_BASE}/api/units/${unitId}/photos.zip`;
  try {
    const res = await fetch(`${API_BASE}/api/units/${unitId}/package`);
    const json = await res.json();
    if (json.success) {
      currentPackage = json.package;
      statusEl.textContent = `Loaded ${currentPackage.unit_name}`;
    }
  } catch (e) {
    statusEl.textContent = "Start server.py on localhost:8000";
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const unitSel = document.getElementById("unitSelect");
  const saved = await chrome.storage.local.get(["selectedUnit"]);
  if (saved.selectedUnit) unitSel.value = saved.selectedUnit;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url) {
    detectedPlatform = detectPlatformFromUrl(tab.url);
    document.getElementById("siteBadge").textContent = detectedPlatform.toUpperCase();
  }

  await loadPackage(unitSel.value);

  unitSel.addEventListener("change", async () => {
    await chrome.storage.local.set({ selectedUnit: unitSel.value });
    await loadPackage(unitSel.value);
  });

  document.getElementById("autofillBtn").addEventListener("click", async () => {
    const payload = getPayloadForPlatform(currentPackage, detectedPlatform);
    const statusEl = document.getElementById("statusMsg");
    if (!payload || !tab?.id) return;

    try {
      await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: (pl, plat) => window.__kentStAutoFill(pl, plat),
        args: [payload, detectedPlatform]
      });
      const count = results?.[0]?.result || 0;
      statusEl.textContent = count > 0 ? `✔ Auto-filled ${count} field(s) on this step!` : "No matching fields visible on this step — use Copy buttons.";
    } catch (e) {
      statusEl.textContent = "Open Facebook, Kijiji, Zumper, or Rentals.ca first.";
    }
  });

  const copyText = async (txt, label) => {
    if (!txt) return;
    await navigator.clipboard.writeText(String(txt));
    document.getElementById("statusMsg").textContent = `✔ Copied ${label}!`;
  };

  document.getElementById("copyTitleBtn").addEventListener("click", () => {
    const pl = getPayloadForPlatform(currentPackage, detectedPlatform);
    copyText(pl?.title, "Title");
  });
  document.getElementById("copyPriceBtn").addEventListener("click", () => {
    const pl = getPayloadForPlatform(currentPackage, detectedPlatform);
    copyText(pl?.price, "Price");
  });
  document.getElementById("copyDescBtn").addEventListener("click", () => {
    const pl = getPayloadForPlatform(currentPackage, detectedPlatform);
    copyText(pl?.description, "Description");
  });
  document.getElementById("copyVideoBtn").addEventListener("click", () => {
    const pl = getPayloadForPlatform(currentPackage, detectedPlatform);
    copyText(pl?.virtual_tour_url || pl?.youtube_video_url || pl?.video_link, "YouTube URL");
  });
  document.getElementById("copyAddrBtn").addEventListener("click", () => {
    copyText("315 Kent Street, Whitby, ON", "Address");
  });

  document.getElementById("markPostedBtn").addEventListener("click", async () => {
    try {
      await fetch(`${API_BASE}/api/postings/mark-posted`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          unit_id: unitSel.value,
          platform: detectedPlatform,
          external_url: tab?.url || null
        })
      });
      document.getElementById("statusMsg").textContent = `🎉 Marked ${detectedPlatform.toUpperCase()} as Posted!`;
    } catch (e) {
      document.getElementById("statusMsg").textContent = "Could not reach localhost:8000";
    }
  });
});
