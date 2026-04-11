// ---------------------------
// Feature: Payment Method UX (Wallet Credit)
// ---------------------------
(function () {

  const form = document.getElementById("paymentMethodForm");
  if (!form) return;

  const amount = parseFloat(form.dataset.amount || "0");

  const walletBalance =
    parseFloat(
      document.getElementById("walletBalance")?.textContent || "0"
    );

  const useCreditToggle = document.getElementById("useCreditToggle");
  const saveCardToggle = document.getElementById("saveCardToggle");

  const useCreditInput = document.getElementById("useCreditInput");
  const saveCardInput = document.getElementById("saveCardInput");
  const selectedMethodInput = document.getElementById("selectedMethodInput");

  const finalAmountText = document.getElementById("finalAmountText");
  const payBtn = document.getElementById("payBtn");

  // ---------------------------
  // Force payment method = card
  // ---------------------------
  if (selectedMethodInput) {
    selectedMethodInput.value = "card";
  }

  // ---------------------------
  // Utils
  // ---------------------------
  function formatAmount(v) {
    return (Math.round(v * 100) / 100).toFixed(2);
  }

  // ---------------------------
  // Compute final amount
  // ---------------------------
  function computeFinal() {

    const useCredit =
      useCreditToggle ? useCreditToggle.checked : false;

    const creditUsed = useCredit
      ? Math.min(walletBalance, amount)
      : 0;

    const finalAmount = Math.max(
      0,
      amount - creditUsed
    );

    if (finalAmountText) {
      finalAmountText.textContent =
        `${formatAmount(finalAmount)} €`;
    }

    if (payBtn) {
      payBtn.textContent =
        payBtn.textContent.replace(
          /[0-9]+(\.[0-9]+)?/,
          formatAmount(finalAmount)
        );
    }

    if (useCreditInput) {
      useCreditInput.value =
        useCredit ? "1" : "0";
    }
  }

  // ---------------------------
  // Credit toggle
  // ---------------------------
  useCreditToggle?.addEventListener(
    "change",
    computeFinal
  );

  // ---------------------------
  // Save card toggle
  // ---------------------------
  saveCardToggle?.addEventListener(
    "change",
    () => {
      if (saveCardInput) {
        saveCardInput.value =
          saveCardToggle.checked ? "1" : "0";
      }
    }
  );

  // ---------------------------
  // Prevent double submit
  // ---------------------------
  let submitting = false;

  form.addEventListener("submit", () => {

    if (submitting) return false;

    submitting = true;

    payBtn?.classList.add("is-loading");

    return true;
  });

  computeFinal();

})();