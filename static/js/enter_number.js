// ---------------------------
// Enter number UX
// ---------------------------
// Flutter parity + production safe
// ---------------------------
(function () {
  const phoneInput = document.getElementById("phoneInput");
  const phoneE164 = document.getElementById("phoneE164");
  const countryCodeInput = document.getElementById("countryCode");
  const continueBtn = document.getElementById("continueBtn");
  const help = document.getElementById("phoneHelp");
  const cityImage = document.getElementById("cityImage");

  const countryBtn = document.getElementById("countryBtn");
  const countryFlag = document.getElementById("countryFlag");
  const modal = document.getElementById("countryModal");
  const list = document.getElementById("countryList");
  const search = document.getElementById("countrySearch");
  const contactBtn = document.getElementById("contactBtn");

  let COUNTRIES = [];
  let DIAL_INDEX = new Map();
  let MAX_DIAL_LEN = 4;
  let _isProgrammaticUpdate = false;

  let lookupTimer = null;
  let lookupRequestId = 0;
  let lastLookupKey = "";
  let lastLookupValid = false;

  // ---------------------------
  // Load countries
  // ---------------------------
  async function loadCountries() {
    try {
      const res = await fetch("/static/data/countries.json", { cache: "force-cache" });
      COUNTRIES = await res.json();

      buildDialIndex();
      setCountry(countryBtn?.dataset?.countryIso || "AF", { setPrefixIfEmpty: true });
      validateAndSync();
    } catch (e) {
      console.error("countries load error", e);
    }
  }

  function buildDialIndex() {
    DIAL_INDEX.clear();
    MAX_DIAL_LEN = 1;

    for (const c of COUNTRIES) {
      const digits = (c.dial || "").replace(/[^\d]/g, "");

      if (!digits) continue;

      if (!DIAL_INDEX.has(digits)) {
        DIAL_INDEX.set(digits, c);
      }

      if (digits.length > MAX_DIAL_LEN) {
        MAX_DIAL_LEN = digits.length;
      }
    }

    MAX_DIAL_LEN = Math.min(MAX_DIAL_LEN, 6);
  }

  // ---------------------------
  // Helpers
  // ---------------------------
  function digitsOnly(value) {
    return (value || "").replace(/[^\d]/g, "");
  }

  function sanitizeToE164(value) {
    let v = (value || "").trim();

    if (!v) return null;

    if (!v.startsWith("+")) {
      v = "+" + v;
    }

    v = "+" + v.slice(1).replace(/[^\d]/g, "");

    if (!/^\+\d+$/.test(v)) return null;

    const digits = digitsOnly(v);

    if (digits.length > 15) return null;

    return v;
  }

  function normalizeLeadingZero(phone) {
    const digits = digitsOnly(phone);
    const maxLen = Math.min(MAX_DIAL_LEN, digits.length);

    for (let len = maxLen; len >= 1; len--) {
      const code = digits.slice(0, len);
      const country = DIAL_INDEX.get(code);

      if (!country) continue;

      const rest = digits.slice(len);

      if (rest.startsWith("0")) {
        return "+" + code + rest.slice(1);
      }

      return phone;
    }

    return phone;
  }

  function syncHiddenE164(e164) {
    if (!phoneE164) return;
    phoneE164.value = e164 || "";
  }

  function syncCountryCode(dial) {
    if (!countryCodeInput) return;
    countryCodeInput.value = dial || "";
  }

  function getSelectedCountry() {
    const iso = countryBtn?.dataset?.countryIso || "AF";
    return COUNTRIES.find((x) => x.iso === iso || x.iso2 === iso) || null;
  }

  function getSelectedCountryDialDigits() {
    const country = getSelectedCountry();
    return digitsOnly(country?.dial || countryCodeInput?.value || "");
  }

  // ---------------------------
  // City image auto
  // ---------------------------
  function setCityByIso(iso) {
    if (!cityImage) return;

    const country = COUNTRIES.find((x) => (x.iso || x.iso2) === iso);
    const query = country ? country.name : "city";

    cityImage.src =
      "https://source.unsplash.com/1200x600/?city," +
      encodeURIComponent(query) +
      "&t=" + Date.now();
  }

// ---------------------------
// Display format
// ---------------------------
function formatForDisplay(e164) {

  if (!e164) {
    return "";
  }

  // supprimer les espaces
  return e164.replace(/\s+/g, "");

}

  // ---------------------------
  // Country
  // ---------------------------
  function setCountry(iso, opts = {}) {
    if (!COUNTRIES.length) return;

    const c = COUNTRIES.find((x) => x.iso === iso || x.iso2 === iso) || COUNTRIES[0];
    const isoVal = c.iso || c.iso2;

    if (countryBtn) {
      countryBtn.dataset.countryIso = isoVal;
    }

    if (countryFlag) {
      countryFlag.textContent = c.flag;
    }

    syncCountryCode(c.dial);
    setCityByIso(isoVal);

    if (opts.setPrefixIfEmpty && phoneInput) {
      const e164 = c.dial;

      _isProgrammaticUpdate = true;
      syncHiddenE164(e164);
      phoneInput.value = formatForDisplay(e164);
      phoneInput.setSelectionRange(phoneInput.value.length, phoneInput.value.length);
      _isProgrammaticUpdate = false;
    }
  }

  // ---------------------------
  // UI states
  // ---------------------------
  function setContinueDisabled(disabled) {
    if (!continueBtn) return;
    continueBtn.disabled = !!disabled;
    continueBtn.setAttribute("aria-disabled", disabled ? "true" : "false");
  }

  function showEmpty() {
    setContinueDisabled(true);

    if (help) {
      help.classList.remove("tz-help--ok", "tz-help--error");
      help.classList.add("tz-help--muted");
      help.textContent = help.dataset.empty || "";
    }

    phoneInput?.classList.remove("tz-input--error");
  }

  function showValid(operatorName) {
    setContinueDisabled(false);

    if (help) {
      help.classList.remove("tz-help--error", "tz-help--muted");
      help.classList.add("tz-help--ok");

      if (operatorName) {
        help.textContent = "✓ " + operatorName;
      } else {
        help.textContent = help.dataset.valid || "";
      }
    }

    phoneInput?.classList.remove("tz-input--error");
  }

  function showInvalid() {
    setContinueDisabled(true);

    if (help) {
      help.classList.remove("tz-help--ok", "tz-help--muted");
      help.classList.add("tz-help--error");
      help.textContent = help.dataset.invalid || "";
    }

    phoneInput?.classList.add("tz-input--error");
  }

  function showChecking() {
    setContinueDisabled(true);

    if (help) {
      help.classList.remove("tz-help--ok", "tz-help--error");
      help.classList.add("tz-help--muted");
      help.textContent = help.dataset.valid || "";
    }

    phoneInput?.classList.remove("tz-input--error");
  }

  // ---------------------------
  // Reloadly phone detection
  // ---------------------------
async function tzLookupNumber() {

  if (!phoneInput) return;

  const phone = phoneE164?.value || "";

  // utiliser ISO pays (AF, FR, etc.)
  const country = countryBtn?.dataset?.countryIso || "AF";

  if (!phone || !country) {
    lastLookupValid = false;
    setContinueDisabled(true);
    return;
  }

  const digits = digitsOnly(phone);

  if (digits.length < 7) {
    lastLookupValid = false;
    setContinueDisabled(true);
    return;
  }

    const lookupKey = `${phone}|${country}`;

    if (lookupKey === lastLookupKey && lastLookupValid) {
      showValid();
      return;
    }

    const requestId = ++lookupRequestId;
    showChecking();

    try {
      const res = await fetch("/recharge/api/lookup-number", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          phone: phone,
          country: country
        })
      });

      let data = {};
      try {
        data = await res.json();
      } catch (e) {
        data = {};
      }

      if (requestId !== lookupRequestId) {
        return;
      }

      if (res.ok && data.valid) {
        lastLookupKey = lookupKey;
        lastLookupValid = true;
        showValid(data.operatorName || "");
      } else {
        lastLookupKey = lookupKey;
        lastLookupValid = false;
        showInvalid();
      }
    } catch (e) {
      if (requestId !== lookupRequestId) {
        return;
      }

      lastLookupKey = lookupKey;
      lastLookupValid = false;
      showInvalid();
    }
  }

  function scheduleLookup() {
    clearTimeout(lookupTimer);

    lookupTimer = setTimeout(() => {
      tzLookupNumber();
    }, 350);
  }

// ---------------------------
// Validation
// ---------------------------
function validateAndSync() {

  if (!phoneInput) return;

  const rawValue = phoneInput.value.trim();

  // champ vide
  if (!rawValue) {
    lastLookupValid = false;
    showEmpty();
    return;
  }

  const rawE164 = sanitizeToE164(rawValue);

  // numéro impossible
  if (rawE164 === null) {
    lastLookupValid = false;
    showInvalid();
    return;
  }

  const e164 = normalizeLeadingZero(rawE164);

  // synchroniser le champ caché
  syncHiddenE164(e164);

  const display = formatForDisplay(e164);

  if (phoneInput.value !== display) {
    _isProgrammaticUpdate = true;
    phoneInput.value = display;
    _isProgrammaticUpdate = false;
  }

  const digits = digitsOnly(e164);

// ---------------------------
// longueur valide internationale
// ---------------------------
const validLength = digits.length >= 9 && digits.length <= 15;

if (!validLength) {
  lastLookupValid = false;
  showInvalid();
  return;
}

// lancer la détection opérateur
scheduleLookup();

} // ← fermer validateAndSync ici


// ---------------------------
// Modal
// ---------------------------
function openModal() {
    if (!modal) return;

    modal.style.display = "block";
    renderList("");

    setTimeout(() => {
      search?.focus();
    }, 50);
  }

  function closeModal() {
    if (!modal) return;
    modal.style.display = "none";
  }

  function renderList(q) {
    if (!COUNTRIES.length || !list) return;

    const query = (q || "").toLowerCase();
    list.innerHTML = "";

    const filtered = COUNTRIES.filter((c) => {
      return c.name.toLowerCase().includes(query) || c.dial.includes(query);
    });

    for (const c of filtered) {
      const row = document.createElement("button");

      row.type = "button";
      row.className = "tz-country-row";
      row.innerHTML = `
        <span class="tz-flag">${c.flag}</span>
        <span class="tz-grow">${c.name}</span>
        <span class="tz-muted">${c.dial}</span>
      `;

      row.onclick = () => {
        setCountry(c.iso || c.iso2, { setPrefixIfEmpty: true });
        closeModal();
        lastLookupKey = "";
        lastLookupValid = false;
        validateAndSync();
      };

      list.appendChild(row);
    }
  }

  // ---------------------------
  // Events
  // ---------------------------
  phoneInput?.addEventListener("input", () => {
    if (_isProgrammaticUpdate) return;

    lastLookupKey = "";
    lastLookupValid = false;
    validateAndSync();
  });

  phoneInput?.addEventListener("blur", () => {
    tzLookupNumber();
  });

  countryBtn?.addEventListener("click", openModal);

  search?.addEventListener("input", (e) => {
    renderList(e.target.value);
  });

  modal?.addEventListener("click", (e) => {
    if (e.target.classList.contains("tz-modal__backdrop")) {
      closeModal();
    }
  });

  contactBtn?.addEventListener("click", async () => {
    if (!("contacts" in navigator && "select" in navigator.contacts)) {
      const message = contactBtn.dataset.unavailableMessage || "";
      if (message) {
        alert(message);
      }
      return;
    }

    try {
      const contacts = await navigator.contacts.select(["tel"], { multiple: false });

      if (contacts.length && contacts[0].tel?.length) {
        phoneInput.value = contacts[0].tel[0];
        lastLookupKey = "";
        lastLookupValid = false;
        validateAndSync();
      }
    } catch (e) {
      console.log("contact cancelled");
    }
  });

  const form = phoneInput?.closest("form");

  if (form) {
    form.addEventListener("submit", (e) => {
      if (phoneE164 && !phoneE164.value) {
        const e164 = sanitizeToE164(phoneInput.value);
        if (e164) {
          phoneE164.value = normalizeLeadingZero(e164);
        }
      }

      if (!lastLookupValid) {
        e.preventDefault();
        tzLookupNumber();
      }
    });
  }

  // ---------------------------
  // Init
  // ---------------------------
  loadCountries();

  // expose modal functions to HTML
  window.openModal = openModal;
  window.closeModal = closeModal;
})();