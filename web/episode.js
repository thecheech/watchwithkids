(() => {
  // Episode pages are rendered statically at build time (SEO + agents).
  // This script only wires up the "Report mistake" flow.
  const boot = window.EP_PAGE;
  const root = document.getElementById("episode-root");
  if (!boot || !root) return;

  const REASONS = [
    { id: "too-lenient", label: "Missed something inappropriate" },
    { id: "too-strict", label: "Rated too harsh" },
    { id: "wrong-score", label: "Wrong score (V / S / L)" },
    { id: "wrong-themes", label: "Themes or notes are off" },
    { id: "wrong-ep", label: "Wrong episode details" },
    { id: "other", label: "Something else" },
  ];

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function epLabel(e) {
    const epNum = String(e.episode).replace(/^0+/, "") || e.episode;
    if (String(e.season) === "0") return `Ep ${epNum}`;
    return `S${e.season} E${epNum}`;
  }

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
  const detailsEl = host.querySelector("#report-details");
  const submitBtn = host.querySelector("#report-submit");
  let activeEp = null;
  let reason = "";
  let lastFocus = null;
  let closeTimer = null;
  let focusTrapCleanup = null;

  function trapFocus(element) {
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    const focusableElements = element.querySelectorAll(focusableSelector);
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    function handleKeyDown(e) {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstFocusable) {
          e.preventDefault();
          lastFocusable.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          e.preventDefault();
          firstFocusable.focus();
        }
      }
    }

    element.addEventListener('keydown', handleKeyDown);
    return () => element.removeEventListener('keydown', handleKeyDown);
  }

  reasonsEl.innerHTML = REASONS.map(
    (r) => `
    <label class="report-reason">
      <input type="radio" name="reason" value="${r.id}" />
      <span>${escapeHtml(r.label)}</span>
    </label>`
  ).join("");

  function openReport(target) {
    if (closeTimer) {
      window.clearTimeout(closeTimer);
      closeTimer = null;
    }
    if (focusTrapCleanup) {
      focusTrapCleanup();
      focusTrapCleanup = null;
    }
    activeEp = target;
    reason = "";
    detailsEl.value = "";
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
    void sheet.offsetWidth;
    scrim.classList.add("is-on");
    sheet.classList.add("is-on");
    focusTrapCleanup = trapFocus(sheet);
    reasonsEl.querySelector("input")?.focus();
  }

  function closeReport() {
    if (focusTrapCleanup) {
      focusTrapCleanup();
      focusTrapCleanup = null;
    }
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

  root.addEventListener("click", (e) => {
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
      show: boot.show,
      show_id: boot.show_id,
      code: activeEp.code,
      season: activeEp.season,
      episode: activeEp.episode,
      title: activeEp.title,
      overall: activeEp.overall,
      reason,
      reason_label: REASONS.find((r) => r.id === reason)?.label || reason,
      details: detailsEl.value.trim().slice(0, 600),
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
})();
