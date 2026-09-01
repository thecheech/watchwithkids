(() => {
  const shows = window.SHOWS || [];
  const featured = document.getElementById("featured");
  const sparkles = document.getElementById("sparkles");

  const READY_ORDER = [
    "friends",
    "seinfeld",
    "the-office",
    "how-i-met-your-mother",
    "big-bang-theory",
    "young-sheldon",
    "malcolm-in-the-middle",
    "modern-family",
    "parks-and-recreation",
    "brooklyn-nine-nine",
    "bobs-burgers",
    "simpsons",
    "futurama",
    "fresh-prince",
    "full-house",
    "wednesday",
    "stranger-things",
  ];
  /** Made-for-kids — separate shelf so Bluey isn't next to South Park. */
  const KIDS_ORDER = [
    "bluey",
    "spongebob",
    "phineas-and-ferb",
    "avatar",
    "gravity-falls",
    "adventure-time",
    "steven-universe",
    "legend-of-korra",
    "clone-wars",
    "owl-house",
    "amphibia",
    "pokemon",
    "kpop-demon-hunters",
  ];
  /** TV-MA / adult animation — rated so you know which episodes are roughest. */
  const ADULT_ORDER = ["rick-and-morty", "family-guy", "south-park"];
  // Empty - all shows with ratings are now in one of the shelves above
  const SOON_ORDER = [];

  const SLIDE_MS = 4000;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (sparkles) {
    const n = reduceMotion ? 0 : 18;
    for (let i = 0; i < n; i++) {
      const s = document.createElement("span");
      s.style.left = `${Math.random() * 100}%`;
      s.style.top = `${Math.random() * 100}%`;
      s.style.setProperty("--dur", `${2.4 + Math.random() * 3.5}s`);
      s.style.animationDelay = `${Math.random() * 4}s`;
      sparkles.appendChild(s);
    }
  }

  const byId = Object.fromEntries(shows.map((s) => [s.id, s]));
  /** Lead with gray-area-heavy shows (Friends, etc.), not the all-clear cartoons. */
  function borderlineKey(s) {
    const mix = s.mix || {};
    const total = mix.total || 0;
    const maybe = mix.maybe || 0;
    return [maybe, total ? maybe / total : 0];
  }
  function ordered(ids) {
    return ids.map((id) => byId[id]).filter(Boolean);
  }
  function byBorderline(list) {
    return [...list].sort((a, b) => {
      const [aN, aPct] = borderlineKey(a);
      const [bN, bPct] = borderlineKey(b);
      if (bN !== aN) return bN - aN;
      if (bPct !== aPct) return bPct - aPct;
      return String(a.name || "").localeCompare(String(b.name || ""));
    });
  }
  const ready = byBorderline(ordered(READY_ORDER));
  const kids = ordered(KIDS_ORDER);
  const adult = ordered(ADULT_ORDER);
  const soon = SOON_ORDER.map((id) => byId[id]).filter(Boolean);
  const HERO_SHOWS = ["friends", "the-office", "modern-family", "big-bang-theory", "seinfeld", "parks-and-recreation"];
  const heroSlides = ordered(HERO_SHOWS);

  if (featured && heroSlides.length) {
    setupHeroTv(featured, heroSlides);
  }

  const liveGrid = document.getElementById("live-grid");
  if (liveGrid) {
    liveGrid.innerHTML = ready.map((s, i) => cardHtml(s, i, false)).join("");
  }

  const kidsGrid = document.getElementById("kids-grid");
  if (kidsGrid) {
    kidsGrid.innerHTML = kids.map((s, i) => cardHtml(s, i, false)).join("");
  }

  const adultGrid = document.getElementById("adult-grid");
  if (adultGrid) {
    adultGrid.innerHTML = adult.map((s, i) => cardHtml(s, i, false)).join("");
  }

  if (soon.length) {
    const shelf = document.createElement("section");
    shelf.className = "shelf";
    shelf.innerHTML = `
      <div class="shelf-head reveal">
        <div>
          <h2>More shows on the shelf</h2>
          <p>Covers up. Ratings rolling out show by show.</p>
        </div>
        <div class="count-chip" id="shelf-count">${soon.length} coming soon</div>
      </div>
      <div class="grid" id="grid"></div>
    `;
    document.querySelector("main.wrap, main")?.appendChild(shelf);
    shelf.querySelector("#grid").innerHTML = soon.map((s, i) => cardHtml(s, i, true)).join("");
  }

  const cards = [...document.querySelectorAll(".show-card")];

  function revealCard(el) {
    if (el.classList.contains("in-view")) return;
    el.classList.add("in-view");
    io?.unobserve(el);
  }

  function revealVisibleCards() {
    const vh = window.innerHeight || document.documentElement.clientHeight || 0;
    for (const el of cards) {
      if (el.classList.contains("in-view")) continue;
      const r = el.getBoundingClientRect();
      if (r.width <= 0 && r.height <= 0) continue;
      if (r.bottom > 0 && r.top < vh) revealCard(el);
    }
  }

  let io = null;
  if (!reduceMotion && cards.length) {
    document.documentElement.classList.add("js-scroll-reveal");
    io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) revealCard(entry.target);
        }
      },
      { rootMargin: "64px 0px 64px 0px", threshold: 0 }
    );
    cards.forEach((c) => io.observe(c));
    revealVisibleCards();
    requestAnimationFrame(revealVisibleCards);
    window.addEventListener("load", revealVisibleCards, { once: true });
    window.addEventListener(
      "scroll",
      () => {
        if (revealVisibleCards._t) return;
        revealVisibleCards._t = window.setTimeout(() => {
          revealVisibleCards._t = 0;
          revealVisibleCards();
        }, 120);
      },
      { passive: true }
    );
    window.setTimeout(revealVisibleCards, 1500);
  } else {
    cards.forEach((c) => c.classList.add("in-view"));
  }

  function setupHeroTv(root, slides) {
    root.innerHTML = `
      <div class="hero-tv">
        <div class="hero-tv-bezel">
          <div class="hero-tv-screen">
            <div class="feature-slides"></div>
          </div>
          <div class="hero-tv-chin" aria-hidden="true"><span class="hero-tv-led"></span></div>
        </div>
        <div class="hero-tv-neck" aria-hidden="true"></div>
        <div class="hero-tv-base" aria-hidden="true"></div>
      </div>
    `;

    const slidesEl = root.querySelector(".feature-slides");
    slidesEl.innerHTML = slides
      .map(
        (s, i) => `
        <a class="feature-slide${i === 0 ? " is-active" : ""}" href="${s.id}.html" data-i="${i}" aria-label="${escapeHtml(s.name)}" aria-hidden="${i === 0 ? "false" : "true"}"${i === 0 ? "" : ' tabindex="-1"'}>
          <img src="${s.coverLocal}" alt="" width="${s.coverW || 1920}" height="${s.coverH || 1080}" ${i === 0 ? 'fetchpriority="high" loading="eager"' : 'loading="lazy"'} />
        </a>`
      )
      .join("");

    let index = 0;
    let timer = null;

    function paint(i) {
      index = ((i % slides.length) + slides.length) % slides.length;
      slidesEl.querySelectorAll(".feature-slide").forEach((el, n) => {
        const on = n === index;
        el.classList.toggle("is-active", on);
        el.setAttribute("aria-hidden", on ? "false" : "true");
        if (on) el.removeAttribute("tabindex");
        else el.setAttribute("tabindex", "-1");
      });
    }

    function schedule() {
      if (timer) window.clearTimeout(timer);
      if (reduceMotion || slides.length < 2) return;
      timer = window.setTimeout(() => {
        paint(index + 1);
        schedule();
      }, SLIDE_MS);
    }

    paint(0);
    schedule();

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        if (timer) window.clearTimeout(timer);
        timer = null;
      } else {
        schedule();
      }
    });
  }

  function cardHtml(s, i, soonMode) {
    const soon = soonMode || !s.ready;
    const tag = soon ? `<span class="status soon">Coming soon</span>` : "";
    const href = s.ready ? `${s.id}.html` : "#";
    const cls = soon ? "show-card is-soon" : "show-card";
    const tagName = soon ? "div" : "a";
    const mix = s.mix;
    const scoreHtml =
      !soon && mix && mix.total ? safeScoreHtml(mix) : "";
    return `
      <${tagName} class="${cls}" data-i="${i}" ${soon ? "" : `href="${href}"`}>
        <img src="${s.coverLocal}" alt="${escapeHtml(s.name)}" width="${s.coverW || 1920}" height="${s.coverH || 1080}" loading="lazy" />
        <div class="shade"></div>
        ${tag}
        <div class="meta">
          <h3>${escapeHtml(s.name)}</h3>
          <p class="year">${escapeHtml(s.premiered || "")}${
            s.genres?.[0] ? ` · ${escapeHtml(s.genres[0])}` : ""
          }</p>
          ${scoreHtml}
        </div>
      </${tagName}>
    `;
  }

  /** Episode mix: Safe (≤2) / Borderline (3) / Hard Pass (≥4). */
  function safeScoreHtml(mix) {
    const total = mix.total || 0;
    if (!total) return "";
    let safePct = Math.round((100 * mix.safe) / total);
    let maybePct = Math.round((100 * mix.maybe) / total);
    let skipPct = Math.max(0, 100 - safePct - maybePct);
    // Keep visual bar in sync if rounding overflowed
    if (safePct + maybePct > 100) {
      maybePct = Math.max(0, 100 - safePct);
      skipPct = 0;
    }
    const parts = [
      { key: "safe", pct: safePct, label: "Safe", count: mix.safe },
      { key: "maybe", pct: maybePct, label: "Borderline", count: mix.maybe },
      { key: "skip", pct: skipPct, label: "Hard Pass", count: mix.skip },
    ];
    const legend = parts
      .filter((p) => p.pct > 0 || p.count > 0)
      .map(
        (p) =>
          `<span class="mix-leg mix-leg--${p.key}"><strong>${p.pct}%</strong> ${p.label}</span>`
      )
      .join("");
    const aria = parts.map((p) => `${p.pct}% ${p.label}`).join(", ");
    return `<div class="mix-score" title="${mix.safe} clear · ${mix.maybe} gray · ${mix.skip} hard pass of ${total}" aria-label="${aria}">
      <div class="mix-bar" style="--safe:${safePct}%;--maybe:${maybePct}%;--skip:${skipPct}%">
        <span class="mix-seg mix-seg--safe" style="flex-grow:${safePct}"></span>
        <span class="mix-seg mix-seg--maybe" style="flex-grow:${maybePct}"></span>
        <span class="mix-seg mix-seg--skip" style="flex-grow:${skipPct}"></span>
      </div>
      <div class="mix-legend">${legend}</div>
    </div>`;
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }
})();
