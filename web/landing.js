(() => {
  const shows = window.SHOWS || [];
  const featured = document.getElementById("featured");
  const grid = document.getElementById("grid");
  const shelfCount = document.getElementById("shelf-count");
  const sparkles = document.getElementById("sparkles");

  const READY_ORDER = [
    "bluey",
    "spongebob",
    "phineas-and-ferb",
    "avatar",
    "gravity-falls",
    "adventure-time",
    "steven-universe",
    "kpop-demon-hunters",
    "full-house",
    "young-sheldon",
    "friends",
    "seinfeld",
    "the-office",
    "how-i-met-your-mother",
    "big-bang-theory",
    "malcolm-in-the-middle",
    "modern-family",
    "parks-and-recreation",
    "wednesday",
    "futurama",
    "rick-and-morty",
    "family-guy",
    "south-park",
  ];
  const SOON_ORDER = [
    "fresh-prince",
    "brooklyn-nine-nine",
    "simpsons",
    "bobs-burgers",
  ];

  const BLURBS = {
    friends: "Six friends, one couch — rated episode by episode.",
    seinfeld: "A show about nothing — with plenty of adult sitcom edges.",
    spongebob: "Bikini Bottom chaos. Mostly kid-safe; we flagged the exceptions.",
    bluey: "Blue Heeler family play — almost always all clear for little kids.",
    "phineas-and-ferb": "Summer inventions and Perry the Platypus — made for kids.",
    avatar: "Four nations, one Avatar — adventure with some wartime weight.",
    "gravity-falls": "Weird Oregon summer — spooky mystery, still a kids show.",
    "adventure-time": "Land of Ooo — silly on the surface, a few darker beats.",
    "steven-universe": "Crystal Gems and feelings — gentle, with heavy themes later.",
    "full-house": "Tanner family sitcom — mostly mild, occasional grown-up bits.",
    "the-office": "Scranton paper-company cringe — preview before little kids.",
    "how-i-met-your-mother": "Yellow umbrella, blue French horn — lots of adult dating plots.",
    "big-bang-theory": "Nerd sitcom with more innuendo than the science jokes suggest.",
    "young-sheldon": "Kid genius, Texas family — mostly mild, a few adult edges.",
    "malcolm-in-the-middle": "Dysfunctional family chaos — gray area more often than not.",
    "rick-and-morty": "Multiverse mayhem — almost always a hard pass for little kids.",
    "family-guy": "Cutaway gags and crude jokes — skip for the little ones.",
    "south-park": "Mountain-town satire — nearly every episode is a hard pass.",
    futurama: "31st-century delivery crew — lots of adult sci-fi comedy.",
    "parks-and-recreation": "Pawnee parks dept. — workplace sitcom with adult edges.",
    "modern-family": "Three families, one mockumentary — lots of grown-up plots.",
    wednesday: "Macabre Nevermore mystery — murder, monsters and deadpan dark humor.",
    "kpop-demon-hunters": "Pop stars by day, demon hunters by night — one animated movie, rated.",
  };

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
  const ready = READY_ORDER.map((id) => byId[id])
    .filter(Boolean)
    .sort((a, b) => {
      const [aN, aPct] = borderlineKey(a);
      const [bN, bPct] = borderlineKey(b);
      if (bN !== aN) return bN - aN;
      if (bPct !== aPct) return bPct - aPct;
      return String(a.name || "").localeCompare(String(b.name || ""));
    });
  const soon = SOON_ORDER.map((id) => byId[id]).filter(Boolean);

  if (featured && ready.length) {
    setupHeroSlideshow(featured, ready);
  }

  const liveGrid = document.getElementById("live-grid");
  if (liveGrid) {
    liveGrid.innerHTML = ready.map((s, i) => cardHtml(s, i, false)).join("");
  }

  if (shelfCount) shelfCount.textContent = `${soon.length} coming soon`;
  grid.innerHTML = soon.map((s, i) => cardHtml(s, i, true)).join("");

  const cards = [...document.querySelectorAll(".show-card")];
  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const el = entry.target;
        const i = Number(el.dataset.i || 0);
        el.style.animationDelay = `${(i % 6) * 55}ms`;
        el.classList.add("in-view");
        io.unobserve(el);
      }
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
  );
  cards.forEach((c) => io.observe(c));

  function setupHeroSlideshow(root, slides) {
    root.innerHTML = `
      <div class="feature-stage" aria-roledescription="carousel" aria-label="Rated shows">
        <div class="feature-slides"></div>
        <div class="feature-chrome">
          <div class="feature-copy">
            <h2 class="feature-title" id="feature-title"></h2>
            <p class="feature-blurb" id="feature-blurb"></p>
            <a class="cta" id="feature-cta" href="#">Browse episodes <span class="cta-arrow">→</span></a>
          </div>
          <div class="feature-dots" role="tablist" aria-label="Choose show"></div>
        </div>
        <div class="feature-progress" aria-hidden="true"><i></i></div>
      </div>
    `;

    const stage = root.querySelector(".feature-stage");
    const slidesEl = root.querySelector(".feature-slides");
    const titleEl = root.querySelector("#feature-title");
    const blurbEl = root.querySelector("#feature-blurb");
    const ctaEl = root.querySelector("#feature-cta");
    const dotsEl = root.querySelector(".feature-dots");
    const progress = root.querySelector(".feature-progress > i");

    slidesEl.innerHTML = slides
      .map(
        (s, i) => `
        <div class="feature-slide${i === 0 ? " is-active" : ""}" data-i="${i}" aria-hidden="${i === 0 ? "false" : "true"}">
          <img src="${s.coverLocal}" alt="" ${i === 0 ? 'loading="eager"' : 'loading="lazy"'} />
        </div>`
      )
      .join("");

    dotsEl.innerHTML = slides
      .map(
        (s, i) => `
        <button type="button" class="feature-dot${i === 0 ? " is-active" : ""}" role="tab" aria-selected="${i === 0 ? "true" : "false"}" aria-label="${escapeHtml(s.name)}" data-i="${i}"></button>`
      )
      .join("");

    let index = 0;
    let timer = null;
    let paused = false;
    let startedAt = 0;
    let remaining = SLIDE_MS;

    function paint(i, { resetProgress = true } = {}) {
      index = ((i % slides.length) + slides.length) % slides.length;
      const s = slides[index];
      slidesEl.querySelectorAll(".feature-slide").forEach((el, n) => {
        const on = n === index;
        el.classList.toggle("is-active", on);
        el.setAttribute("aria-hidden", on ? "false" : "true");
      });
      dotsEl.querySelectorAll(".feature-dot").forEach((el, n) => {
        const on = n === index;
        el.classList.toggle("is-active", on);
        el.setAttribute("aria-selected", on ? "true" : "false");
      });
      titleEl.textContent = s.name;
      blurbEl.textContent = BLURBS[s.id] || "";
      ctaEl.href = `${s.id}.html`;
      stage.dataset.show = s.id;
      if (resetProgress && progress) {
        progress.style.transition = "none";
        progress.style.transform = "scaleX(0)";
        // force reflow then animate
        void progress.offsetWidth;
        if (!reduceMotion && !paused) {
          progress.style.transition = `transform ${SLIDE_MS}ms linear`;
          progress.style.transform = "scaleX(1)";
        }
      }
    }

    function clearTimer() {
      if (timer) {
        window.clearTimeout(timer);
        timer = null;
      }
    }

    function schedule(delay = SLIDE_MS) {
      clearTimer();
      if (reduceMotion || slides.length < 2 || paused) return;
      remaining = delay;
      startedAt = performance.now();
      if (progress) {
        progress.style.transition = "none";
        const done = 1 - delay / SLIDE_MS;
        progress.style.transform = `scaleX(${Math.max(0, done)})`;
        void progress.offsetWidth;
        progress.style.transition = `transform ${delay}ms linear`;
        progress.style.transform = "scaleX(1)";
      }
      timer = window.setTimeout(() => {
        paint(index + 1);
        schedule(SLIDE_MS);
      }, delay);
    }

    function pause() {
      if (paused || reduceMotion) return;
      paused = true;
      clearTimer();
      if (startedAt) {
        const elapsed = performance.now() - startedAt;
        remaining = Math.max(400, remaining - elapsed);
      }
      if (progress) progress.style.transition = "none";
    }

    function resume() {
      if (!paused || reduceMotion) return;
      paused = false;
      schedule(remaining);
    }

    paint(0);
    schedule(SLIDE_MS);

    dotsEl.addEventListener("click", (e) => {
      const btn = e.target.closest(".feature-dot");
      if (!btn) return;
      paint(Number(btn.dataset.i));
      schedule(SLIDE_MS);
    });

    stage.addEventListener("pointerenter", pause);
    stage.addEventListener("pointerleave", resume);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) pause();
      else resume();
    });

    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    if (!reduceMotion && finePointer) {
      stage.addEventListener("pointermove", (e) => {
        const r = stage.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        stage.style.transform = `translateY(-4px) rotateX(${(-y * 3.5).toFixed(2)}deg) rotateY(${(x * 4.5).toFixed(2)}deg)`;
      });
      stage.addEventListener("pointerleave", () => {
        stage.style.transform = "";
      });
    }

    let swipeX = 0;
    stage.addEventListener("pointerdown", (e) => {
      swipeX = e.clientX;
    });
    stage.addEventListener("pointerup", (e) => {
      const dx = e.clientX - swipeX;
      if (Math.abs(dx) < 48) return;
      paint(index + (dx < 0 ? 1 : -1));
      schedule(SLIDE_MS);
    });
  }

  function cardHtml(s, i, soonMode) {
    const soon = soonMode || !s.ready;
    const tag = soon ? `<span class="status soon">Coming soon</span>` : "";
    const href = s.ready ? `${s.id}.html` : "#";
    const guideHref = s.ready ? `guides/${s.id}.html` : "";
    const cls = soon ? "show-card is-soon" : "show-card";
    const tagName = soon ? "div" : "a";
    const mix = s.mix;
    const scoreHtml =
      !soon && mix && mix.total ? safeScoreHtml(mix) : "";
    const guideHtml = guideHref ? guideChipHtml(guideHref, mix) : "";
    return `
      <${tagName} class="${cls}" data-i="${i}" ${soon ? "" : `href="${href}"`}>
        <img src="${s.coverLocal}" alt="${escapeHtml(s.name)}" loading="lazy" />
        <div class="shade"></div>
        ${tag}
        <div class="meta">
          <h3>${escapeHtml(s.name)}</h3>
          <p class="year">${escapeHtml(s.premiered || "")}${
            s.genres?.[0] ? ` · ${escapeHtml(s.genres[0])}` : ""
          }</p>
          ${scoreHtml}
          ${guideHtml}
        </div>
      </${tagName}>
    `;
  }

  /** Compact deep-link into the per-show guide — count, not a fat empty bar. */
  function guideChipHtml(guideHref, mix) {
    let label = "Episode guide →";
    if (mix && mix.total) {
      if (mix.safe > 0) {
        label = `${mix.safe} safe →`;
      } else if (mix.maybe > 0) {
        label = `${mix.maybe} to preview →`;
      } else if (mix.skip > 0) {
        label = `${mix.skip} hard pass →`;
      }
    }
    return `<span class="card-guide" data-guide="${guideHref}">${label}</span>`;
  }

  document.addEventListener("click", (e) => {
    const chip = e.target.closest(".card-guide");
    if (!chip) return;
    e.preventDefault();
    e.stopPropagation();
    const href = chip.getAttribute("data-guide");
    if (href) window.location.href = href;
  });

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
