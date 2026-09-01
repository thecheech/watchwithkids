(() => {
  const LABEL = {"2": "Mild", "3": "Caution", "4": "Too much"};
  const HINT = {"2": "Mild — passing mention or joke", "3": "Caution — preview or stay in the room", "4": "Too much — skip for younger kids"};
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

  function tier(score) {
    const s = Number(score) || 2;
    if (s <= 2) return 2;
    if (s === 3) return 3;
    return 4;
  }

  function rankClass(n) {
    if (n >= 4) return "severity-too-much";
    if (n === 3) return "severity-caution";
    return "severity-mild";
  }

  window.WWTK_SEVERITY = {
    label: LABEL,
    hint: HINT,
    score,
    tier(d) { return tier(score(d)); },
    rankClass,
  };
})();
