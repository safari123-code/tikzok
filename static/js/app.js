function tzCloseAbout(){
  document.body.style.opacity = "0";
  setTimeout(()=> history.back(),150);
}
// ---------------------------
// Disable double tap zoom
// ---------------------------
let lastTouchEnd = 0;

document.addEventListener('touchend', function (event) {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
        event.preventDefault();
    }
    lastTouchEnd = now;
}, false);
// ---------------------------
// Gmail suggestion button (FINAL)
// ---------------------------
document.addEventListener("DOMContentLoaded", function () {

  const input = document.getElementById("emailInput");
  const btn = document.getElementById("gmailSuggestBtn");

  if (!input || !btn) return;

  input.addEventListener("input", function () {
    const value = input.value.trim();

    if (value && !value.includes("@")) {
      btn.textContent = value + "@gmail.com";
      btn.style.display = "block";
    } else {
      btn.style.display = "none";
    }
  });

  btn.addEventListener("click", function () {
    input.value = btn.textContent;
    btn.style.display = "none";
    input.focus();
  });

});