(() => {
  const boot = window.EP_PAGE;
  const root = document.getElementById("episode-root");
  if (!boot || !boot.episode || !root) {
    if (root) {
      root.innerHTML =
        "<p class='empty'>😅 Episode not found. <a href='../../index.html'>Back home</a></p>";
    }
    return;
  }

  const ep = boot.episode;
  const showId = boot.show_id;
  const showName = boot.show;
  const cover = boot.cover;

  const BUCKET_BADGE = {
    safe: { className: "bucket-pill safe", text: "✅ All clear" },
    maybe: { className: "bucket-pill maybe", text: "🤔 Gray area" },
    skip: { className: "bucket-pill skip", text: "🚫 Hard pass" },
  };

  function bucketOf(e) {
    if (e.overall <= 2) return "safe";
    if (e.overall === 3) return "maybe";
    return "skip";
  }

  function epLabel(e) {
    const epNum = String(e.episode).replace(/^0+/, "") || e.episode;
    if (e.season === 0 || e.season === "0") return `Ep ${epNum}`;
    return `S${e.season} E${epNum}`;
  }

  function signalOf(value) {
    if (value >= 4) return "stop";
    if (value === 3) return "caution";
    return "go";
  }

  function fitReadout(overall) {
    if (overall <= 2) return { label: "Mostly appropriate" };
    if (overall === 3) return { label: "Mixed — preview first" };
    return { label: "Leans inappropriate" };
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function cleanTitle(title) {
    return String(title).replace(/\s+/g, " ").trim();
  }

  function scoreBlock(emoji, label, value) {
    const signal = signalOf(value);
    const tip = `${label} ${value}/5`;
    return `
      <div class="score-block" data-tip="${escapeHtml(tip)}">
        <span class="score-label">${emoji} ${label}</span>
        <div class="semaphore signal-${signal} intensity-${value}" role="img" aria-label="${escapeHtml(tip)}">
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

  function fitMeterHtml(e) {
    const overall = Number(e.overall) || 1;
    const fit = ((overall - 1) / 4) * 0.84 + 0.08;
    const signal = signalOf(overall);
    const readout = fitReadout(overall);
    const themes = e.themes || { fine: [], watch: [] };
    const fineN = (themes.fine || []).length;
    const watchN = (themes.watch || []).length;
    const themeTotal = fineN + watchN;
    const watchShare = themeTotal ? watchN / themeTotal : fit;
    return `
      <div class="fit-meter signal-${signal}" style="--fit:${fit.toFixed(3)}; --watch:${watchShare.toFixed(3)}" role="img" aria-label="${escapeHtml(readout.label)}">
        <div class="fit-meter-top">
          <span class="fit-meter-kicker">Kid fit</span>
          <span class="fit-meter-readout">${escapeHtml(readout.label)}</span>
        </div>
        <div class="fit-track">
          <span class="fit-gradient" aria-hidden="true"></span>
          <span class="fit-balance" aria-hidden="true"></span>
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

  const bKey = bucketOf(ep);
  const badge = BUCKET_BADGE[bKey];
  const themes = ep.themes || { fine: [], watch: ep.examples || [] };
  const details =
    Array.isArray(themes.watch_detail) && themes.watch_detail.length
      ? themes.watch_detail
      : (themes.watch || []).map((theme) => ({ theme, how: "" }));
  const title = cleanTitle(ep.title);

  document.title = `${epLabel(ep)} · ${title} · ${showName}`;

  const prevHref = boot.prev ? `./${boot.prev}.html` : null;
  const nextHref = boot.next ? `./${boot.next}.html` : null;

  root.innerHTML = `
    <nav class="topnav wrap ep-nav">
      <a class="back-home" href="../../${escapeHtml(showId)}.html">← ${escapeHtml(showName)}</a>
      <a class="back-home subtle" href="../../index.html">All shows</a>
    </nav>

    <header class="ep-hero wrap">
      <div class="ep-hero-card">
        <div class="ep-hero-cover">
          <img src="${escapeHtml(cover)}" alt="" width="1920" height="1080" />
        </div>
        <div class="ep-hero-body">
          <div class="ep-meta">
            <span class="badge">🎞️ ${escapeHtml(epLabel(ep))}</span>
            <span class="${badge.className}">${escapeHtml(badge.text)}</span>
          </div>
          <p class="ep-show">${escapeHtml(showName)}</p>
          <h1>${escapeHtml(title)}</h1>
          ${ep.summary ? `<p class="summary">${escapeHtml(ep.summary)}</p>` : ""}
          ${fitMeterHtml(ep)}
        </div>
      </div>
    </header>

    <main class="wrap ep-main">
      <section class="ep-panel">
        <h2 class="ep-section-title">Content guide</h2>
        <div class="scores ep-scores" aria-label="Traffic-light content guide">
          ${scoreBlock("👊", "Violence", ep.violence)}
          ${scoreBlock("💋", "Sex", ep.sex)}
          ${scoreBlock("🙊", "Language", ep.language)}
          ${scoreBlock("⭐", "Overall", ep.overall)}
        </div>
        <p class="verdict-line">${escapeHtml(ep.verdict || "")}</p>
      </section>

      <section class="ep-panel">
        <h2 class="ep-section-title">Watch for</h2>
        <ul class="examples theme-watch-list">
          ${
            details.length
              ? details
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
                  .join("")
              : "<li>No watch-for themes flagged.</li>"
          }
        </ul>
        ${ep.notes ? `<p class="notes">📝 ${escapeHtml(ep.notes)}</p>` : ""}
      </section>

      <footer class="ep-actions">
        <div class="ep-pager">
          ${
            prevHref
              ? `<a class="ep-page-link" href="${prevHref}">← Prev</a>`
              : `<span class="ep-page-link is-disabled">← Prev</span>`
          }
          ${
            nextHref
              ? `<a class="ep-page-link" href="${nextHref}">Next →</a>`
              : `<span class="ep-page-link is-disabled">Next →</span>`
          }
        </div>
        <button
          type="button"
          class="report-trigger ep-report"
          data-code="${escapeHtml(ep.code)}"
          data-season="${escapeHtml(String(ep.season))}"
          data-episode="${escapeHtml(String(ep.episode))}"
          data-title="${escapeHtml(title)}"
          data-overall="${ep.overall}"
        >
          <svg class="report-ico" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none">
            <path d="M3.5 2.5v11M3.5 3.2h7.2c.7 0 1.1.8.7 1.4l-1.1 1.7c-.2.3-.2.7 0 1l1.1 1.7c.4.6 0 1.4-.7 1.4H3.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Report mistake</span>
        </button>
      </footer>
    </main>
  `;

  setupReportFlow({
    show: showName,
    show_id: showId,
    triggerRoot: root,
  });

  function setupReportFlow({ show, show_id, triggerRoot }) {
    const REASONS = [
      { id: "too-lenient", label: "Missed something inappropriate" },
      { id: "too-strict", label: "Rated too harsh" },
      { id: "wrong-score", label: "Wrong score (V / S / L)" },
      { id: "wrong-themes", label: "Themes or notes are off" },
      { id: "wrong-ep", label: "Wrong episode details" },
      { id: "other", label: "Something else" },
    ];

    const host = document.createElement("div");
    host.id = "report-root";
    host.innerHTML = `
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
            <textarea id="report-details" name="details" rows="3" maxlength="600" placeholder="A sentence is enough"></textarea>
            <p class="report-hint">No account needed. We read every report.</p>
            <div class="report-actions">
              <button type="button" class="report-btn-ghost" data-report-close>Cancel</button>
              <button type="submit" class="report-btn-solid" id="report-submit" disabled>Send report</button>
            </div>
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
    document.body.appendChild(host);

    const scrim = host.querySelector(".report-scrim");
    const sheet = host.querySelector(".report-sheet");
    const formView = host.querySelector('[data-report-view="form"]');
    const doneView = host.querySelector('[data-report-view="done"]');
    const epEl = host.querySelector("#report-ep");
    const reasonsEl = host.querySelector("#report-reasons");
    const form = host.querySelector("#report-form");
    const details = host.querySelector("#report-details");
    const submitBtn = host.querySelector("#report-submit");
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

    function openReport(target) {
      activeEp = target;
      reason = "";
      details.value = "";
      submitBtn.disabled = true;
      submitBtn.textContent = "Send report";
      form.querySelectorAll('input[name="reason"]').forEach((el) => {
        el.checked = false;
      });
      epEl.innerHTML = `<span class="report-ep-code">${escapeHtml(
        epLabel({ season: target.season, episode: target.episode })
      )}</span> · ${escapeHtml(target.title)}`;
      formView.hidden = false;
      doneView.hidden = true;
      scrim.hidden = false;
      sheet.hidden = false;
      document.body.classList.add("report-open");
      lastFocus = document.activeElement;
      requestAnimationFrame(() => {
        scrim.classList.add("is-on");
        sheet.classList.add("is-on");
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

    triggerRoot.addEventListener("click", (e) => {
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
    host.addEventListener("click", (e) => {
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
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending…";
      const payload = {
        show,
        show_id,
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
      } catch (_) {}
      try {
        await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (_) {}
      formView.hidden = true;
      doneView.hidden = false;
    });
  }
})();
