// ---------------------------
// Feature: Payment Method UX
// ---------------------------
(function () {

  const form = document.getElementById("paymentMethodForm");

  if (form) {

    const amount = parseFloat(form.dataset.amount || "0");
    const points = parseFloat(form.dataset.points || "0");

    const toastKey = form.dataset.toastKey || "";
    if (toastKey) {
      tzToast?.(document.querySelector(`[data-i18n="${toastKey}"]`)?.textContent || "");
    }

    const usePointsToggle = document.getElementById("usePointsToggle");
    const saveCardToggle = document.getElementById("saveCardToggle");

    const usePointsInput = document.getElementById("usePointsInput");
    const saveCardInput = document.getElementById("saveCardInput");
    const selectedMethodInput = document.getElementById("selectedMethodInput");

    const finalAmountText = document.getElementById("finalAmountText");
    const payBtn = document.getElementById("payBtn");

    // Force card method
    if (selectedMethodInput) {
      selectedMethodInput.value = "card";
    }

    function fmt2(v){
      return (Math.round(v * 100) / 100).toFixed(2);
    }

    function computeFinal(){

      const usePoints = usePointsToggle ? usePointsToggle.checked : false;

      const pointsUsed = usePoints
        ? Math.min(points, amount)
        : 0;

      const finalAmount = Math.max(
        0,
        amount - pointsUsed
      );

      if (finalAmountText) {
        finalAmountText.textContent = `${fmt2(finalAmount)} €`;
      }

      if (payBtn) {
        payBtn.textContent =
          payBtn.textContent.replace(
            /[0-9]+(\.[0-9]+)?/,
            fmt2(finalAmount)
          );
      }

      if (usePointsInput) {
        usePointsInput.value = usePoints ? "1" : "0";
      }
    }

    usePointsToggle?.addEventListener(
      "change",
      computeFinal
    );

    saveCardToggle?.addEventListener(
      "change",
      () => {
        saveCardInput.value =
          saveCardToggle.checked ? "1" : "0";
      }
    );

    // Prevent double submit
    let locking = false;

    form.addEventListener("submit", () => {

      if (locking) return false;

      locking = true;

      payBtn?.classList.add("is-loading");

      return true;
    });

    computeFinal();
  }

  // ---------------------------
  // Feature: Card menu (⋯)
  // ---------------------------

  document
    .querySelectorAll(".tz-card-menu-btn")
    .forEach(btn => {

      btn.addEventListener("click", e => {

        e.stopPropagation();

        const menu =
          btn.nextElementSibling;

        document
          .querySelectorAll(".tz-card-menu")
          .forEach(m => {

            if (m !== menu) {
              m.classList.remove("open");
            }

          });

        menu?.classList.toggle("open");

      });

    });

  // close menu outside click

  document.addEventListener(
    "click",
    () => {

      document
        .querySelectorAll(".tz-card-menu")
        .forEach(menu => {

          menu.classList.remove("open");

        });

    }
  );

})();