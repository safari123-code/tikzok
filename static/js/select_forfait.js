// ---------------------------
// Select forfait
// ---------------------------

async function selectForfait(btn){

  const gb = btn.dataset.gb
  const price = btn.dataset.price

  try{

    const res = await fetch("/recharge/select-forfait",{
      method:"POST",
      headers:{
        "Content-Type":"application/json"
      },
      body:JSON.stringify({
        gb:gb,
        price:price
      })
    })

    const data = await res.json()

    if(data.ok){
      window.location.href="/recharge/select-amount"
    }

  }catch(e){
    console.error("forfait selection error", e)
  }

}


// ---------------------------
// Tabs filter
// ---------------------------

document.addEventListener("DOMContentLoaded", () => {

  const tabs = document.querySelectorAll(".tz-tab")
  const plans = document.querySelectorAll(".tz-forfait-card")

  tabs.forEach(tab => {

    tab.addEventListener("click", () => {

      const type = tab.dataset.type

      tabs.forEach(t => t.classList.remove("is-active"))
      tab.classList.add("is-active")

      plans.forEach(plan => {

        const planType = (plan.dataset.planType || "").toUpperCase()

        let show = false

        if(type === "DATA"){
          show = planType.includes("DATA")
        }

        if(type === "VOICE"){
          show = planType.includes("VOICE") || planType.includes("MIN")
        }

        if(type === "SMS"){
          show = planType.includes("SMS")
        }

        if(type === "COMBO"){
          show = planType.includes("COMBO") || planType.includes("BUNDLE")
        }

        plan.style.display = show ? "block" : "none"

      })

    })

  })

  document.querySelector(".tz-tab.is-active")?.click()

})