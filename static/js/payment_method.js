// ---------------------------
// Feature: Payment Method UX
// ---------------------------
(function () {

  const form = document.getElementById("paymentMethodForm");
  if (!form) return;

  const amount = parseFloat(form.dataset.amount || "0");
  const points = parseFloat(form.dataset.points || "0");

  const toastKey = form.dataset.toastKey || "";

  const usePointsToggle = document.getElementById("usePointsToggle");
  const saveCardToggle = document.getElementById("saveCardToggle");

  const usePointsInput = document.getElementById("usePointsInput");
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

    const usePoints = usePointsToggle ? usePointsToggle.checked : false;

    const pointsUsed = usePoints
      ? Math.min(points, amount)
      : 0;

    const finalAmount = Math.max(
      0,
      amount - pointsUsed
    );

    if (finalAmountText) {
      finalAmountText.textContent = `${formatAmount(finalAmount)} €`;
    }

    if (payBtn) {
      payBtn.textContent = payBtn.textContent.replace(
        /[0-9]+(\.[0-9]+)?/,
        formatAmount(finalAmount)
      );
    }

    if (usePointsInput) {
      usePointsInput.value = usePoints ? "1" : "0";
    }
  }

  // ---------------------------
  // Points toggle
  // ---------------------------

  usePointsToggle?.addEventListener(
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