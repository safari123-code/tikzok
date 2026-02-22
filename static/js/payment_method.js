(function () {
  const ctx = window.__PAY_CTX__ || {};
  const amount = Number(ctx.amount || 0);
  const points = Number(ctx.points || 0);

  const usePoints = document.getElementById("usePoints");
  const pointsLine = document.getElementById("pointsLine");
  const finalAmount = document.getElementById("finalAmount");
  const payBtn = document.getElementById("payBtn");

  function compute() {
    const enabled = !!usePoints?.checked;
    const used = enabled ? Math.min(points, amount) : 0;
    const final = Math.max(0, amount - used);

    if (pointsLine) pointsLine.textContent = `${points.toFixed(2)}`;
    if (finalAmount) finalAmount.textContent = `${final.toFixed(2)} €`;
    if (payBtn) payBtn.textContent = `${final.toFixed(2)} €`;
  }

  usePoints?.addEventListener("change", compute);
  compute();
})();