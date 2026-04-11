// ---------------------------
// Wallet quick amounts
// ---------------------------

(function(){

const buttons = document.querySelectorAll("#quickAmounts .tz-amt-btn");
const payBtn = document.getElementById("quickPayBtn");
const shareBtn = document.getElementById("shareLinkBtn");

if(!buttons.length) return;

let selectedAmount = 5;

// default select 5€
buttons[0].classList.add("is-selected");

buttons.forEach(btn => {

btn.addEventListener("click", () => {

buttons.forEach(b => b.classList.remove("is-selected"));
btn.classList.add("is-selected");

selectedAmount = parseFloat(btn.dataset.amount);

});

});

// continuer → payment method
payBtn?.addEventListener("click", () => {

window.location.href =
`/payment/method?amount=${selectedAmount}`;

});

// share link
shareBtn?.addEventListener("click", async () => {

const link =
`${window.location.origin}/payment/card?amount=${selectedAmount}`;

await navigator.clipboard.writeText(link);

shareBtn.textContent = "Lien copié ✓";

setTimeout(()=>{
shareBtn.textContent = "Copier lien ami";
},1500);

});

})();