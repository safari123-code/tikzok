// ---------------------------
// Enter number UX (FINAL STABLE + Formatting)
// Flutter parity + production safe
// ---------------------------
(function () {

  const phoneInput = document.getElementById("phoneInput");
  const phoneE164 = document.getElementById("phoneE164");
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

  // ================= LOAD COUNTRIES =================
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

      if (!DIAL_INDEX.has(digits)) DIAL_INDEX.set(digits, c);

      if (digits.length > MAX_DIAL_LEN) MAX_DIAL_LEN = digits.length;

    }

    MAX_DIAL_LEN = Math.min(MAX_DIAL_LEN, 6);

  }

  // ================= HELPERS =================
  function digitsOnly(s) {

    return (s || "").replace(/[^\d]/g, "");

  }

  function sanitizeToE164(value) {

    let v = (value || "").trim();

    if (!v.startsWith("+")) v = "+" + v;

    v = "+" + v.slice(1).replace(/[^\d]/g, "");

    if (!/^\+\d+$/.test(v)) return null;

    const d = digitsOnly(v);

    if (d.length > 15) return null;

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

      if (rest.startsWith("0")) return "+" + code + rest.slice(1);

      return phone;

    }

    return phone;

  }

  // ---------------------------
  // City image auto
  // ---------------------------
  function setCityByIso(iso) {

    if (!cityImage) return;

    const country = COUNTRIES.find(x => (x.iso || x.iso2) === iso);

    const query = country ? country.name : "city";

    cityImage.src =
      "https://source.unsplash.com/1200x600/?city," +
      encodeURIComponent(query) +
      "&t=" + Date.now();

  }

  function getSelectedIso() {

    return countryBtn?.dataset?.countryIso || "AF";

  }

  // ================= DISPLAY FORMAT =================
  function formatForDisplay(e164) {

    const d = digitsOnly(e164);

    if (!d) return e164;

    if (d.startsWith("33")) {

      const rest = d.slice(2);

      let out = "+33";

      if (rest.length > 0) out += " " + rest.slice(0, 1);
      if (rest.length > 1) out += " " + rest.slice(1, 3);
      if (rest.length > 3) out += " " + rest.slice(3, 5);
      if (rest.length > 5) out += " " + rest.slice(5, 7);
      if (rest.length > 7) out += " " + rest.slice(7, 9);

      if (rest.length > 9) out += " " + rest.slice(9);

      return out;

    }

    const grouped = d.replace(/(\d{3})(?=\d)/g, "$1 ").trim();

    return "+" + grouped;

  }

  function syncHiddenE164(e164) {

    if (!phoneE164) return;

    phoneE164.value = e164;

  }

  // ================= COUNTRY =================
  function setCountry(iso, opts = {}) {

    if (!COUNTRIES.length) return;

    const c = COUNTRIES.find(x => x.iso === iso || x.iso2 === iso) || COUNTRIES[0];

    const isoVal = c.iso || c.iso2;

    if (countryBtn) countryBtn.dataset.countryIso = isoVal;

    if (countryFlag) countryFlag.textContent = c.flag;

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

// ================= VALIDATION =================

function showEmpty() {

  if (continueBtn) continueBtn.disabled = true;

  if (help) {

    help.classList.remove("tz-help--ok", "tz-help--error");
    help.classList.add("tz-help--muted");

    help.textContent = help.dataset.empty;

  }

  phoneInput?.classList.remove("tz-input--error");

}

function showValid() {

  if (continueBtn) continueBtn.disabled = false;

  if (help) {

    help.classList.remove("tz-help--error", "tz-help--muted");
    help.classList.add("tz-help--ok");

    help.textContent = help.dataset.valid;

  }

  phoneInput?.classList.remove("tz-input--error");

}

function showInvalid() {

  if (continueBtn) continueBtn.disabled = true;

  if (help) {

    help.classList.remove("tz-help--ok", "tz-help--muted");
    help.classList.add("tz-help--error");

    help.textContent = help.dataset.invalid;

  }

  phoneInput?.classList.add("tz-input--error");

}

function validateAndSync() {

  if (!phoneInput) return;

  // -------- état vide --------
  if (!phoneInput.value.trim()) {
    showEmpty();
    return;
  }

  const rawE164 = sanitizeToE164(phoneInput.value);

  if (rawE164 === null) {

    showInvalid();
    return;

  }

  let e164 = normalizeLeadingZero(rawE164);

  syncHiddenE164(e164);

  const display = formatForDisplay(e164);

  if (phoneInput.value !== display) {

    _isProgrammaticUpdate = true;
    phoneInput.value = display;
    _isProgrammaticUpdate = false;

  }

  const digits = digitsOnly(e164);

  const validLength = digits.length >= 9 && digits.length <= 15;

  if (validLength) showValid();
  else showInvalid();

}

  // ================= MODAL =================
  function openModal() {

    if (!modal) return;

    modal.style.display = "block";

    renderList("");

    setTimeout(() => search?.focus(), 50);

  }

  function closeModal() {

    if (!modal) return;

    modal.style.display = "none";

  }

  function renderList(q) {

    if (!COUNTRIES.length || !list) return;

    const query = (q || "").toLowerCase();

    list.innerHTML = "";

    const filtered = COUNTRIES.filter(c =>
      c.name.toLowerCase().includes(query) ||
      c.dial.includes(query)
    );

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

        validateAndSync();

      };

      list.appendChild(row);

    }

  }

  // ================= EVENTS =================
  phoneInput?.addEventListener("input", () => {

    if (_isProgrammaticUpdate) return;

    validateAndSync();

  });

  countryBtn?.addEventListener("click", openModal);

  search?.addEventListener("input", (e) => renderList(e.target.value));

  modal?.addEventListener("click", (e) => {

    if (e.target.classList.contains("tz-modal__backdrop")) closeModal();

  });

  contactBtn?.addEventListener("click", async () => {

    if (!("contacts" in navigator && "select" in navigator.contacts)) {

      alert("Contacts non disponibles");

      return;

    }

    try {

      const contacts = await navigator.contacts.select(["tel"], { multiple: false });

      if (contacts.length && contacts[0].tel?.length) {

        phoneInput.value = contacts[0].tel[0];

        validateAndSync();

      }

    } catch (e) {

      console.log("contact cancelled");

    }

  });

  const form = phoneInput?.closest("form");

  if (form) {

    form.addEventListener("submit", () => {

      if (phoneE164 && !phoneE164.value) {

        const e164 = sanitizeToE164(phoneInput.value);

        if (e164) phoneE164.value = normalizeLeadingZero(e164);

      }

    });

  }


  // ================= INIT =================
loadCountries();

// expose modal functions to HTML
window.openModal = openModal;
window.closeModal = closeModal;

})();
