/* ---------------------------
   Tikzok — Country Picker (modal)
   - Charge la liste des pays depuis /static/data/countries.json
   - Remplit le modal
   - Sélection -> met à jour flag + iso + dial
--------------------------- */

(function () {
  "use strict";

  const MODAL_ID = "countryModal";
  const LIST_ID = "countryList";
  const SEARCH_ID = "countrySearch";

  const BTN_ID = "countryBtn";
  const FLAG_ID = "countryFlag";

  const HIDDEN_DIAL_ID = "countryCode";
  const PHONE_ID = "phoneInput";
  const CITY_IMG_ID = "cityImage";

  let _countries = [];
  let _filtered = [];
  let _loaded = false;

  // ---------------------------
  // Helpers
  // ---------------------------
  function byId(id) {
    return document.getElementById(id);
  }

  function normalizeStr(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function safeIso(iso) {
    const v = String(iso || "").toLowerCase();
    return v.match(/^[a-z]{2}$/) ? v : "fr";
  }

  function setCityImage(iso) {
    const img = byId(CITY_IMG_ID);
    if (!img) return;
    const safe = safeIso(iso);
    const base = img.getAttribute("data-base") || ""; // optionnel si tu veux plus tard
    // On garde la même convention que ton template
    img.src = `/static/images/cities/${safe}.jpg`;
  }

  function setSelectedCountry(country) {
    const btn = byId(BTN_ID);
    const flag = byId(FLAG_ID);
    const hiddenDial = byId(HIDDEN_DIAL_ID);

    if (btn) btn.dataset.countryIso = country.iso2.toLowerCase();
    if (flag) flag.textContent = country.flag;

    if (hiddenDial) hiddenDial.value = country.dial;

    // UX: met à jour l’image
    setCityImage(country.iso2);

    // Sélection visuelle dans la liste
    const list = byId(LIST_ID);
    if (list) {
      list.querySelectorAll(".tz-country-row.is-selected").forEach((el) => {
        el.classList.remove("is-selected");
      });
      const selected = list.querySelector(`[data-iso="${country.iso2.toLowerCase()}"]`);
      if (selected) selected.classList.add("is-selected");
    }
  }

  function renderList(items) {
    const list = byId(LIST_ID);
    if (!list) return;

    const currentIso = (byId(BTN_ID)?.dataset.countryIso || "fr").toLowerCase();
    const frag = document.createDocumentFragment();

    items.forEach((c) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tz-country-row";
      btn.dataset.iso = c.iso2.toLowerCase();
      btn.dataset.dial = c.dial;

      if (btn.dataset.iso === currentIso) btn.classList.add("is-selected");

      // Aucun texte UI “hardcodé” : ici ce sont des données pays
      btn.innerHTML = `
        <span class="tz-flag" aria-hidden="true">${c.flag}</span>
        <span class="tz-grow" style="text-align:left;min-width:0;">
          <span class="tz-strong" style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${c.name}</span>
          <span class="tz-muted tz-small" style="display:block;">${c.iso2.toUpperCase()} · ${c.dial}</span>
        </span>
      `;

      btn.addEventListener("click", () => {
        setSelectedCountry(c);

        // UX Flutter-like: quand on choisit un pays, on remplace le contenu par le dial
        const phone = byId(PHONE_ID);
        if (phone) {
          phone.value = c.dial;
          phone.dispatchEvent(new Event("input", { bubbles: true }));
          phone.focus();
        }

        window.tzCloseCountryModal();
      });

      frag.appendChild(btn);
    });

    list.innerHTML = "";
    list.appendChild(frag);
  }

  async function loadCountriesOnce() {
    if (_loaded) return;

    // JSON local (production): pas de dépendance externe
    const res = await fetch("/static/data/countries.json", { cache: "force-cache" });
    if (!res.ok) throw new Error("countries.json not found");
    const data = await res.json();

    // Attendu: [{ iso2:"FR", dial:"+33", flag:"🇫🇷", name:"France" }, ...]
    _countries = Array.isArray(data) ? data : [];
    _filtered = _countries.slice();
    _loaded = true;
  }

  function filterCountries() {
    const q = normalizeStr(byId(SEARCH_ID)?.value || "");
    if (!q) {
      _filtered = _countries.slice();
      renderList(_filtered);
      return;
    }

    _filtered = _countries.filter((c) => {
      const hay = normalizeStr(`${c.name} ${c.iso2} ${c.dial}`);
      return hay.includes(q);
    });

    renderList(_filtered);
  }

  // ---------------------------
  // Public API used by template
  // ---------------------------
  window.tzOpenCountryModal = async function () {
    const modal = byId(MODAL_ID);
    if (!modal) return;

    try {
      await loadCountriesOnce();
      renderList(_countries);
      _loaded = true;
    } catch (e) {
      // Si le JSON n’existe pas: on ouvre quand même (liste vide)
      const list = byId(LIST_ID);
      if (list) list.innerHTML = "";
    }

    modal.classList.add("tz-modal--open");

    // focus search
    const search = byId(SEARCH_ID);
    if (search) {
      search.value = "";
      search.focus();
    }

    // close on ESC
    document.addEventListener("keydown", onKeydown);
  };

  window.tzCloseCountryModal = function () {
    const modal = byId(MODAL_ID);
    if (!modal) return;
    modal.classList.remove("tz-modal--open");
    document.removeEventListener("keydown", onKeydown);
  };

  window.tzFilterCountries = function () {
    if (!_loaded) return;
    filterCountries();
  };

  function onKeydown(e) {
    if (e.key === "Escape") window.tzCloseCountryModal();
  }

  // ---------------------------
  // Init: si page déjà avec iso/dial, on synchronise l'image
  // ---------------------------
  document.addEventListener("DOMContentLoaded", () => {
    const iso = (byId(BTN_ID)?.dataset.countryIso || "fr").toLowerCase();
    setCityImage(iso);
  });
})();