function setProgress(percent, color) {
  const circle = document.querySelector(".progress-ring__circle");
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;
  circle.style.strokeDashoffset = offset;
  circle.style.stroke = color;
}

async function animateScore(targetScore, color) {
  const scoreNum = document.getElementById("score-number");
  let current = 0;
  const step = Math.ceil(targetScore / 40);

  const timer = setInterval(() => {
    current += step;
    if (current >= targetScore) {
      current = targetScore;
      clearInterval(timer);
    }
    scoreNum.textContent = `${current}%`;
    setProgress(current, color);
  }, 20);
}

async function runScan() {
  const resultText = document.getElementById("result-text");
  const desc = document.getElementById("desc");
  const scoreNum = document.getElementById("score-number");
  const circle = document.getElementById("circle");
  const urlText = document.getElementById("url-text");
  const body = document.body;

  // Reset UI
  body.className = "";
  circle.classList.add("pulsing");
  resultText.textContent = "Analyzing...";
  desc.textContent = "Please wait while we scan this site.";
  scoreNum.textContent = "--%";
  setProgress(0, "#00aaff");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab?.url;
    urlText.textContent = url || "No active URL found";

    if (!url || url.startsWith("chrome://")) {
      resultText.textContent = "Unavailable";
      desc.textContent = "Cannot analyze internal browser pages.";
      circle.classList.remove("pulsing");
      return;
    }

    // API call with proper URL encoding
    const response = await fetch(`http://127.0.0.1:5000/api?url=${encodeURIComponent(url)}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) throw new Error("Server returned error");

    const data = await response.json();
    circle.classList.remove("pulsing");

    if (data && data.Trust_Score !== undefined) {
      const score = Math.round(data.Trust_Score);
      const result = data.Result?.toLowerCase() || "";
      let color = "#00aaff";
      let bgClass = "";
      let message = "";
      let description = "";

      // Flexible keyword matching for different states
      if (result.includes("safe") || result.includes("legit")) {
        color = "#00b35a"; // green
        bgClass = "legit-bg";
        message = "Legitimate";
        description = "This site appears safe to use.";
      } else if (result.includes("caution") || result.includes("suspicious") || result.includes("warning")) {
        color = "#ffb400"; // yellow
        bgClass = "caution-bg";
        message = "Caution";
        description = "Proceed carefully — mixed safety indicators.";
      } else if (result.includes("unsafe") || result.includes("malicious") || result.includes("phish")) {
        color = "#dc3545"; // red
        bgClass = "phish-bg";
        message = "Phishing";
        description = "⚠ Dangerous site — avoid entering sensitive info.";
      } else {
        color = "#00aaff";
        message = "Unknown";
        description = "Could not determine website safety.";
      }

      // Animate score and update UI
      await animateScore(score, color);
      resultText.textContent = message;
      resultText.style.color = color;
      desc.textContent = description;
      body.className = bgClass;
    } else {
      throw new Error("Invalid API response");
    }
  } catch (err) {
    console.error("Error:", err);
    resultText.textContent = "Server Unavailable";
    desc.textContent = "Ensure backend is running on 127.0.0.1:5000.";
    circle.classList.remove("pulsing");
  }
}

// Auto-scan on load + manual
document.addEventListener("DOMContentLoaded", runScan);
document.getElementById("scan-btn").addEventListener("click", runScan);