(() => {
  const data = window.RATINGS;
  if (!data || !Array.isArray(data.episodes)) {
    document.getElementById("list").innerHTML =
      "<p class='empty'>😅 Missing data.js — run <code>python3 build_web.py</code>.</p>";
    return;
  }

  // Buckets from overall score:
  // safe  = 1–2  · maybe = 3  · skip = 4–5
  const BUCKETS = {
    all: {
      match: () => true,
      hint: "✨ Everything in the catalog — tap a vibe to narrow it.",
      stats: "episodes",
    },
    safe: {
      match: (ep) => ep.overall <= 2,
      hint: "✅ All clear — mild enough for most kid couch nights.",
      stats: "all-clear picks",
    },
    maybe: {
      match: (ep) => ep.overall === 3,
      hint: "🤔 Gray area — sitcom adult stuff; preview or stay in the room.",
      stats: "gray-area picks",
    },
    skip: {
      match: (ep) => ep.overall >= 4,
      hint: "🚫 Hard pass — strippers, affairs, heavy sex jokes… skip with little kids.",
      stats: "hard-pass episodes",
    },
  };

  const BUCKET_BADGE = {
    safe: { className: "bucket-pill safe", text: "All clear" },
    maybe: { className: "bucket-pill maybe", text: "Gray area" },
    skip: { className: "bucket-pill skip", text: "Hard pass" },
  };

  const NOTES_TITLE = {
    safe: "Mild notes",
    maybe: "What parents notice",
    skip: "Why it’s a hard pass",
  };

  const els = {
    season: document.getElementById("season"),
    q: document.getElementById("q"),
    sort: document.getElementById("sort"),
    list: document.getElementById("list"),
    empty: document.getElementById("empty"),
    stats: document.getElementById("stats"),
    disclaimer: document.getElementById("disclaimer"),
    hint: document.getElementById("bucket-hint"),
    vibeBtns: [...document.querySelectorAll(".vibe-btn")],
  };

  let bucket = "safe";

  els.disclaimer.textContent =
    "👋 Fun family guide, not an official rating. Your kids / your rules!";

  els.vibeBtns.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.bucket === bucket);
  });

  const seasons = [...new Set(data.episodes.map((e) => e.season))].sort((a, b) => a - b);
  for (const s of seasons) {
    const opt = document.createElement("option");
    opt.value = String(s);
    opt.textContent = `Season ${s} 🎬`;
    els.season.appendChild(opt);
  }

  function bucketOf(ep) {
    if (ep.overall <= 2) return "safe";
    if (ep.overall === 3) return "maybe";
    return "skip";
  }

  function refreshCounts() {
    const season = els.season.value;
    const q = els.q.value.trim().toLowerCase();
    const base = data.episodes.filter((ep) => {
      if (season !== "all" && String(ep.season) !== season) return false;
      if (!q) return true;
      const blob = [
        ep.title,
        ep.index_title,
        ep.code,
        ep.summary || "",
        ...(ep.examples || []),
        ep.notes || "",
      ]
        .join(" ")
        .toLowerCase();
      return blob.includes(q);
    });

    const counts = { all: base.length, safe: 0, maybe: 0, skip: 0 };
    for (const ep of base) counts[bucketOf(ep)] += 1;

    for (const [key, n] of Object.entries(counts)) {
      document.querySelectorAll(`[data-count-for="${key}"]`).forEach((node) => {
        node.textContent = String(n);
      });
    }
  }

  function epLabel(ep) {
    const epNum = String(ep.episode).replace(/^0+/, "") || ep.episode;
    return `S${ep.season} E${epNum}`;
  }

  function signalOf(value) {
    if (value >= 4) return "stop";
    if (value === 3) return "caution";
    return "go";
  }

  function scoreBlock(emoji, label, value) {
    const signal = signalOf(value);
    const tip = `${label} ${value}/5 · ${
      signal === "stop" ? "STOP" : signal === "caution" ? "Caution" : "Go"
    }`;
    return `
      <div class="score-block" data-tip="${escapeHtml(tip)}">
        <span class="score-label">${emoji} ${label}</span>
        <div
          class="semaphore signal-${signal} intensity-${value}"
          role="img"
          aria-label="${escapeHtml(tip)}"
        >
          <span class="sem-housing">
            <i class="lamp stop"></i>
            <i class="lamp caution"></i>
            <i class="lamp go"></i>
          </span>
          <span class="sem-hover">${value}/5</span>
        </div>
      </div>
    `;
  }

  function renderCard(ep, i) {
    const bKey = bucketOf(ep);
    const examples = (ep.examples || [])
      .map((x) => `<li>${escapeHtml(x)}</li>`)
      .join("");
    const notes = ep.notes
      ? `<p class="notes">📝 ${escapeHtml(ep.notes)}</p>`
      : "";
    const badge = BUCKET_BADGE[bKey];
    const summary = ep.summary
      ? `<p class="summary">${escapeHtml(ep.summary)}</p>`
      : "";
    return `
      <article class="card card-${bKey}" style="animation-delay:${Math.min(i, 12) * 25}ms">
        <div class="card-top">
          <div class="card-copy">
            <div class="ep-meta">
              <span class="badge">🎞️ ${escapeHtml(epLabel(ep))}</span>
              <span class="${badge.className}">${escapeHtml(badge.text)}</span>
            </div>
            <h2>${escapeHtml(cleanTitle(ep.title))}</h2>
            ${summary}
          </div>
          <div class="scores" aria-label="Traffic-light content guide">
            ${scoreBlock("👊", "Violence", ep.violence)}
            ${scoreBlock("💋", "Sex", ep.sex)}
            ${scoreBlock("🙊", "Language", ep.language)}
            ${scoreBlock("⭐", "Overall", ep.overall)}
          </div>
        </div>
        <div class="notes-block">
          <p class="examples-title">${NOTES_TITLE[bKey]}</p>
          <ul class="examples">${examples}</ul>
        </div>
        ${notes}
      </article>
    `;
  }

  function cleanTitle(title) {
    return String(title).replace(/\s+/g, " ").trim();
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function sortEpisodes(list, mode) {
    const copy = [...list];
    const air = (a, b) =>
      a.season - b.season ||
      String(a.episode).localeCompare(String(b.episode), undefined, { numeric: true });
    switch (mode) {
      case "overall-desc":
        return copy.sort((a, b) => b.overall - a.overall || air(a, b));
      case "overall-asc":
        return copy.sort((a, b) => a.overall - b.overall || air(a, b));
      case "sex-desc":
        return copy.sort((a, b) => b.sex - a.sex || air(a, b));
      case "language-desc":
        return copy.sort((a, b) => b.language - a.language || air(a, b));
      case "violence-desc":
        return copy.sort((a, b) => b.violence - a.violence || air(a, b));
      default:
        return copy.sort(air);
    }
  }

  function apply() {
    const season = els.season.value;
    const q = els.q.value.trim().toLowerCase();
    const conf = BUCKETS[bucket];

    let filtered = data.episodes.filter((ep) => {
      if (season !== "all" && String(ep.season) !== season) return false;
      if (!conf.match(ep)) return false;
      if (!q) return true;
      const blob = [
        ep.title,
        ep.index_title,
        ep.code,
        ep.summary || "",
        ...(ep.examples || []),
        ep.notes || "",
      ]
        .join(" ")
        .toLowerCase();
      return blob.includes(q);
    });

    filtered = sortEpisodes(filtered, els.sort.value);
    refreshCounts();

    els.hint.textContent = conf.hint;
    els.stats.textContent = `🎉 ${filtered.length} ${conf.stats}`;
    els.empty.classList.toggle("hidden", filtered.length > 0);
    els.list.innerHTML = filtered.map((ep, i) => renderCard(ep, i)).join("");
  }

  els.vibeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      bucket = btn.dataset.bucket;
      els.vibeBtns.forEach((b) => b.classList.toggle("is-active", b === btn));
      apply();
      window.scrollTo({ top: els.list.offsetTop - 24, behavior: "smooth" });
    });
  });

  for (const el of [els.season, els.q, els.sort]) {
    el.addEventListener("input", apply);
    el.addEventListener("change", apply);
  }

  apply();
})();
