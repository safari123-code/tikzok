// ---------------------------
// Tikzok — Country Picker (modal)
// ---------------------------
// UI only
// Single source of truth stays in enter_number.js
// ---------------------------
(function () {
  "use strict";

  const MODAL_ID = "countryModal";
  const LIST_ID = "countryList";
  const SEARCH_ID = "countrySearch";
  const BTN_ID = "countryBtn";

  let countries = [];
  let loaded = false;

  // ---------------------------
  // Helpers
  // ---------------------------
  function byId(id) {
    return document.getElementById(id);
  }

  function normalizeStr(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .trim();
  }

  function sanitizeIso(value) {
    const iso = String(value || "").trim().toLowerCase();
    return /^[a-z]{2}$/.test(iso) ? iso : "fr";
  }

  function getCountriesPromise() {
    if (!window.__tzCountriesPromise) {
      window.__tzCountriesPromise = fetch("/static/data/countries.json", {
        cache: "force-cache"
      }).then((res) => {
        if (!res.ok) {
          throw new Error("countries.json not found");
        }
        return res.json();
      });
    }

    return window.__tzCountriesPromise;
  }

  async function loadCountriesOnce() {
    if (loaded) {
      return;
    }

    const data = await getCountriesPromise();
    countries = Array.isArray(data) ? data : [];
    loaded = true;
  }

  function getCurrentIso() {
    return sanitizeIso(byId(BTN_ID)?.dataset?.countryIso || "fr");
  }

  function dispatchCountrySelected(country) {
    document.dispatchEvent(new CustomEvent("tz:country-selected", {
      detail: { country }
    }));
  }

  function buildCountryRow(country) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tz-country-row";
    btn.dataset.iso = sanitizeIso(country.iso || country.iso2);

    if (btn.dataset.iso === getCurrentIso()) {
      btn.classList.add("is-selected");
    }

    btn.innerHTML = `
      <span class="tz-flag" aria-hidden="true">${country.flag || ""}</span>
      <span class="tz-grow" style="text-align:left;min-width:0;">
        <span class="tz-strong" style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
          ${country.name || ""}
        </span>
        <span class="tz-muted tz-small" style="display:block;">
          ${(country.iso2 || country.iso || "").toUpperCase()} · ${country.dial || ""}
        </span>
      </span>
    `;

    btn.addEventListener("click", () => {
      dispatchCountrySelected(country);
      window.tzCloseCountryModal();
    });

    return btn;
  }

  function renderList(query) {
    const list = byId(LIST_ID);
    if (!list) {
      return;
    }

    const q = normalizeStr(query);
    const items = !q
      ? countries
      : countries.filter((country) => {
          const haystack = normalizeStr(
            `${country.name || ""} ${country.iso2 || country.iso || ""} ${country.dial || ""}`
          );
          return haystack.includes(q);
        });

    const fragment = document.createDocumentFragment();

    for (const country of items) {
      fragment.appendChild(buildCountryRow(country));
    }

    list.innerHTML = "";
    list.appendChild(fragment);
  }

  function onKeydown(e) {
    if (e.key === "Escape") {
      window.tzCloseCountryModal();
    }
  }

  // ---------------------------
  // Public API
  // ---------------------------
  window.tzOpenCountryModal = async function () {
    const modal = byId(MODAL_ID);
    const search = byId(SEARCH_ID);
    const list = byId(LIST_ID);

    if (!modal) {
      return;
    }

    try {
      await loadCountriesOnce();
      renderList("");
    } catch (e) {
      if (list) {
        list.innerHTML = "";
      }
    }

    modal.style.display = "block";
    modal.setAttribute("aria-hidden", "false");
    modal.classList.add("tz-modal--open");

    if (search) {
      search.value = "";
      setTimeout(() => search.focus(), 30);
    }

    document.addEventListener("keydown", onKeydown);
  };

  window.tzCloseCountryModal = function () {
    const modal = byId(MODAL_ID);
    if (!modal) {
      return;
    }

    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    modal.classList.remove("tz-modal--open");
    document.removeEventListener("keydown", onKeydown);
  };

  window.tzFilterCountries = function () {
    const search = byId(SEARCH_ID);
    renderList(search?.value || "");
  };

  // ---------------------------
  // Init
  // ---------------------------
  document.addEventListener("DOMContentLoaded", () => {
    const search = byId(SEARCH_ID);
    const modal = byId(MODAL_ID);

    search?.addEventListener("input", () => {
      window.tzFilterCountries();
    });

    modal?.addEventListener("click", (e) => {
      if (e.target.classList.contains("tz-modal__backdrop")) {
        window.tzCloseCountryModal();
      }
    });
  });
})();