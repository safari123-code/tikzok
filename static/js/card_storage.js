// ---------------------------
// Feature: Saved Cards Menu
// ---------------------------

(function () {

  const buttons = document.querySelectorAll(".tz-menu-btn");
  if (!buttons.length) return;

  const closeAllMenus = () => {
    document.querySelectorAll(".tz-menu-dropdown").forEach(menu => {
      menu.classList.remove("open");
    });
  };

  buttons.forEach(btn => {

    btn.addEventListener("click", (e) => {

      e.stopPropagation();

      const menu = btn.nextElementSibling;
      if (!menu) return;

      const isOpen = menu.classList.contains("open");

      closeAllMenus();

      if (!isOpen) {
        menu.classList.add("open");
      }

    });

  });

  // fermer si clic extérieur
  document.addEventListener("click", closeAllMenus);

  // support mobile touch
  document.addEventListener("touchstart", closeAllMenus);

})();