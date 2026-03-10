// ---------------------------
// Feature: Success Copy (animation + toast)
// ---------------------------
(function () {
  document.querySelectorAll(".tz-copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const targetId = btn.getAttribute("data-copy-target");
      const target = document.getElementById(targetId);
      if (!target) return;

      const text = target.textContent.trim();

      try {
        await navigator.clipboard.writeText(text);

        // micro animation
        btn.style.transform = "scale(.95)";
        window.setTimeout(() => (btn.style.transform = ""), 120);

        // highlight copied target
        target.style.background = "rgba(76,175,80,.12)";
        target.style.borderRadius = "10px";
        target.style.padding = "2px 8px";
        window.setTimeout(() => {
          target.style.background = "";
          target.style.borderRadius = "";
          target.style.padding = "";
        }, 650);

        tzToast?.(document.documentElement.dataset.tzCopiedText || "");
      } catch (_) {
        tzToast?.(document.documentElement.dataset.tzCopyFailedText || "");
      }
    });
  });
})();