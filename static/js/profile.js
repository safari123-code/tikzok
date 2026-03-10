// ---------------------------
// Profile avatar preview
// ---------------------------

(function () {

  const input = document.getElementById("avatarInput");
  const preview = document.getElementById("avatarPreview");

  if (!input || !preview) return;

  input.addEventListener("change", () => {

    const file = input.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = (e) => {

      // Si c'était un placeholder on remplace
      if (preview.tagName !== "IMG") {

        const img = document.createElement("img");
        img.id = "avatarPreview";
        img.className = "tz-avatar-img";
        img.src = e.target.result;

        preview.replaceWith(img);

      } else {
        preview.src = e.target.result;
      }

    };

    reader.readAsDataURL(file);

  });

})();

// ---------------------------
// Avatar crop + preview
// ---------------------------

let cropper;

const input = document.getElementById("avatarInput");
const preview = document.getElementById("avatarPreview");

if (input) {

  input.addEventListener("change", e => {

    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = function (event) {

      if (preview.tagName !== "IMG") {
        const img = document.createElement("img");
        img.id = "avatarPreview";
        img.className = "tz-avatar-img";
        preview.replaceWith(img);
      }

      preview.src = event.target.result;

      if (cropper) cropper.destroy();

      cropper = new Cropper(preview, {
        aspectRatio: 1,
        viewMode: 1,
        autoCropArea: 1
      });

    };

    reader.readAsDataURL(file);

  });

}

// ---------------------------
// Auto save profile
// ---------------------------

const form = document.querySelector("form");

if (form) {

  form.querySelectorAll("input").forEach(input => {

    input.addEventListener("change", () => {

      const formData = new FormData(form);

      fetch(form.action || window.location.pathname, {
        method: "POST",
        body: formData
      });

    });

  });

}