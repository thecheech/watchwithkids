(() => {
  const LABEL = {"1": "Clear", "2": "Mild", "3": "Gray area", "4": "Spicy", "5": "Adults only"};
  const HINT = {"1": "All clear — nothing to worry about", "2": "Mild — passing mention or joke", "3": "Gray area — preview or stay in the room", "4": "Spicy — skip for younger kids", "5": "Adults only — hard pass for kids"};
  const FROM_INTENSITY = {1: 2, 2: 3, 3: 4};

  function score(d) {
    const stored = Number(d?.severity);
    if (stored >= 1 && stored <= 5) return stored;
    const sev = Number(d?.sev);
    if (sev >= 5) return 5;
    if (sev >= 4) return 4;
    if (sev === 3) return 3;
    if (sev === 1 || sev === 2) return 2;
    return FROM_INTENSITY[Number(d?.intensity) || 1] || 2;
  }

  function rankClass(n) {
    if (n >= 5) return "severity-adult";
    if (n >= 4) return "severity-spicy";
    if (n === 3) return "severity-gray";
    if (n <= 1) return "severity-clear";
    return "severity-mild";
  }

  window.WWTK_SEVERITY = { label: LABEL, hint: HINT, score, rankClass };
})();
