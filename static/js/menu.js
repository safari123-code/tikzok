// ---------------------------
// Side menu toggle + outside click
// ---------------------------

const toggle = document.getElementById("menuToggle");
const menu = document.getElementById("sideMenu");

if (toggle && menu) {

    // Toggle bouton
    toggle.addEventListener("click", (e) => {
        e.stopPropagation();
        menu.classList.toggle("open");
    });

    // Click extérieur → fermer
    document.addEventListener("click", (e) => {
        const clickInsideMenu = menu.contains(e.target);
        const clickToggle = toggle.contains(e.target);

        if (!clickInsideMenu && !clickToggle) {
            menu.classList.remove("open");
        }
    });

}