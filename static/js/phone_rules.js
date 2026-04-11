// ---------------------------
// Generate rules for ALL countries
// ---------------------------
window.TZ_PHONE_RULES = {};

fetch("/static/data/countries.json")
  .then(r => r.json())
  .then(countries => {
    countries.forEach(c => {
      const iso = (c.iso || c.iso2 || "").toLowerCase();
      if (!iso) return;

      // default rule (safe fallback)
      window.TZ_PHONE_RULES[iso] = { min: 6, max: 12 };
    });

    // ---------------------------
    // Overrides (manual)
    // ---------------------------
    Object.assign(window.TZ_PHONE_RULES, {

      af: { min: 9, max: 9 },   // Afghanistan
      fr: { min: 9, max: 9 },   // France
      tr: { min: 10, max: 10 }, // Turkey
      us: { min: 10, max: 10 },
      ca: { min: 10, max: 10 },
      gb: { min: 10, max: 10 },
      dz: { min: 9, max: 9 },
      ma: { min: 9, max: 9 },
      tn: { min: 8, max: 8 }

    });
  });