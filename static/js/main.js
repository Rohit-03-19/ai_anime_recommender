/**
 * AI ANIME EXPLORER - FRONTEND ENGINE
 * Logic for handling API calls, DOM manipulation, and UI state.
 */

// 1. PAGE ROUTING LOGIC
function switchPage(pageId) {
  const recommendSection = document.getElementById("recommend-section");
  const placeholderSection = document.getElementById("placeholder-section");
  const title = document.getElementById("placeholder-title");

  // Reset Visibility
  recommendSection.classList.add("hidden");
  placeholderSection.classList.add("hidden");

  // Update Navigation Active State (FIXED SCOPE)
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.remove("active");
    if (btn.getAttribute("onclick").includes(pageId)) {
      btn.classList.add("active");
    }
  });

  if (pageId === "recommend") {
    recommendSection.classList.remove("hidden");
  } else {
    placeholderSection.classList.remove("hidden");
    title.innerText = pageId.charAt(0).toUpperCase() + pageId.slice(1);
  }
}

// 2. CORE RECOMMENDATION HANDLER
async function handleRecommendation() {
  const queryInput = document.getElementById("user-query");
  const query = queryInput.value.trim();

  if (!query) {
    alert("Please enter a vibe first!");
    return;
  }

  const statusBox = document.getElementById("status-box");
  const resultsContainer = document.getElementById("results-container");
  const posterGrid = document.getElementById("poster-grid");
  const narrativeContainer = document.getElementById("narrative-container");

  statusBox.classList.remove("hidden");
  resultsContainer.classList.add("hidden");
  posterGrid.innerHTML = "";
  narrativeContainer.innerHTML = "";

  try {
    const response = await fetch(
      `/api/recommend?query=${encodeURIComponent(query)}`,
    );
    const data = await response.json();

    if (!data.success) throw new Error(data.error);

    const metadataPromises = data.titles.map((title) => fetchMetadata(title));
    const metadataResults = await Promise.all(metadataPromises);

    metadataResults.forEach((meta, index) => {
      if (meta && !meta.error) {
        renderAnimeCard(meta, index);
      }
    });

    data.explanations.forEach((exp, index) => {
      renderNarrativeBox(exp, index + 1);
    });

    statusBox.classList.add("hidden");
    resultsContainer.classList.remove("hidden");
  } catch (error) {
    console.error("AI Engine Error:", error);
    alert("The Connoisseur is having trouble: " + error.message);
    statusBox.classList.add("hidden");
  }
}

// 3. METADATA HELPER
async function fetchMetadata(title) {
  try {
    const res = await fetch(`/api/metadata?title=${encodeURIComponent(title)}`);
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

// 4. DOM COMPONENT CREATORS
function renderAnimeCard(meta, index) {
  const grid = document.getElementById("poster-grid");
  const card = document.createElement("div");
  card.className = "anime-card";
  card.style.animationDelay = `${index * 200}ms`;

  card.innerHTML = `
        <img src="${meta.image}" alt="${meta.title}" loading="lazy">
        <div class="anime-card-content">
            <h3>${meta.title}</h3>
            <p style="color: #fbbf24; margin-bottom: 15px;">
                <span style="font-size: 1.2rem;">★</span> Score: ${meta.score}
            </p>
            <a href="${meta.url}" target="_blank" class="mal-link-btn">View on MAL</a>
        </div>
    `;
  grid.appendChild(card);
}

function renderNarrativeBox(text, rank) {
  const container = document.getElementById("narrative-container");
  const box = document.createElement("div");
  box.className = "rec-item-container";

  const formattedText = text.replace(
    /\*\*(.*?)\*\*/g,
    '<span class="highlight-bold">$1</span>',
  );

  box.innerHTML = `
        <div style="color: #00c6ff; font-weight: 800; font-size: 0.85rem; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1px;">
            Match Rank #${rank}
        </div>
        <div class="rec-text" style="line-height: 1.8; font-size: 1.05rem; color: #e2e8f0;">
            ${formattedText}
        </div>
    `;
  container.appendChild(box);
}

// 5. TOP 50 IN-CARD SCROLL LOGIC
async function toggleTop50() {
  const container = document.getElementById("top-anime-list-container");
  const link = document.getElementById("expand-top-anime");

  if (container.classList.contains("list-container-expanded")) {
    container.classList.remove("list-container-expanded");
    container.scrollTo({ top: 0, behavior: "smooth" });
    link.innerText = " More > ";
    return;
  }

  container.classList.add("list-container-expanded");
  link.innerText = " Loading... ";

  try {
    const response = await fetch("/api/top-anime");
    const result = await response.json();

    if (result.success) {
      // FIX: Sort numerically to ensure 49 is before 50/51
      const sortedData = result.data.sort((a, b) => a.rank - b.rank);

      const allItems = sortedData
        .map(
          (anime) => `
                <div class="list-item">
                    <span class="rank-val">${anime.rank}</span> 
                    ${anime.title} 
                    <span style="margin-left:auto; color:#94a3b8; font-size:0.8rem;">⭐ ${anime.score}</span>
                </div>
            `,
        )
        .join("");

      container.innerHTML = allItems;
      link.innerText = " Less < ";
    }
  } catch (e) {
    link.innerText = " Error ";
  }
}

// 6. INITIALIZATION GUARD
document.addEventListener("DOMContentLoaded", () => {
  // Force cleanup on load
  const modal = document.getElementById("top-anime-modal");
  if (modal) modal.classList.add("hidden");

  // Register Enter Key for search
  document.getElementById("user-query").addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleRecommendation();
  });

  switchPage("recommend");
});
// --- NEW: FETCH AND RENDER TRENDING CARDS ---
async function loadTrendingData() {
  const animeContainer = document.getElementById("top-anime-list-container");
  const charContainer = document.getElementById("popular-characters-container");

  try {
    // Fetch Top Anime (Already built in your FastAPI backend)
    const animeRes = await fetch("/api/top-anime");
    const animeData = await animeRes.json();

    if (animeData.success) {
      // Render only the Top 4 initially as requested
      animeContainer.innerHTML = animeData.data
        .slice(0, 4)
        .map(
          (anime) => `
                <div class="list-item">
                    <span class="rank-val">${anime.rank}</span> ${anime.title}
                </div>
            `,
        )
        .join("");
    }

    // Fetch Popular Characters (Direct Jikan call for simplicity)
    const charRes = await fetch(
      "https://api.jikan.moe/v4/top/characters?limit=4",
    );
    const charData = await charRes.json();

    if (charData.data) {
      charContainer.innerHTML = charData.data
        .map(
          (char, index) => `
                <div class="list-item">
                    <span class="rank-val">${index + 1}</span> ${char.name}
                </div>
            `,
        )
        .join("");
    }
  } catch (e) {
    console.error("Trending Load Error:", e);
    animeContainer.innerHTML = "<p>Update pending...</p>";
    charContainer.innerHTML = "<p>Update pending...</p>";
  }
}

// --- UPDATE INITIALIZATION GUARD ---
document.addEventListener("DOMContentLoaded", () => {
  // ... your existing modal/page cleanup ...

  // Trigger the live data load
  loadTrendingData();

  switchPage("recommend");
});

async function toggleTop50Characters() {
  const container = document.getElementById("popular-characters-container");
  const link = document.getElementById("expand-popular-chars");

  // Toggle scrollable state (using the same CSS class as Top Anime)
  if (container.classList.contains("list-container-expanded")) {
    container.classList.remove("list-container-expanded");
    container.scrollTo({ top: 0, behavior: "smooth" });
    link.innerText = " More > ";
    return;
  }

  // Check if we already loaded the 50 items to prevent duplicate API calls
  if (container.children.length > 5) {
    container.classList.add("list-container-expanded");
    link.innerText = " Less < ";
    return;
  }

  link.innerText = " Loading... ";

  try {
    const response = await fetch("/api/top-characters");
    const result = await response.json();

    if (result.success) {
      // Replace initial top 4 with the full sorted list
      const allItems = result.data
        .map(
          (char) => `
                <div class="list-item">
                    <span class="rank-val">${char.rank}</span> 
                    ${char.name}
                </div>
            `,
        )
        .join("");

      container.innerHTML = allItems;
      container.classList.add("list-container-expanded");
      link.innerText = " Less < ";
    }
  } catch (e) {
    console.error("Top Characters Load Error:", e);
    link.innerText = " Error ";
  }
}
