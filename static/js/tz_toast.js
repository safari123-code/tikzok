// ---------------------------
// Feature: Toast (lightweight)
// ---------------------------
(function () {
  function ensureToast() {
    let el = document.getElementById("tzToast");
    if (el) return el;
    el = document.createElement("div");
    el.id = "tzToast";
    el.style.position = "fixed";
    el.style.left = "50%";
    el.style.bottom = "18px";
    el.style.transform = "translateX(-50%)";
    el.style.padding = "12px 14px";
    el.style.borderRadius = "14px";
    el.style.background = "rgba(17,17,17,.92)";
    el.style.color = "#fff";
    el.style.fontWeight = "800";
    el.style.fontSize = "13px";
    el.style.maxWidth = "92vw";
    el.style.opacity = "0";
    el.style.pointerEvents = "none";
    el.style.transition = "opacity 160ms ease, transform 160ms ease";
    el.style.zIndex = "3000";
    document.body.appendChild(el);
    return el;
  }

  window.tzToast = function (msg) {
    if (!msg) return;
    const el = ensureToast();
    el.textContent = msg;
    el.style.opacity = "1";
    el.style.transform = "translateX(-50%) translateY(-2px)";
    window.clearTimeout(el._t);
    el._t = window.setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateX(-50%) translateY(0)";
    }, 2200);
  };
})();