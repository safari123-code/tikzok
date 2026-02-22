(function () {
  const cardNumber = document.getElementById("cardNumber");
  const expiry = document.getElementById("expiry");
  const cvv = document.getElementById("cvv");

  function digitsOnly(s) { return (s || "").replace(/[^\d]/g, ""); }

  function formatCardNumber(v) {
    const d = digitsOnly(v).slice(0, 19);
    return d.replace(/(\d{4})(?=\d)/g, "$1 ").trim();
  }

  function formatExpiry(v) {
    const d = digitsOnly(v).slice(0, 4);
    if (d.length <= 2) return d;
    return d.slice(0,2) + "/" + d.slice(2);
  }

  cardNumber?.addEventListener("input", () => {
    const v = formatCardNumber(cardNumber.value);
    cardNumber.value = v;
  });

  expiry?.addEventListener("input", () => {
    expiry.value = formatExpiry(expiry.value);
  });

  cvv?.addEventListener("input", () => {
    cvv.value = digitsOnly(cvv.value).slice(0, 4);
  });
})();