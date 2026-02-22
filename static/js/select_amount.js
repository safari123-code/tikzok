// ---------------------------
// Select amount UX (Flutter-like)
// ---------------------------
(function () {
  const ctx = window.__TZ_CTX__ || {};
  const taxRate = Number(ctx.tax_rate || 0.10);

  const fixedWrap = document.getElementById("fixedAmountsWrap");
  const amountDisplay = document.getElementById("amountDisplay");
  const pointsEarned = document.getElementById("pointsEarned");

  const rowAmount = document.getElementById("rowAmount");
  const rowTax = document.getElementById("rowTax");
  const rowReceived = document.getElementById("rowReceived");

  const quoteLoader = document.getElementById("quoteLoader");
  const moneyToggle = document.getElementById("moneyToggle");
  const moneyDetails = document.getElementById("moneyDetails");
  const chevron = document.getElementById("moneyChevron");

  const goPayBtn = document.getElementById("goPayBtn");

  let operatorId = ctx.operator?.id || null;
  let amount = 5.0;
  let debounce = null;

  function moneyOpen(open) {
    moneyDetails.style.display = open ? "block" : "none";
    chevron.textContent = open ? "▴" : "▾";
  }

  function calcTax(a) {
    return +(a * taxRate).toFixed(2);
  }
  function totalToPay(a) {
    return +(a + calcTax(a)).toFixed(2);
  }
  function points(a) {
    return +(a * 0.025).toFixed(2);
  }

  function setAmount(a) {
    amount = +a;
    amountDisplay.textContent = `${amount.toFixed(2)} €`;
    pointsEarned.textContent = points(amount).toFixed(2);

    rowAmount.textContent = `${amount.toFixed(2)} €`;
    rowTax.textContent = `${calcTax(amount).toFixed(2)} €`;

    moneyOpen(true);
    scheduleQuote();
  }

  function renderFixedAmounts() {
    const fixed = (ctx.amounts && ctx.amounts.fixedAmounts) ? ctx.amounts.fixedAmounts : [];
    fixedWrap.innerHTML = "";

    if (!Array.isArray(fixed) || fixed.length === 0) return;

    fixed.forEach(v => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tz-amt-btn";
      btn.textContent = `${Number(v).toFixed(0)} €`;
      btn.addEventListener("click", () => {
        [...fixedWrap.querySelectorAll(".tz-amt-btn")].forEach(x => x.classList.remove("is-selected"));
        btn.classList.add("is-selected");
        setAmount(Number(v));
      });
      fixedWrap.appendChild(btn);
    });

    // default
    setAmount(Number(fixed[0]));
    fixedWrap.querySelector(".tz-amt-btn")?.classList.add("is-selected");
  }

  async function fetchQuote() {
    if (!operatorId) return;

    quoteLoader.hidden = false;
    try {
      const res = await fetch("/recharge/api/quote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operatorId, amount }),
      });

      if (!res.ok) throw new Error("quote");
      const data = await res.json();
      if (!data.ok) throw new Error("quote");

      const localAmount = data.localAmount;
      const localCurrency = data.localCurrency;
      rowReceived.textContent = `${Number(localAmount).toFixed(0)} ${localCurrency}`;
    } catch (e) {
      // fallback: show EUR
      rowReceived.textContent = `${amount.toFixed(0)} EUR`;
    } finally {
      quoteLoader.hidden = true;
    }
  }

  function scheduleQuote() {
    if (debounce) clearTimeout(debounce);
    debounce = setTimeout(fetchQuote, 250);
  }

  async function persistTotalAndGoPay() {
    // store total in session before going to /payment/method
    const total = totalToPay(amount);
    await fetch("/recharge/api/store-total", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ total: total.toFixed(2) }),
    }).catch(() => { /* ignore */ });

    window.location.href = "/payment/method";
  }

  moneyToggle?.addEventListener("click", () => {
    const open = moneyDetails.style.display !== "block";
    moneyOpen(open);
  });

  goPayBtn?.addEventListener("click", persistTotalAndGoPay);

  renderFixedAmounts();
  moneyOpen(true);
  fetchQuote();
})();