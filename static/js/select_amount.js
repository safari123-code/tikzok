// ---------------------------
// Feature: Forfait behavior (FINAL PRODUCTION)
// ---------------------------

(function () {

  const form = document.getElementById("selectAmountForm");
  if (!form) return;

  const continueBtn = document.getElementById("continueBtn");
  const amountCard = document.getElementById("amountCard");
  const amountDisplay = document.getElementById("amountDisplay");
  const amountInput = document.getElementById("amountInput");

  const rowAmount = document.getElementById("rowAmount");
  const rowTax = document.getElementById("rowTax");
  const rowReceived = document.getElementById("rowReceived");
  const pointsEarnedText = document.getElementById("pointsEarnedText");

  const moneyBtn = document.getElementById("moneyAccordionBtn");
  const moneyPanel = document.getElementById("moneyPanel");
  const chevron = document.getElementById("moneyChevron");

  const fixedWrap = document.getElementById("fixedAmountWrap");
  const range = document.getElementById("amountRange");

  const forfaitCard = document.getElementById("forfaitCard");
  const forfaitTitle = document.getElementById("forfaitTitle");
  const removeForfaitBtn = document.getElementById("removeForfaitBtn");
  const forfaitGb = document.getElementById("forfaitGb");
  const forfaitPrice = document.getElementById("forfaitPrice");

  const taxRate = parseFloat(amountCard?.dataset?.taxRate || "0.10");
  const pointsRate = parseFloat(amountCard?.dataset?.pointsRate || "0.025");

  const userCurrency = "€";

  let debounceT = null;

  function fmt2(v) {
    return (Math.round(Number(v || 0) * 100) / 100).toFixed(2);
  }

  function setSelectedButton(v) {
    if (!fixedWrap) return;

    fixedWrap.querySelectorAll(".tz-amt-btn").forEach((b) => {
      b.classList.toggle("is-selected", parseFloat(b.dataset.amount) === v);
    });
  }

  function setMoneyOpen(open) {
    if (!moneyBtn || !moneyPanel) return;

    moneyPanel.style.display = open ? "block" : "none";

    if (chevron) chevron.textContent = open ? "▴" : "▾";

    moneyBtn.setAttribute("aria-expanded", String(open));
  }

  function scrollToDetails() {
    window.setTimeout(() => {
      moneyPanel?.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    }, 200);
  }

  function setAmountLocked(locked) {

    if (fixedWrap) {
      fixedWrap.style.opacity = locked ? "0.45" : "1";
      fixedWrap.style.pointerEvents = locked ? "none" : "auto";
    }

    if (range) {
      range.disabled = !!locked;
      range.style.opacity = locked ? "0.45" : "1";
    }
  }

  // ---------------------------
  // UI update
  // ---------------------------

  function updateUI(amount) {

    const a = Number(amount || 0);

    if (amountInput) amountInput.value = fmt2(a);

    if (amountDisplay)
      amountDisplay.textContent = `${fmt2(a)} ${userCurrency}`;

    if (rowAmount)
      rowAmount.textContent = `${fmt2(a)} ${userCurrency}`;

    if (rowTax)
      rowTax.textContent = `${fmt2(a * taxRate)} ${userCurrency}`;

    if (pointsEarnedText) {

      const points = fmt2(a * pointsRate);

      pointsEarnedText.textContent =
        pointsEarnedText.textContent.replace(/[0-9]+(\.[0-9]+)?/, points);
    }

    const total = a + (a * taxRate);

    if (continueBtn) {

      const payTemplate = continueBtn?.dataset?.payText || "Pay {amount}";
      const formatted = `${fmt2(total)} ${userCurrency}`;

      continueBtn.textContent =
        payTemplate.replace("{amount}", formatted);
    }
  }

 // ---------------------------
// 🔥 BACKEND ONLY (FINAL PRODUCTION SAFE)
// ---------------------------

async function fetchQuote(amount) {

  const gb = forfaitGb?.value;

  // ---------------------------
  // Priorité forfait
  // ---------------------------
  if (gb && rowReceived) {
    rowReceived.textContent = gb;
    return;
  }

  if (rowReceived) {
    rowReceived.style.opacity = "0.6";
  }

  try {

    const res = await fetch("/recharge/api/quote", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        amount: amount
      })
    });

    let data = null;

    // 🔥 SAFE PARSE
    try {
      data = await res.json();
    } catch (_) {
      data = null;
    }

    // ---------------------------
    // ❌ erreur backend
    // ---------------------------
    if (!res.ok || !data || !data.ok) {

      if (rowReceived) {
        rowReceived.textContent = "—";
        rowReceived.style.opacity = "0.5";
      }

      return;
    }

    // ---------------------------
    // ✅ SUCCESS
    // ---------------------------
    if (data.received && rowReceived) {

      rowReceived.textContent = data.received;

      // animation micro-interaction
      rowReceived.style.transition = "all .25s ease";
      rowReceived.style.transform = "scale(1.05)";
      rowReceived.style.opacity = "1";

      setTimeout(() => {
        rowReceived.style.transform = "scale(1)";
      }, 140);
    }

  } catch (e) {

    console.error("quote error", e);

    if (rowReceived) {
      rowReceived.textContent = "—";
      rowReceived.style.opacity = "0.5";
    }
  }
} 

  // ---------------------------
  // Debounce
  // ---------------------------

  function scheduleQuote(amount) {

    if (debounceT)
      window.clearTimeout(debounceT);

    debounceT =
      window.setTimeout(() => fetchQuote(amount), 250);
  }

  // ---------------------------
  // Forfait logic
  // ---------------------------

  function applyForfaitStateFromInputs() {

    const gb = (forfaitGb?.value || "").trim();
    const priceStr = (forfaitPrice?.value || "").trim();

    const hasForfait = !!gb && !!priceStr && !Number.isNaN(Number(priceStr));

    if (hasForfait) {

      const p = Number(priceStr);

      updateUI(p);
      setSelectedButton(p);
      setMoneyOpen(true);
      setAmountLocked(true);
      scheduleQuote(p);
      scrollToDetails();

    } else {

      setAmountLocked(false);
    }
  }

 // ---------------------------
// Events (FINAL PRODUCTION)
// ---------------------------

// Accordion
moneyBtn?.addEventListener("click", () => {
  const isOpen = moneyPanel.style.display !== "none";
  setMoneyOpen(!isOpen);
});

// Fixed amounts
fixedWrap?.addEventListener("click", (e) => {

  const btn = e.target.closest(".tz-amt-btn");
  if (!btn) return;

  const v = parseFloat(btn.dataset.amount);

  setSelectedButton(v);
  updateUI(v);
  setMoneyOpen(true);
  scheduleQuote(v);
  scrollToDetails();
});

// Range slider (live)
range?.addEventListener("input", () => {
  updateUI(parseFloat(range.value));
});

// Range slider (final)
range?.addEventListener("change", () => {

  const v = parseFloat(range.value);

  setMoneyOpen(true);
  scheduleQuote(v);
  scrollToDetails();
});

// Remove forfait
removeForfaitBtn?.addEventListener("click", (e) => {

  e.preventDefault();
  e.stopPropagation();

  if (forfaitGb) forfaitGb.value = "";
  if (forfaitPrice) forfaitPrice.value = "";

  removeForfaitBtn.style.display = "none";

  const amount = parseFloat(amountInput?.value || "0");

  scheduleQuote(amount);
  setAmountLocked(false);

  tzToast?.(document.documentElement.dataset.tzRemovedText || "");
});

// ---------------------------
// 🔥 Forfait card click → redirect
// ---------------------------
forfaitCard?.addEventListener("click", (e) => {

  // ignore clic sur bouton remove
  if (e.target.closest("#removeForfaitBtn")) return;

  const url = forfaitCard.dataset.forfaitUrl;

  if (url) {
    window.location.href = url;
  }
});
  // ---------------------------
  // Init
  // ---------------------------

  if (rowReceived) {
    rowReceived.style.opacity = "0.8";
  }

  const initialAmount =
    parseFloat(amountInput?.value || "0");

  updateUI(initialAmount);
  setMoneyOpen(true);
  scheduleQuote(initialAmount);
  scrollToDetails();
  applyForfaitStateFromInputs();

})();