// ---------------------------
// Select forfait (FINAL PRODUCTION)
// ---------------------------

async function selectForfait(btn){

  if(!btn) return;

  const gb = btn.dataset.gb || "";
  const price = parseFloat(btn.dataset.price || "0");
  const planId = btn.dataset.id;

  // 🔥 sécurité stricte
  if(!planId || price <= 0){
    console.warn("Invalid forfait data");
    return;
  }

  const cards = document.querySelectorAll(".tz-forfait-card");

  // ---------------------------
  // UX: loading state
  // ---------------------------
  cards.forEach(b=>{
    b.classList.remove("is-selected");
    b.disabled = true;
    b.style.opacity = "0.6";
  });

  btn.classList.add("is-selected");
  btn.style.opacity = "1";

  try{

    const res = await fetch("/recharge/select-forfait",{
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        id: planId,
        gb: gb,
        price: price
      })
    });

    if(!res.ok){
      throw new Error("Network error");
    }

    const data = await res.json();

    if(data.ok){
      // 🔥 UX: micro delay smooth
      setTimeout(()=>{
        window.location.href = "/recharge/select-amount";
      }, 120);
      return;
    }

    throw new Error("API error");

  } catch(e){

    console.error("❌ forfait selection error:", e);

    // ---------------------------
    // rollback UX
    // ---------------------------
    cards.forEach(b=>{
      b.disabled = false;
      b.style.opacity = "1";
      b.classList.remove("is-selected");
    });

    // toast si dispo
    if(typeof tzToast === "function"){
      tzToast("Erreur, réessayez");
    }
  }
}


// ---------------------------
// Tabs filter (FINAL CLEAN)
// ---------------------------

document.addEventListener("DOMContentLoaded", () => {

  const tabs = document.querySelectorAll(".tz-tab");
  const plans = document.querySelectorAll(".tz-forfait-card");

  if(!tabs.length || !plans.length) return;

  const matchPlan = (type, planType) => {

    if(type === "DATA") return planType.includes("DATA");

    if(type === "VOICE"){
      return planType.includes("VOICE") || planType.includes("MIN");
    }

    if(type === "SMS") return planType.includes("SMS");

    if(type === "COMBO"){
      return planType.includes("COMBO") || planType.includes("BUNDLE");
    }

    return true;
  };

  tabs.forEach(tab => {

    tab.addEventListener("click", () => {

      const type = (tab.dataset.type || "").toUpperCase();

      // active tab
      tabs.forEach(t => t.classList.remove("is-active"));
      tab.classList.add("is-active");

      // filter plans
      plans.forEach(plan => {

        const planType = (plan.dataset.planType || "").toUpperCase();

        const show = matchPlan(type, planType);

        plan.style.display = show ? "block" : "none";
      });

    });

  });

  // 🔥 auto trigger
  document.querySelector(".tz-tab.is-active")?.click();
});