// ---------------------------
// Feature: Success Copy (FINAL PRO)
// ---------------------------
(function () {

  const buttons = document.querySelectorAll(".tz-copy-btn");
  if (!buttons.length) return;

  buttons.forEach((btn) => {

    btn.addEventListener("click", async () => {

      const targetId = btn.getAttribute("data-copy-target");
      const target = document.getElementById(targetId);
      if (!target) return;

      const text = (target.textContent || "").trim();
      if (!text) return;

      try {
        // ---------------------------
        // Modern clipboard API
        // ---------------------------
        await navigator.clipboard.writeText(text);

      } catch (_) {
        // ---------------------------
        // Fallback (iOS / vieux Android)
        // ---------------------------
        try {
          const textarea = document.createElement("textarea");
          textarea.value = text;
          textarea.style.position = "fixed";
          textarea.style.opacity = "0";
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand("copy");
          document.body.removeChild(textarea);
        } catch (err) {
          tzToast?.(document.documentElement.dataset.tzCopyFailedText || "");
          return;
        }
      }

      // ---------------------------
      // Micro animation button
      // ---------------------------
      btn.style.transform = "scale(.92)";
      btn.style.transition = "transform .15s ease";

      setTimeout(() => {
        btn.style.transform = "";
      }, 120);

      // ---------------------------
      // Highlight target
      // ---------------------------
      target.style.transition = "all .25s ease";
      target.style.background = "rgba(76,175,80,.12)";
      target.style.borderRadius = "10px";
      target.style.padding = "2px 8px";

      setTimeout(() => {
        target.style.background = "";
        target.style.borderRadius = "";
        target.style.padding = "";
      }, 650);

      // ---------------------------
      // Toast
      // ---------------------------
      tzToast?.(document.documentElement.dataset.tzCopiedText || "");

    });

  });

})();