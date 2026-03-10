// ---------------------------
// Feature: Card Payment UX + Copy/Paste animations
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
  const numEl = document.getElementById("cardNumber");
  const expEl = document.getElementById("cardExpiry");
  const cvvEl = document.getElementById("cardCvv");

  function digitsOnly(s){
    return (s || "").replace(/\D/g, "");
  }

  function formatCardNumber(v) {
    const d = digitsOnly(v).slice(0,19);
    return d.replace(/(.{4})/g, "$1 ").trim();
  }

  function formatExpiry(v) {
    const d = digitsOnly(v).slice(0,4);
    if (d.length <= 2) return d;
    return d.slice(0,2) + "/" + d.slice(2);
  }

  // ---------------------------
  // Micro interaction (paste)
  // ---------------------------
  function pulse(el){
    el.style.transform = "scale(1.01)";
    el.style.boxShadow = "0 0 0 4px rgba(33,150,243,.12)";
    setTimeout(() => {
      el.style.transform = "";
      el.style.boxShadow = "";
    },220);
  }

  // ---------------------------
  // Format inputs
  // ---------------------------
  numEl?.addEventListener("input", () => {
    const start = numEl.selectionStart || 0;
    const before = numEl.value;

    numEl.value = formatCardNumber(before);

    numEl.selectionEnd = numEl.selectionStart =
      Math.min(numEl.value.length, start);
  });

  expEl?.addEventListener("input", () => {
    expEl.value = formatExpiry(expEl.value);
  });

  [nameEl, numEl, expEl, cvvEl].forEach(el=>{
    el?.addEventListener("paste", ()=>pulse(el));
  });

  // ---------------------------
  // Save card toggle
  // ---------------------------
  saveToggle?.addEventListener("change", ()=>{
    saveInput.value = saveToggle.checked ? "1" : "0";
  });

  // ---------------------------
  // Error display
  // ---------------------------
  function showErr(id, show){
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = show ? "block" : "none";
  }

  // ---------------------------
  // Validation
  // ---------------------------
  function validate(){

    let ok = true;

    const name = (nameEl.value || "")
      .trim()
      .replace(/\s+/g," ");

    const parts = name.split(" ").filter(Boolean);

    if(parts.length < 2 || parts.some(p=>p.length < 2)){
      ok=false;
      showErr("errName",true);
    } else showErr("errName",false);


    const digits = digitsOnly(numEl.value);

    if(digits.length < 15 || digits.length > 19){
      ok=false;
      showErr("errNumber",true);
    } else showErr("errNumber",false);


    const exp = (expEl.value || "").trim();

    if(!/^(0[1-9]|1[0-2])\/\d{2}$/.test(exp)){
      ok=false;
      showErr("errExpiry",true);
    } else showErr("errExpiry",false);


    const cvv = (cvvEl.value || "").trim();

    if(!/^\d{3,4}$/.test(cvv)){
      ok=false;
      showErr("errCvv",true);
    } else showErr("errCvv",false);

    return ok;
  }

  // ---------------------------
  // Submit
  // ---------------------------
  let lock=false;

  form.addEventListener("submit",(e)=>{

    if(lock){
      e.preventDefault();
      return;
    }

    if(!validate()){
      e.preventDefault();
      tzToast?.("");
      return;
    }

    // IMPORTANT
    // send clean digits to Flask
    numEl.value = digitsOnly(numEl.value);

    lock=true;

    payBtn.classList.add("is-loading");

    if(btnLoader) btnLoader.style.display="inline-block";

    if(payBtnText) payBtnText.style.opacity=".92";

  });

})();