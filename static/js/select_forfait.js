// ---------------------------
// Select forfait (UX + SAFE + DATA FIX)
// ---------------------------

async function selectForfait(btn){

  if(!btn) return

  const gb = btn.dataset.gb
  const price = btn.dataset.price
  const planId = btn.dataset.id   // 🔥 CRITIQUE

  if(!gb || !price) return

  const cards = document.querySelectorAll(".tz-forfait-card")

  // 🔥 UX: disable all + reset
  cards.forEach(b=>{
    b.classList.remove("is-selected")
    b.disabled = true
  })

  btn.classList.add("is-selected")

  try{

    const res = await fetch("/recharge/select-forfait",{
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        id: planId,   // 🔥 AJOUT
        gb,
        price
      })
    })

    if(!res.ok){
      throw new Error("Network error")
    }

    const data = await res.json()

    if(data.ok){
      window.location.href = "/recharge/select-amount"
      return
    }

    throw new Error("API error")

  } catch(e){

    console.error("forfait selection error", e)

    // 🔁 rollback UX
    cards.forEach(b=>{
      b.disabled = false
      b.classList.remove("is-selected")
    })
  }
}


// ---------------------------
// Tabs filter (SAFE + CLEAN)
// ---------------------------

document.addEventListener("DOMContentLoaded", () => {

  const tabs = document.querySelectorAll(".tz-tab")
  const plans = document.querySelectorAll(".tz-forfait-card")

  if(!tabs.length || !plans.length) return

  const matchPlan = (type, planType) => {

    if(type === "DATA") return planType.includes("DATA")

    if(type === "VOICE") {
      return planType.includes("VOICE") || planType.includes("MIN")
    }

    if(type === "SMS") return planType.includes("SMS")

    if(type === "COMBO") {
      return planType.includes("COMBO") || planType.includes("BUNDLE")
    }

    return true
  }

  tabs.forEach(tab => {

    tab.addEventListener("click", () => {

      const type = (tab.dataset.type || "").toUpperCase()

      tabs.forEach(t => t.classList.remove("is-active"))
      tab.classList.add("is-active")

      plans.forEach(plan => {

        const planType = (plan.dataset.planType || "").toUpperCase()

        const show = matchPlan(type, planType)

        plan.style.display = show ? "block" : "none"
      })
    })
  })

  // auto trigger first tab
  document.querySelector(".tz-tab.is-active")?.click()
})