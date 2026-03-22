// ---------------------------
// Feature: Forfait behavior (FINAL CLEAN)
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
  const operatorId = amountCard?.dataset?.operatorId || "";
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
  // Reloadly Quote (API ONLY)
  // ---------------------------

  async function fetchQuote(amount) {

    const gb = forfaitGb?.value;

    // Forfait priorité
    if (gb && rowReceived) {
      rowReceived.textContent = gb;
      return;
    }

    if (!operatorId) return;

    try {

      const res = await fetch("/recharge/api/quote", {

        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },

        body: JSON.stringify({
          operatorId: operatorId,
          amount: amount // ✅ backend gère fees
        })
      });

      if (!res.ok) return;

      const data = await res.json();

      if (!data?.ok) return;

      if (data.localAmount && data.localCurrency && rowReceived) {

        rowReceived.textContent =
          `${Math.round(Number(data.localAmount))} ${data.localCurrency}`;
      }

    } catch (e) {
      console.error("quote error", e);
    }
  }

  function scheduleQuote(amount) {

    if (debounceT)
      window.clearTimeout(debounceT);

    debounceT =
      window.setTimeout(() => fetchQuote(amount), 250);
  }

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
  // Events
  // ---------------------------

  moneyBtn?.addEventListener("click", () => {

    const isOpen = moneyPanel.style.display !== "none";
    setMoneyOpen(!isOpen);
  });

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

  range?.addEventListener("input", () => {
    updateUI(parseFloat(range.value));
  });

  range?.addEventListener("change", () => {

    const v = parseFloat(range.value);

    setMoneyOpen(true);
    scheduleQuote(v);
    scrollToDetails();
  });

  forfaitCard?.addEventListener("click", (e) => {

    if (e.target && e.target.closest("#removeForfaitBtn")) return;

    const url = forfaitCard.dataset.forfaitUrl;

    if (url) window.location.href = url;
  });

  removeForfaitBtn?.addEventListener("click", (e) => {

    e.preventDefault();
    e.stopPropagation();

    if (forfaitGb) forfaitGb.value = "";
    if (forfaitPrice) forfaitPrice.value = "";

    const fallback = document.documentElement.dataset.tzChooseInternetPlan || "";

    if (forfaitTitle) forfaitTitle.textContent = fallback;

    removeForfaitBtn.style.display = "none";

    const amount = parseFloat(amountInput?.value || "0");

    scheduleQuote(amount);

    setAmountLocked(false);

    tzToast?.(document.documentElement.dataset.tzRemovedText || "");

    removeForfaitBtn.style.transform = "scale(.98)";

    setTimeout(() => (removeForfaitBtn.style.transform = ""), 120);
  });

  // ---------------------------
  // Init
  // ---------------------------

  const initialAmount =
    parseFloat(amountInput?.value || "0");

  updateUI(initialAmount);
  setMoneyOpen(true);
  scheduleQuote(initialAmount);
  scrollToDetails();
  applyForfaitStateFromInputs();

})();