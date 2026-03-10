async function loadOperators() {

  const res = await fetch("/recharge/api/operators");

  const data = await res.json();

  if (!data.ok) return;

  const list = document.getElementById("operatorList");

  list.innerHTML = "";

  data.operators.forEach(op => {

    const row = document.createElement("div");

    row.className = "tz-card tz-operator-row";

    row.innerHTML = `
      <div class="tz-row">
        ${op.logo_url ? `<img src="${op.logo_url}" style="width:34px;height:34px;">` : "📶"}
        <div class="tz-grow">${op.name}</div>
        <span>›</span>
      </div>
    `;

    list.appendChild(row);
  });

}

document.addEventListener("DOMContentLoaded", loadOperators);