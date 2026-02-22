// ---------------------------
// Enter number UX (FINAL)
// ---------------------------
(function () {
  const phoneInput = document.getElementById("phoneInput");
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
      const res = await fetch("/static/data/countries.json", { cache: "no-store" });
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

      if (digits.length > MAX_DIAL_LEN) MAX_DIAL_LEN = digits.length;
    }

    MAX_DIAL_LEN = Math.min(MAX_DIAL_LEN, 6);
  }

  // ================= HELPERS =================
  function digitsOnly(s) {
    return (s || "").replace(/[^\d]/g, "");
  }

  function sanitizePhone(value) {
    let v = (value || "").trim();

    if (!v.startsWith("+")) v = "+" + v;
    v = "+" + v.slice(1).replace(/[^\d]/g, "");

    const d = digitsOnly(v);
    if (d.length > 15) return null;

    return v;
  }

  function setCityByIso(iso) {
    const lower = (iso || "af").toLowerCase();
    cityImage.src = `/static/images/cities/${lower}.jpg`;
  }

  function getSelectedIso() {
    return countryBtn?.dataset?.countryIso || "AF";
  }

  // ================= COUNTRY =================
  function setCountry(iso, opts = {}) {
    if (!COUNTRIES.length) return;

    const c = COUNTRIES.find(x => x.iso === iso) || COUNTRIES[0];

    countryBtn.dataset.countryIso = c.iso;
    countryFlag.textContent = c.flag;

    setCityByIso(c.iso);

    if (opts.setPrefixIfEmpty) {
      const current = sanitizePhone(phoneInput.value) || "";
      const currentDigits = digitsOnly(current);
      const dialDigits = c.dial.replace(/[^\d]/g, "");

      if (!currentDigits || currentDigits.length <= dialDigits.length) {
        _isProgrammaticUpdate = true;
        phoneInput.value = c.dial;
        phoneInput.setSelectionRange(phoneInput.value.length, phoneInput.value.length);
        _isProgrammaticUpdate = false;
      }
    }
  }

  function detectCountryFromPhone(phone) {
    const v = sanitizePhone(phone);
    if (!v) return null;

    const digits = digitsOnly(v);
    const maxLen = Math.min(MAX_DIAL_LEN, digits.length);

    for (let len = maxLen; len >= 1; len--) {
      const candidate = digits.slice(0, len);
      const country = DIAL_INDEX.get(candidate);
      if (country) return country;
    }

    return null;
  }

  // ================= UI HELPERS =================
  function showValid() {
    continueBtn.disabled = false;

    help.classList.remove("tz-help--error", "tz-help--muted");
    help.classList.add("tz-help--ok");

    phoneInput.classList.remove("tz-input--error");
  }

  function showInvalid() {
    continueBtn.disabled = true;

    help.classList.remove("tz-help--ok");
    help.classList.add("tz-help--muted");

    phoneInput.classList.add("tz-input--error");
  }

  // ================= VALIDATION =================
  function validateAndSync() {
    const v = sanitizePhone(phoneInput.value);

    if (v === null) {
      showInvalid();
      return;
    }

    if (phoneInput.value !== v) {
      _isProgrammaticUpdate = true;
      phoneInput.value = v;
      _isProgrammaticUpdate = false;
    }

    const detected = detectCountryFromPhone(v);

    if (detected) {
      const currentIso = getSelectedIso();
      if (detected.iso !== currentIso) {
        setCountry(detected.iso, { setPrefixIfEmpty: false });
      }
    }

    const digits = digitsOnly(v);
    const validLength = digits.length >= 9 && digits.length <= 15;
    const validCountry = !!detected;

    if (validLength && validCountry) showValid();
    else showInvalid();
  }

  // ================= MODAL =================
  function openModal() {
    modal.setAttribute("aria-hidden", "false");
    modal.classList.add("tz-modal--open");
    renderList("");
    setTimeout(() => search && search.focus(), 0);
  }

  function closeModal() {
    modal.setAttribute("aria-hidden", "true");
    modal.classList.remove("tz-modal--open");
  }

  function renderList(q) {
    if (!COUNTRIES.length) return;

    const query = (q || "").toLowerCase();
    const selectedIso = getSelectedIso();

    list.innerHTML = "";

    const filtered = COUNTRIES.filter(c =>
      c.name.toLowerCase().includes(query) ||
      c.dial.includes(query) ||
      c.iso.toLowerCase().includes(query)
    );

    filtered.sort((a, b) => {
      if (a.iso === selectedIso) return -1;
      if (b.iso === selectedIso) return 1;
      return a.name.localeCompare(b.name);
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

      row.addEventListener("click", () => {
        setCountry(c.iso, { setPrefixIfEmpty: true });
        closeModal();
        validateAndSync();
      });

      list.appendChild(row);
    }
  }

  // ================= EVENTS =================
  phoneInput?.addEventListener("input", () => {
    if (_isProgrammaticUpdate) return;
    validateAndSync();
  });

  countryBtn?.addEventListener("click", openModal);

  modal?.addEventListener("click", (e) => {
    const t = e.target;
    if (t && (t.dataset.close === "1" || t.classList.contains("tz-modal__backdrop"))) {
      closeModal();
    }
  });

  search?.addEventListener("input", (e) => renderList(e.target.value));

  // ⭐ CONTACT PICKER WEB (safe)
contactBtn?.addEventListener("click", async () => {
  if (!("contacts" in navigator && "select" in navigator.contacts)) {
    console.log("Contact picker not supported");
    return;
  }

  try {
    const contacts = await navigator.contacts.select(["tel"], { multiple: false });

    if (contacts.length && contacts[0].tel?.length) {
      phoneInput.value = contacts[0].tel[0];
      validateAndSync();
    }
  } catch (e) {
    console.log("User cancelled");
  }
});
  // ================= INIT =================
  loadCountries();

})();