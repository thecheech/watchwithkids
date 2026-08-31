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
    safe: { className: "bucket-pill safe", text: "✅ All clear" },
    maybe: { className: "bucket-pill maybe", text: "🤔 Gray area" },
    skip: { className: "bucket-pill skip", text: "🚫 Hard pass" },
  };

  const NOTES_TITLE = {
    safe: "Watch for",
    maybe: "Watch for",
    skip: "Watch for",
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
    themeChips: document.getElementById("theme-chips"),
    themeClear: document.getElementById("theme-clear"),
  };

  let bucket = "all";
  const selectedThemes = new Set();

  els.disclaimer.textContent =
    "👋 Fun family guide, not an official rating. You kids — your rules!";

  els.vibeBtns.forEach((btn) => {
    btn.classList.toggle("is-active", btn.dataset.bucket === bucket);
  });

  const seasons = [...new Set(data.episodes.map((e) => e.season))].sort((a, b) => Number(a) - Number(b));
  for (const s of seasons) {
    const opt = document.createElement("option");
    opt.value = String(s);
    opt.textContent = (s === 0 || s === '0') ? 'Other / specials 🎬' : `Season ${s} 🎬`;
    els.season.appendChild(opt);
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

  function matchesQuery(ep, q) {
    if (!q) return true;
    const details = watchDetailsOf(ep);
    const blob = [
      ep.title,
      ep.index_title,
      ep.code,
      ep.summary || "",
      ...watchThemesOf(ep),
      ...details.map((d) => `${d.theme} ${d.how || ""}`),
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

  function themeIndex() {
    const season = els.season.value;
    const counts = new Map();
    for (const ep of data.episodes) {
      if (season !== "all" && String(ep.season) !== season) continue;
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
      if (season !== "all" && String(ep.season) !== season) return false;
      if (!matchesThemes(ep)) return false;
      return matchesQuery(ep, q);
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
    const watchLis = details
      .map((d) => {
        const how = (d.how || "").trim();
        return `<li>
          <span class="theme-name">${escapeHtml(d.theme)}</span>${
            how
              ? `<span class="theme-sep" aria-hidden="true">—</span><span class="theme-how">${escapeHtml(how)}</span>`
              : ""
          }
        </li>`;
      })
      .join("");
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
    return `
      <article class="card card-${bKey}" style="animation-delay:${Math.min(i, 12) * 25}ms">
        <a class="card-hit" href="${href}" aria-label="Open ${escapeHtml(cleanTitle(ep.title))}">
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
            ${themeHtml}
          </div>
          ${notes}
        </a>
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

  function apply() {
    const season = els.season.value;
    const q = els.q.value.trim().toLowerCase();
    const conf = BUCKETS[bucket];

    let filtered = data.episodes.filter((ep) => {
      if (season !== "all" && String(ep.season) !== season) return false;
      if (!conf.match(ep)) return false;
      if (!matchesThemes(ep)) return false;
      return matchesQuery(ep, q);
    });

    // When filtering by themes, prefer theme-relevance ordering unless user picked another sort
    const sortMode =
      selectedThemes.size && els.sort.value === "air" ? "themes" : els.sort.value;
    filtered = sortEpisodes(filtered, sortMode);
    refreshCounts();

    const themeNote = selectedThemes.size
      ? ` · ${selectedThemes.size} theme${selectedThemes.size > 1 ? "s" : ""}`
      : "";
    els.hint.textContent = conf.hint;
    els.stats.textContent = `🎉 ${filtered.length} ${conf.stats}${themeNote}`;
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

  if (els.themeChips) {
    els.themeChips.addEventListener("click", (e) => {
      const btn = e.target.closest(".theme-chip");
      if (!btn) return;
      const theme = btn.dataset.theme;
      if (selectedThemes.has(theme)) selectedThemes.delete(theme);
      else selectedThemes.add(theme);
      renderThemeChips();
      apply();
    });
  }
  if (els.themeClear) {
    els.themeClear.addEventListener("click", () => {
      selectedThemes.clear();
      renderThemeChips();
      apply();
    });
  }

  for (const el of [els.season, els.q, els.sort]) {
    el.addEventListener("input", () => {
      if (el === els.season) renderThemeChips();
      apply();
    });
    el.addEventListener("change", () => {
      if (el === els.season) renderThemeChips();
      apply();
    });
  }

  setupReportFlow();
  renderThemeChips();
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

    reasonsEl.innerHTML = REASONS.map(
      (r) => `
      <label class="report-reason">
        <input type="radio" name="reason" value="${r.id}" />
        <span>${escapeHtml(r.label)}</span>
      </label>`
    ).join("");

    function openReport(ep) {
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
      requestAnimationFrame(() => {
        scrim.classList.add("is-on");
        sheet.classList.add("is-on");
        reasonsEl.querySelector("input")?.focus();
      });
    }

    function closeReport() {
      scrim.classList.remove("is-on");
      sheet.classList.remove("is-on");
      document.body.classList.remove("report-open");
      window.setTimeout(() => {
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
