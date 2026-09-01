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
    safe: "Watch for",
    maybe: "Watch for",
    skip: "Watch for",
  };

  const els = {
    season: document.getElementById("season"),
    episode: document.getElementById("episode"),
    episodeField: document.getElementById("episode-field"),
    controlsBar: document.querySelector(".controls-bar"),
    q: document.getElementById("q"),
    sort: document.getElementById("sort"),
    list: document.getElementById("list"),
    empty: document.getElementById("empty"),
    stats: document.getElementById("stats"),
    disclaimer: document.getElementById("disclaimer"),
    hint: document.getElementById("bucket-hint"),
    vibeBtns: [...document.querySelectorAll(".vibe-btn")],
    themeChips: document.getElementById("theme-chips"),
    themeClear: document.getElementById("theme-clear"),
  };

  let bucket = "all";
  const selectedThemes = new Set();
  const PAGE_SIZE = 10;
  const THEMES_PER_PAGE = 3;
  let listPage = 1;
  let pendingEpScroll = null;

  els.disclaimer.textContent =
    "👋 Fun family guide, not an official rating. Your kids — your rules!";

  els.vibeBtns.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.bucket === bucket);
  });

  const seasons = [...new Set(data.episodes.map((e) => e.season))].sort((a, b) => Number(a) - Number(b));
  for (const s of seasons) {
    const opt = document.createElement("option");
    opt.value = String(s);
    const episodeCount = data.episodes.filter((e) => e.season === s).length;
    const epLabel = episodeCount === 1 ? '1 ep' : `${episodeCount} eps`;
    opt.textContent = (s === 0 || s === '0') ? `Other / specials (${epLabel}) 🎬` : `Season ${s} (${epLabel}) 🎬`;
    els.season.appendChild(opt);
  }

  function epAnchorId(ep) {
    const code = String(ep.code).replace(/[^A-Za-z0-9._-]+/g, "-");
    return `ep-${code}`;
  }

  function episodesInSeason(season) {
    return data.episodes
      .filter((ep) => inSelectedSeason(ep, season))
      .sort(
        (a, b) =>
          String(a.episode).localeCompare(String(b.episode), undefined, { numeric: true })
      );
  }

  function episodeOptionLabel(ep) {
    const epNum = String(ep.episode).replace(/^0+/, "") || ep.episode;
    const title = cleanTitle(ep.title);
    const short = title.length > 42 ? title.slice(0, 42).replace(/[ ,;:—-]+$/, "") + "…" : title;
    return `E${epNum} · ${short}`;
  }

  function renderEpisodeSelect() {
    if (!els.episode || !els.episodeField) return;
    const season = els.season.value;
    const showPicker = season !== "all";
    els.episodeField.hidden = !showPicker;
    els.controlsBar?.classList.toggle("has-episode", showPicker);
    if (!showPicker) {
      els.episode.innerHTML = '<option value="">Jump to episode…</option>';
      els.episode.value = "";
      return;
    }
    const eps = episodesInSeason(season);
    els.episode.innerHTML =
      '<option value="">Jump to episode…</option>' +
      eps
        .map(
          (ep) =>
            `<option value="${escapeHtml(epAnchorId(ep))}">${escapeHtml(episodeOptionLabel(ep))}</option>`
        )
        .join("");
    els.episode.value = "";
  }

  function filteredList({ season, q, sortMode }) {
    const conf = BUCKETS[bucket];
    let filtered = data.episodes.filter((ep) => {
      if (!inSelectedSeason(ep, season)) return false;
      if (!conf.match(ep)) return false;
      if (!matchesThemes(ep)) return false;
      return matchesQuery(ep, q);
    });
    return sortEpisodes(filtered, sortMode);
  }

  function ensureEpisodeVisible(code) {
    const ep = data.episodes.find((e) => epAnchorId(e) === code);
    if (!ep) return null;
    const season = els.season.value;
    const q = els.q.value.trim().toLowerCase();
    let sortMode = selectedThemes.size && els.sort.value === "air" ? "themes" : els.sort.value;
    let list = filteredList({ season, q, sortMode });
    if (!list.some((e) => epAnchorId(e) === code)) {
      bucket = "all";
      selectedThemes.clear();
      els.q.value = "";
      els.vibeBtns.forEach((b) => b.classList.toggle("is-active", b.dataset.bucket === "all"));
      renderThemeChips();
      sortMode = els.sort.value;
      list = filteredList({ season, q: "", sortMode });
    }
    if (!list.some((e) => epAnchorId(e) === code)) return null;
    const index = list.findIndex((e) => epAnchorId(e) === code);
    listPage = Math.floor(index / PAGE_SIZE) + 1;
    pendingEpScroll = code;
    apply();
    return ep;
  }

  function scrollToEpisodeAnchor(code) {
    const target =
      document.getElementById(code) ||
      document.querySelector(`.ep-index-row#${CSS.escape(code)}`);
    if (!target) return;
    if (location.hash !== `#${code}`) {
      history.replaceState(null, "", `#${code}`);
    }
    const top = target.getBoundingClientRect().top + window.scrollY - 24;
    window.scrollTo({ top, behavior: "smooth" });
    target.classList.add("ep-highlight");
    window.setTimeout(() => target.classList.remove("ep-highlight"), 1400);
  }

  function jumpToEpisode(code) {
    if (!code) return;
    ensureEpisodeVisible(code);
  }

  function watchThemesOf(ep) {
    const themes = ep.themes || {};
    const watch = themes.watch || [];
    return watch.filter((x) => x && x.length <= 40 && !/[.!]$/.test(x));
  }

  function watchDetailsOf(ep) {
    const details = ep.themes && ep.themes.watch_detail;
    if (Array.isArray(details) && details.length) {
      return details.filter((d) => d && d.theme);
    }
    return watchThemesOf(ep).map((theme) => ({ theme, how: "" }));
  }

  /** Cards stay scannable — the full wording lives on the episode page. */
  function clamp(text, max = 110) {
    if (text.length <= max) return text;
    const cut = text.slice(0, max);
    const space = cut.lastIndexOf(" ");
    return (space > max * 0.6 ? cut.slice(0, space) : cut).replace(/[ ,;:—-]+$/, "") + "…";
  }

  /** Most severe moment for a theme: quotes get quote marks, notes stay prose. */
  function headlineOf(d) {
    const text = clamp((d.text || d.how || "").trim());
    if (!text) return "";
    if (d.kind === "quote") {
      const speaker = (d.speaker || "").trim();
      const quoted = `<q>${escapeHtml(text)}</q>`;
      return speaker
        ? `<span class="theme-speaker">${escapeHtml(speaker)}</span> ${quoted}`
        : quoted;
    }
    return escapeHtml(text);
  }

  function instancesOf(d) {
    if (Array.isArray(d.instances) && d.instances.length) return d.instances;
    const text = (d.text || d.how || "").trim();
    return text ? [{ kind: d.kind, speaker: d.speaker, text }] : [];
  }

  function wrapIndex(i, n) {
    if (n <= 0) return 0;
    return ((i % n) + n) % n;
  }

  function themeItemHtml(d, { hidden } = {}) {
    const instances = instancesOf(d);
    const inst = instances[0] || d;
    const headline = headlineOf(inst);
    const count = Number(d.count) || instances.length || 1;
    const n = instances.length;
    let extra = "";
    if (n > 1) {
      extra = `<span class="theme-pager">
        <button type="button" class="theme-page-btn" data-watch-step="-1" aria-label="Previous ${escapeHtml(d.theme)} moment">‹</button>
        <span class="theme-page-n" data-watch-n>1/${n}</span>
        <button type="button" class="theme-page-btn" data-watch-step="1" aria-label="Next ${escapeHtml(d.theme)} moment">›</button>
      </span>`;
    } else if (count > 1) {
      extra = `<span class="theme-more" title="${count} moments in this episode">+${count - 1}</span>`;
    }
    const payload = escapeHtml(
      JSON.stringify(
        instances.map((x) => ({
          kind: x.kind || "",
          speaker: x.speaker || "",
          text: x.text || x.how || "",
        }))
      )
    );
    return `<li class="theme-item"${hidden ? " hidden" : ""} data-instances="${payload}" data-idx="0">
      <span class="theme-item-head">
        <span class="theme-name">${escapeHtml(d.theme)}</span>${extra}
      </span>${headline ? `<span class="theme-how" data-watch-how>${headline}</span>` : ""}
    </li>`;
  }

  function matchesQuery(ep, q) {
    if (!q) return true;
    const details = watchDetailsOf(ep);
    const blob = [
      ep.title,
      ep.index_title,
      ep.code,
      ep.summary || "",
      ...watchThemesOf(ep),
      ...details.map((d) => {
        const inst = instancesOf(d)
          .map((x) => `${x.speaker || ""} ${x.text || ""}`)
          .join(" ");
        return `${d.theme} ${d.how || ""} ${inst}`;
      }),
      ep.notes || "",
    ]
      .join(" ")
      .toLowerCase();
    return blob.includes(q);
  }

  function matchesThemes(ep) {
    if (!selectedThemes.size) return true;
    const watch = watchThemesOf(ep);
    for (const t of selectedThemes) {
      if (watch.includes(t)) return true;
    }
    return false;
  }

  function seasonKey(value) {
    return String(value);
  }

  function inSelectedSeason(ep, season = els.season.value) {
    return season === "all" || seasonKey(ep.season) === season;
  }

  function themeIndex() {
    const season = els.season.value;
    const q = els.q.value.trim().toLowerCase();
    const counts = new Map();
    for (const ep of data.episodes) {
      if (!inSelectedSeason(ep, season)) continue;
      if (!matchesQuery(ep, q)) continue;
      for (const t of watchThemesOf(ep)) {
        counts.set(t, (counts.get(t) || 0) + 1);
      }
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function renderThemeChips() {
    if (!els.themeChips) return;
    const index = themeIndex();
    if (!index.length) {
      els.themeChips.innerHTML =
        '<p class="theme-chips-empty">No watch-for themes in this slice.</p>';
      if (els.themeClear) els.themeClear.hidden = true;
      return;
    }
    // Drop themes that disappeared after season change
    for (const t of [...selectedThemes]) {
      if (!index.some(([label]) => label === t)) selectedThemes.delete(t);
    }
    els.themeChips.innerHTML = index
      .map(([label, count]) => {
        const on = selectedThemes.has(label);
        return `
          <button
            type="button"
            class="theme-chip${on ? " is-on" : ""}"
            data-theme="${escapeHtml(label)}"
            aria-pressed="${on ? "true" : "false"}"
          >
            <span class="theme-chip-label">${escapeHtml(label)}</span>
            <span class="theme-chip-count">${count}</span>
          </button>`;
      })
      .join("");
    if (els.themeClear) els.themeClear.hidden = selectedThemes.size === 0;
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
      if (!inSelectedSeason(ep, season)) return false;
      if (!matchesThemes(ep)) return false;
      return matchesQuery(ep, q);
    });

    const counts = { all: base.length, safe: 0, maybe: 0, skip: 0 };
    for (const ep of base) counts[bucketOf(ep)] += 1;

    for (const [key, n] of Object.entries(counts)) {
      document.querySelectorAll(`[data-count-for="${key}"]`).forEach((node) => {
        node.textContent = String(n);
      });
      // Disable bucket buttons when count is zero (except "all")
      const btn = document.getElementById(`bucket-${key}`);
      if (btn && key !== "all") {
        btn.disabled = n === 0;
        btn.setAttribute("aria-disabled", n === 0 ? "true" : "false");
      }
    }
  }

  function emptyCopy({ season, q }) {
    const hasSearch = Boolean(q);
    const hasThemes = selectedThemes.size > 0;
    const seasonNarrow = season !== "all";
    if (hasSearch) return "Nothing matched that search. Try another word, or clear the box.";
    if (bucket === "safe" && !hasThemes && !seasonNarrow) {
      const anySafe = data.episodes.some((ep) => ep.overall <= 2);
      if (!anySafe) {
        return "No all-clear episodes in this show — try Gray area, or Show all.";
      }
    }
    if (bucket === "safe") {
      return "No all-clear episodes in this slice — try Gray area, or Show all.";
    }
    if (hasThemes) return "Nothing matched those themes. Clear a chip or pick Show all.";
    if (seasonNarrow) return "Nothing in this season for the current filters.";
    return "Nothing matched. Loosen the filters and try again!";
  }

  function epLabel(ep) {
    const epNum = String(ep.episode).replace(/^0+/, "") || ep.episode;
    if (ep.season === 0 || ep.season === '0') return `Ep ${epNum}`;
    return `S${ep.season} E${epNum}`;
  }

  function signalOf(value) {
    if (value >= 4) return "stop";
    if (value === 3) return "caution";
    return "go";
  }

  function fitReadout(overall) {
    if (overall <= 2) return { label: "Mostly appropriate", short: "Appropriate lean" };
    if (overall === 3) return { label: "Mixed — preview first", short: "Mixed" };
    return { label: "Leans inappropriate", short: "Inappropriate lean" };
  }

  function fitMeterHtml(ep) {
    const overall = Number(ep.overall) || 1;
    // 1 → 8%, 5 → 92% so marker never kisses the rail
    const fit = ((overall - 1) / 4) * 0.84 + 0.08;
    const signal = signalOf(overall);
    const readout = fitReadout(overall);
    const themes = ep.themes || { fine: [], watch: [] };
    const fineN = (themes.fine || []).length;
    const watchN = (themes.watch || []).length;
    const themeTotal = fineN + watchN;
    const watchShare = themeTotal ? watchN / themeTotal : fit;
    const aria = `Kid-fit meter: ${readout.label}. Overall ${overall} of 5.`;
    return `
      <div class="fit-meter signal-${signal}" style="--fit:${fit.toFixed(3)}; --watch:${watchShare.toFixed(3)}" role="img" aria-label="${escapeHtml(aria)}">
        <div class="fit-meter-top">
          <span class="fit-meter-kicker">Kid fit</span>
          <span class="fit-meter-readout">${escapeHtml(readout.label)}</span>
        </div>
        <div class="fit-track">
          <span class="fit-gradient" aria-hidden="true"></span>
          <span class="fit-balance" aria-hidden="true" title="Theme balance"></span>
          <span class="fit-marker" aria-hidden="true">
            <span class="fit-marker-dot"></span>
            <span class="fit-marker-score">${overall}/5</span>
          </span>
        </div>
        <div class="fit-ends">
          <span>Appropriate</span>
          <span>Inappropriate</span>
        </div>
      </div>
    `;
  }

  function scoreBlock(emoji, label, value, compact) {
    const signal = signalOf(value);
    const tip = `${label} ${value}/5 · ${
      signal === "stop" ? "STOP" : signal === "caution" ? "Caution" : "Go"
    }`;
    if (compact) {
      return `
        <span class="score-chip signal-${signal}" title="${escapeHtml(tip)}" aria-label="${escapeHtml(tip)}">
          <span class="score-chip-emoji" aria-hidden="true">${emoji}</span>
          <span class="score-chip-n">${value}</span>
        </span>`;
    }
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

  function showId() {
    return (
      data.show_id ||
      location.pathname.split("/").pop().replace(/\.html$/, "") ||
      "friends"
    );
  }

  function epHref(ep) {
    const code = String(ep.code).replace(/[^A-Za-z0-9._-]+/g, "-");
    return `ep/${showId()}/${encodeURIComponent(code)}.html`;
  }

  function renderCard(ep, i) {
    const bKey = bucketOf(ep);
    const details = watchDetailsOf(ep);
    const themePages = Math.max(1, Math.ceil(details.length / THEMES_PER_PAGE));
    const watchLis = details
      .map((d, di) => themeItemHtml(d, { hidden: di >= THEMES_PER_PAGE }))
      .join("");
    const listPager =
      themePages > 1
        ? `<div class="watch-list-pager" data-watch-list-pager data-page="0">
            <button type="button" class="theme-page-btn" data-watch-list-step="-1" aria-label="Previous watch-for themes">‹</button>
            <span class="theme-page-n" data-watch-list-n>1/${themePages}</span>
            <button type="button" class="theme-page-btn" data-watch-list-step="1" aria-label="Next watch-for themes">›</button>
          </div>`
        : "";
    const themeHtml = details.length
      ? `<ul class="examples theme-watch-list">${watchLis}</ul>`
      : `<ul class="examples theme-watch-list"><li>No watch-for themes flagged.</li></ul>`;
    const notes = ep.notes
      ? `<p class="notes">📝 ${escapeHtml(ep.notes)}</p>`
      : "";
    const badge = BUCKET_BADGE[bKey];
    const summary = ep.summary
      ? `<p class="summary">${escapeHtml(ep.summary)}</p>`
      : "";
    const href = epHref(ep);
    // Prefer medium still for list thumbs — full stills are for episode pages.
    const stillSrc = ep.still || ep.stillFull;
    const still = stillSrc
      ? `<div class="card-still" aria-hidden="true"><img src="${escapeHtml(stillSrc)}" alt="" width="250" height="140" loading="lazy" decoding="async" referrerpolicy="no-referrer" /></div>`
      : "";
    return `
      <article class="card card-${bKey}${stillSrc ? " has-still" : ""}" id="${escapeHtml(epAnchorId(ep))}">
        <a class="card-hit" href="${href}" aria-label="Open ${escapeHtml(cleanTitle(ep.title))}">
          <div class="card-top">
            ${still}
            <div class="card-copy">
              <div class="ep-meta">
                <span class="badge">🎞️ ${escapeHtml(epLabel(ep))}</span>
                <span class="${badge.className}">${escapeHtml(badge.text)}</span>
              </div>
              <h2>${escapeHtml(cleanTitle(ep.title))}</h2>
              ${summary}
            </div>
            <div class="scores scores-full" aria-label="Traffic-light content guide">
              ${scoreBlock("👊", "Violence", ep.violence)}
              ${scoreBlock("💋", "Sex", ep.sex)}
              ${scoreBlock("🙊", "Language", ep.language)}
              ${scoreBlock("⭐", "Overall", ep.overall)}
            </div>
            <div class="scores-compact" aria-label="Content scores">
              ${scoreBlock("👊", "Violence", ep.violence, true)}
              ${scoreBlock("💋", "Sex", ep.sex, true)}
              ${scoreBlock("🙊", "Language", ep.language, true)}
              ${scoreBlock("⭐", "Overall", ep.overall, true)}
            </div>
          </div>
        </a>
        <div class="notes-block">
          <div class="examples-head">
            <p class="examples-title">${NOTES_TITLE[bKey]}</p>
            ${listPager}
          </div>
          ${themeHtml}
        </div>
        ${notes}
        <footer class="card-foot">
          <a class="card-open-hint" href="${href}">Open episode <span aria-hidden="true">→</span></a>
          <button
            type="button"
            class="report-trigger"
            data-code="${escapeHtml(ep.code)}"
            data-season="${escapeHtml(String(ep.season))}"
            data-episode="${escapeHtml(String(ep.episode))}"
            data-title="${escapeHtml(cleanTitle(ep.title))}"
            data-overall="${ep.overall}"
            aria-label="Report a mistake on ${escapeHtml(cleanTitle(ep.title))}"
          >
            <svg class="report-ico" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none">
              <path d="M3.5 2.5v11M3.5 3.2h7.2c.7 0 1.1.8.7 1.4l-1.1 1.7c-.2.3-.2.7 0 1l1.1 1.7c.4.6 0 1.4-.7 1.4H3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Report mistake</span>
          </button>
        </footer>
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
    const watchCount = (ep) => watchThemesOf(ep).length;
    const matchCount = (ep) => {
      if (!selectedThemes.size) return watchCount(ep);
      return watchThemesOf(ep).filter((t) => selectedThemes.has(t)).length;
    };
    switch (mode) {
      case "themes":
        return copy.sort((a, b) => matchCount(b) - matchCount(a) || b.overall - a.overall || air(a, b));
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

  function apply({ resetPage } = {}) {
    const season = els.season.value;
    const q = els.q.value.trim().toLowerCase();
    const conf = BUCKETS[bucket];

    let filtered = data.episodes.filter((ep) => {
      if (!inSelectedSeason(ep, season)) return false;
      if (!conf.match(ep)) return false;
      if (!matchesThemes(ep)) return false;
      return matchesQuery(ep, q);
    });

    // When filtering by themes, prefer theme-relevance ordering unless user picked another sort
    const sortMode =
      selectedThemes.size && els.sort.value === "air" ? "themes" : els.sort.value;
    filtered = sortEpisodes(filtered, sortMode);
    refreshCounts();
    renderThemeChips();  // Update theme chip counts when filters change

    const themeNote = selectedThemes.size
      ? ` · ${selectedThemes.size} theme${selectedThemes.size > 1 ? "s" : ""}`
      : "";
    const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    if (resetPage || listPage > pages) listPage = 1;
    const start = (listPage - 1) * PAGE_SIZE;
    const visible = filtered.slice(start, start + PAGE_SIZE);

    els.hint.textContent = conf.hint;
    const noun = conf.stats === "episodes" && filtered.length === 1 ? "episode" : conf.stats;
    const seasonNote = season !== "all" ? ` · season ${season}` : "";
    els.stats.textContent = `🎉 ${filtered.length} ${noun}${themeNote}${seasonNote}`;
    els.empty.textContent = emptyCopy({ season, q });
    els.empty.classList.toggle("hidden", filtered.length > 0);
    els.list.innerHTML = visible.map((ep, i) => renderCard(ep, i)).join("");
    renderListPager(filtered.length, pages, start);

    // The crawlable full index under the live list never respects filters —
    // hide it whenever the interactive list is narrowed so it doesn't look broken.
    const narrowed =
      season !== "all" || Boolean(q) || bucket !== "all" || selectedThemes.size > 0;
    document.querySelectorAll(".ep-index, .seo-copy").forEach((el) => {
      el.hidden = narrowed;
    });

    if (pendingEpScroll) {
      const code = pendingEpScroll;
      pendingEpScroll = null;
      requestAnimationFrame(() => scrollToEpisodeAnchor(code));
    }
  }

  function pageWindow(current, pages) {
    if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);
    const set = new Set([1, pages, current, current - 1, current + 1]);
    if (current <= 3) [2, 3, 4].forEach((n) => set.add(n));
    if (current >= pages - 2) [pages - 3, pages - 2, pages - 1].forEach((n) => set.add(n));
    const nums = [...set].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
    const out = [];
    for (let i = 0; i < nums.length; i++) {
      if (i && nums[i] - nums[i - 1] > 1) out.push("…");
      out.push(nums[i]);
    }
    return out;
  }

  function renderListPager(total, pages, start) {
    let nav = document.getElementById("list-pager");
    if (!nav) {
      nav = document.createElement("nav");
      nav.id = "list-pager";
      nav.className = "list-pager";
      nav.setAttribute("aria-label", "Episode list pages");
      els.list.insertAdjacentElement("afterend", nav);
      nav.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-list-page]");
        if (!btn || btn.disabled) return;
        const next = Number(btn.dataset.listPage);
        if (!Number.isFinite(next) || next === listPage) return;
        listPage = next;
        apply();
        const top = els.list.getBoundingClientRect().top + window.scrollY - 24;
        window.scrollTo({ top, behavior: "smooth" });
      });
    }
    if (pages <= 1 || total === 0) {
      nav.hidden = true;
      nav.innerHTML = "";
      return;
    }
    nav.hidden = false;
    const end = Math.min(start + PAGE_SIZE, total);
    const buttons = pageWindow(listPage, pages)
      .map((p) => {
        if (p === "…") return `<span class="list-pager-gap" aria-hidden="true">…</span>`;
        const current = p === listPage;
        return `<button type="button" class="list-pager-btn${current ? " is-active" : ""}" data-list-page="${p}"${current ? ' aria-current="page"' : ""}>${p}</button>`;
      })
      .join("");
    nav.innerHTML = `
      <p class="list-pager-range">${start + 1}–${end} of ${total}</p>
      <div class="list-pager-btns">
        <button type="button" class="list-pager-btn" data-list-page="${listPage - 1}" ${listPage <= 1 ? "disabled" : ""} aria-label="Previous page">‹</button>
        ${buttons}
        <button type="button" class="list-pager-btn" data-list-page="${listPage + 1}" ${listPage >= pages ? "disabled" : ""} aria-label="Next page">›</button>
      </div>
    `;
  }

  function applyInstance(li, nextIdx) {
    let instances = [];
    try {
      instances = JSON.parse(li.dataset.instances || "[]");
    } catch (_) {
      return;
    }
    if (!instances.length) return;
    const idx = wrapIndex(nextIdx, instances.length);
    li.dataset.idx = String(idx);
    const how = li.querySelector("[data-watch-how]");
    const nEl = li.querySelector("[data-watch-n]");
    if (how) how.innerHTML = headlineOf(instances[idx]);
    if (nEl) nEl.textContent = `${idx + 1}/${instances.length}`;
  }

  function applyThemePage(block, nextPage) {
    const ul = block.querySelector(".theme-watch-list");
    const pager = block.querySelector("[data-watch-list-pager]");
    if (!ul) return;
    const items = [...ul.querySelectorAll(":scope > li")];
    const pages = Math.max(1, Math.ceil(items.length / THEMES_PER_PAGE));
    const page = wrapIndex(nextPage, pages);
    items.forEach((li, i) => {
      li.hidden = i < page * THEMES_PER_PAGE || i >= (page + 1) * THEMES_PER_PAGE;
    });
    if (pager) {
      pager.dataset.page = String(page);
      const nEl = pager.querySelector("[data-watch-list-n]");
      if (nEl) nEl.textContent = `${page + 1}/${pages}`;
    }
  }

  els.list.addEventListener("click", (e) => {
    const stepBtn = e.target.closest("[data-watch-step]");
    if (stepBtn) {
      e.preventDefault();
      const li = stepBtn.closest("li");
      if (li) applyInstance(li, Number(li.dataset.idx || 0) + Number(stepBtn.dataset.watchStep));
      return;
    }
    const listBtn = e.target.closest("[data-watch-list-step]");
    if (!listBtn) return;
    e.preventDefault();
    const pager = listBtn.closest("[data-watch-list-pager]");
    const block = listBtn.closest(".notes-block");
    if (pager && block) {
      applyThemePage(block, Number(pager.dataset.page || 0) + Number(listBtn.dataset.watchListStep));
    }
  });

  els.vibeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      bucket = btn.dataset.bucket;
      els.vibeBtns.forEach((b) => b.classList.toggle("is-active", b === btn));
      apply({ resetPage: true });
      window.scrollTo({ top: els.list.offsetTop - 24, behavior: "smooth" });
    });
  });

  if (els.themeChips) {
    els.themeChips.addEventListener("click", (e) => {
      const btn = e.target.closest(".theme-chip");
      if (!btn) return;
      const theme = btn.dataset.theme;
      if (selectedThemes.has(theme)) selectedThemes.delete(theme);
      else selectedThemes.add(theme);
      renderThemeChips();
      apply({ resetPage: true });
    });
  }
  if (els.themeClear) {
    els.themeClear.addEventListener("click", () => {
      selectedThemes.clear();
      renderThemeChips();
      apply({ resetPage: true });
    });
  }

  for (const el of [els.season, els.q, els.sort]) {
    el.addEventListener("input", () => {
      if (el === els.season || el === els.q) renderThemeChips();
      if (el === els.season) renderEpisodeSelect();
      apply({ resetPage: true });
    });
    el.addEventListener("change", () => {
      if (el === els.season || el === els.q) renderThemeChips();
      if (el === els.season) renderEpisodeSelect();
      apply({ resetPage: true });
    });
  }

  if (els.episode) {
    els.episode.addEventListener("change", () => {
      const code = els.episode.value;
      if (code) jumpToEpisode(code);
      els.episode.value = "";
    });
  }

  window.addEventListener("hashchange", () => {
    const hash = location.hash.replace(/^#/, "");
    if (hash.startsWith("ep-")) jumpToEpisode(hash);
  });

  setupReportFlow();
  renderThemeChips();
  renderEpisodeSelect();

  const initialHash = location.hash.replace(/^#/, "");
  if (initialHash.startsWith("ep-")) {
    const ep = data.episodes.find((e) => epAnchorId(e) === initialHash);
    if (ep) {
      els.season.value = seasonKey(ep.season);
      renderEpisodeSelect();
      renderThemeChips();
      pendingEpScroll = initialHash;
    }
  }

  apply();

  function setupReportFlow() {
    const REASONS = [
      { id: "too-lenient", label: "Missed something inappropriate" },
      { id: "too-strict", label: "Rated too harsh" },
      { id: "wrong-score", label: "Wrong score (V / S / L)" },
      { id: "wrong-themes", label: "Themes or notes are off" },
      { id: "wrong-ep", label: "Wrong episode details" },
      { id: "other", label: "Something else" },
    ];

    const root = document.createElement("div");
    root.id = "report-root";
    root.innerHTML = `
      <div class="report-scrim" data-report-close hidden></div>
      <div class="report-sheet" role="dialog" aria-modal="true" aria-labelledby="report-title" hidden>
        <div class="report-panel" data-report-view="form">
          <header class="report-head">
            <div>
              <p class="report-kicker">Help us stay accurate</p>
              <h2 id="report-title">Report a mistake</h2>
            </div>
            <button type="button" class="report-x" data-report-close aria-label="Close">
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M4.5 4.5l9 9M13.5 4.5l-9 9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            </button>
          </header>
          <p class="report-ep" id="report-ep"></p>
          <form id="report-form" class="report-form" novalidate>
            <fieldset class="report-fieldset">
              <legend>What’s wrong?</legend>
              <div class="report-reasons" id="report-reasons" role="radiogroup" aria-label="Reason"></div>
            </fieldset>
            <label class="report-label" for="report-details">
              Details <span class="opt">(optional)</span>
            </label>
            <textarea id="report-details" name="details" rows="3" maxlength="600" placeholder="A sentence is enough — e.g. “kiss scene around minute 12”"></textarea>
            <p class="report-hint">No account needed. We read every report.</p>
            <div class="report-actions">
              <button type="button" class="report-btn-ghost" data-report-close>Cancel</button>
              <button type="submit" class="report-btn-solid" id="report-submit" disabled>Send report</button>
            </div>
            <p class="report-error" id="report-error" hidden></p>
          </form>
        </div>
        <div class="report-panel report-done" data-report-view="done" hidden>
          <div class="report-check" aria-hidden="true">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><circle cx="14" cy="14" r="13" stroke="currentColor" stroke-width="1.5"/><path d="M8 14.2l4 4 8-8.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <h2>Thanks — noted.</h2>
          <p>We’ll review this episode and fix anything that’s off.</p>
          <button type="button" class="report-btn-solid" data-report-close>Done</button>
        </div>
      </div>
    `;
    document.body.appendChild(root);

    const scrim = root.querySelector(".report-scrim");
    const sheet = root.querySelector(".report-sheet");
    const formView = root.querySelector('[data-report-view="form"]');
    const doneView = root.querySelector('[data-report-view="done"]');
    const epEl = root.querySelector("#report-ep");
    const reasonsEl = root.querySelector("#report-reasons");
    const form = root.querySelector("#report-form");
    const details = root.querySelector("#report-details");
    const submitBtn = root.querySelector("#report-submit");
    const errEl = root.querySelector("#report-error");
    let activeEp = null;
    let reason = "";
    let lastFocus = null;
    let closeTimer = null;

    reasonsEl.innerHTML = REASONS.map(
      (r) => `
      <label class="report-reason">
        <input type="radio" name="reason" value="${r.id}" />
        <span>${escapeHtml(r.label)}</span>
      </label>`
    ).join("");

    function openReport(ep) {
      if (closeTimer) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      activeEp = ep;
      reason = "";
      details.value = "";
      errEl.hidden = true;
      submitBtn.disabled = true;
      submitBtn.textContent = "Send report";
      form.querySelectorAll('input[name="reason"]').forEach((el) => {
        el.checked = false;
      });
      epEl.innerHTML = `<span class="report-ep-code">${escapeHtml(
        epLabel({ season: ep.season, episode: ep.episode })
      )}</span> · ${escapeHtml(ep.title)}`;
      formView.hidden = false;
      doneView.hidden = true;
      scrim.hidden = false;
      sheet.hidden = false;
      document.body.classList.add("report-open");
      lastFocus = document.activeElement;
      void sheet.offsetWidth;
      scrim.classList.add("is-on");
      sheet.classList.add("is-on");
      reasonsEl.querySelector("input")?.focus();
    }

    function closeReport() {
      scrim.classList.remove("is-on");
      sheet.classList.remove("is-on");
      document.body.classList.remove("report-open");
      if (closeTimer) window.clearTimeout(closeTimer);
      closeTimer = window.setTimeout(() => {
        closeTimer = null;
        scrim.hidden = true;
        sheet.hidden = true;
        if (lastFocus && lastFocus.focus) lastFocus.focus();
      }, 180);
    }

    els.list.addEventListener("click", (e) => {
      const btn = e.target.closest(".report-trigger");
      if (!btn) return;
      openReport({
        code: btn.dataset.code,
        season: btn.dataset.season,
        episode: btn.dataset.episode,
        title: btn.dataset.title,
        overall: Number(btn.dataset.overall),
      });
    });

    sheet.addEventListener("click", (e) => {
      if (e.target === sheet) closeReport();
    });

    root.addEventListener("click", (e) => {
      if (e.target.closest("[data-report-close]")) closeReport();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !sheet.hidden) closeReport();
    });

    reasonsEl.addEventListener("change", (e) => {
      const input = e.target.closest('input[name="reason"]');
      if (!input) return;
      reason = input.value;
      submitBtn.disabled = !reason;
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!activeEp || !reason) return;
      errEl.hidden = true;
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending…";

      const payload = {
        show: data.show,
        show_id: data.show_id || null,
        code: activeEp.code,
        season: activeEp.season,
        episode: activeEp.episode,
        title: activeEp.title,
        overall: activeEp.overall,
        reason,
        reason_label: REASONS.find((r) => r.id === reason)?.label || reason,
        details: details.value.trim().slice(0, 600),
        page: location.href,
        at: new Date().toISOString(),
      };

      try {
        const key = "wwtk-reports";
        const prev = JSON.parse(localStorage.getItem(key) || "[]");
        prev.push(payload);
        localStorage.setItem(key, JSON.stringify(prev.slice(-80)));
      } catch (_) {
        /* ignore quota */
      }

      try {
        await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (_) {
        /* best-effort — local queue still kept */
      }

      formView.hidden = true;
      doneView.hidden = false;
      doneView.querySelector("button")?.focus();
    });
  }
})();
