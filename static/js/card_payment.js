// ---------------------------
// Feature: Card Payment UX + Stripe Elements (3 fields)
// ---------------------------
(function () {

const form = document.getElementById("cardPaymentForm");
if (!form) return;

const payBtn = document.getElementById("payBtn");
const btnLoader = document.getElementById("btnLoader");
const payBtnText = document.getElementById("payBtnText");

const saveToggle = document.getElementById("saveCardToggle");
const saveInput = document.getElementById("saveCardInput");

const nameEl = document.getElementById("cardName");

// ---------------------------
// Stripe init
// ---------------------------
const stripe = Stripe(window.STRIPE_PUBLIC_KEY);

const elements = stripe.elements({
  locale: "fr"
});

const style = {
  base: {
    fontSize: "16px",
    color: "#1a1a1a",
    "::placeholder": {
      color: "#aab7c4"
    }
  }
};

// 🔒 Anti-Link + clean UI
const cardNumber = elements.create("cardNumber", {
  style: style,
  disableLink: true
});

const cardExpiry = elements.create("cardExpiry", { style });
const cardCvc = elements.create("cardCvc", { style });

cardNumber.mount("#card-number");
cardExpiry.mount("#card-expiry");
cardCvc.mount("#card-cvc");

const brandLogo = document.getElementById("cardBrandLogo");

const BRAND_ICONS = {
  visa: "https://img.icons8.com/color/48/visa.png",
  mastercard: "https://img.icons8.com/color/48/mastercard-logo.png",
  amex: "https://img.icons8.com/color/48/amex.png",
  discover: "https://img.icons8.com/color/48/discover.png",
  diners: "https://img.icons8.com/color/48/diners-club.png",
  jcb: "https://img.icons8.com/color/48/jcb.png",
  unionpay: "https://img.icons8.com/color/48/unionpay.png"
};

cardNumber.on("change", (event) => {

  const brand = event.brand;

  if (!brand || !BRAND_ICONS[brand]) {
    brandLogo.style.display = "none";
    return;
  }

  brandLogo.src = BRAND_ICONS[brand];
  brandLogo.style.display = "block";

});
// ---------------------------
// UX AUTO FOCUS (FINAL FIX)
// ---------------------------

// Nom → Numéro
nameEl?.addEventListener("input", () => {
  if (nameEl.value.trim().length >= 3) {
    cardNumber.focus();
  }
});

// Numéro → Expiration
cardNumber.on("change", (event) => {
  if (event.complete) {
    setTimeout(() => {
      cardExpiry.focus();
    }, 150);
  }
});

// Expiration → CVC
cardExpiry.on("change", (event) => {
  if (event.complete) {
    setTimeout(() => {
      cardCvc.focus();
    }, 150);
  }
});

// ---------------------------
// Saved card UX
// ---------------------------

const selectedCardBox = document.getElementById("selectedCardBox");
const selectedCardText = document.getElementById("selectedCardText");
const changeCardBtn = document.getElementById("changeCardBtn");

const savedCards = document.querySelectorAll(".tz-saved-card");

savedCards.forEach(card => {

  card.addEventListener("click", () => {

    const last4 = card.dataset.last4;
    const brand = card.dataset.brand || "Carte";
    const name = card.dataset.name || "";

    selectedCardBox.style.display = "block";
    selectedCardText.innerHTML = `💳 ${brand} •••• ${last4}`;

    if (nameEl) nameEl.value = name;

    document.getElementById("card-number").parentElement.style.display = "none";
    document.getElementById("card-expiry").parentElement.style.display = "none";

    setTimeout(() => cardCvc.focus(), 200);

  });

});

changeCardBtn?.addEventListener("click", () => {

  selectedCardBox.style.display = "none";

  document.getElementById("card-number").parentElement.style.display = "block";
  document.getElementById("card-expiry").parentElement.style.display = "block";

});
// ---------------------------
// Save card toggle
// ---------------------------
saveToggle?.addEventListener("change", () => {
  saveInput.value = saveToggle.checked ? "1" : "0";
});

// ---------------------------
// Helpers
// ---------------------------
function resetButton() {
  payBtn.classList.remove("is-loading");

  if (btnLoader) btnLoader.style.display = "none";
  if (payBtnText) payBtnText.style.opacity = "1";
}

// ---------------------------
// Submit
// ---------------------------
let lock = false;

form.addEventListener("submit", async (e) => {

  e.preventDefault();

  if (lock) return;
  lock = true;

  payBtn.classList.add("is-loading");

  if (btnLoader) btnLoader.style.display = "inline-block";
  if (payBtnText) payBtnText.style.opacity = ".92";

  try {

    const res = await fetch("/payment/card", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    });

    // 🔥 DEBUG RESPONSE RAW
    const raw = await res.text();
    console.log("RAW RESPONSE:", raw);

    let data;
    try {
      data = JSON.parse(raw);
    } catch (e) {
      console.error("JSON parse error:", e);
      tzToast?.("Server error");
      lock = false;
      resetButton();
      return;
    }

    console.log("DATA:", data);

    if (!res.ok) {
      tzToast?.("Server error");
      lock = false;
      resetButton();
      return;
    }

    // 🔥 Already processed (idempotency)
    if (data.already_processed) {
      window.location.href = "/payment/success";
      return;
    }

    // 🔥 Missing client secret
    if (!data.client_secret) {
      tzToast?.("Payment initialization failed");
      lock = false;
      resetButton();
      return;
    }

    // ---------------------------
    // Stripe confirm
    // ---------------------------
    const result = await stripe.confirmCardPayment(
      data.client_secret,
      {
        payment_method: {
          card: cardNumber,
          billing_details: {
            name: nameEl?.value || ""
          }
        }
      }
    );

    if (result.error) {
      console.error("Stripe error:", result.error);

      tzToast?.(
        result.error.message || "Paiement refusé"
      );

      cardNumber.focus();

      lock = false;
      resetButton();
      return;
    }

    // ---------------------------
    // SUCCESS
    // ---------------------------
    if (result.paymentIntent?.status === "succeeded") {
      window.location.href =
        "/payment/success?payment_intent=" +
        result.paymentIntent.id;
      return;
    }

    // fallback
    tzToast?.("Payment failed");

    lock = false;
    resetButton();

  } catch (err) {

    console.error("Stripe fatal error:", err);

    tzToast?.("Network error");

    lock = false;
    resetButton();

  }

});
})();