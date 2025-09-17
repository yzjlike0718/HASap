(async function () {
  const YEAR = new Date().getFullYear();
  document.getElementById("year").textContent = YEAR;

  const DATA_URL = "assets/mos_demo.json";
  let allData = [];
  try {
    const resp = await fetch(DATA_URL, { cache: "no-store" });
    allData = await resp.json();
  } catch (e) {
    console.error("加载数据失败:", e);
  }

  const grid = document.getElementById("grid");
  const searchInput = document.getElementById("search");
  const sysFilters = [...document.querySelectorAll(".sys-filter")];
  const resetBtn = document.getElementById("reset");

  function systemFilterSet() {
    return new Set(sysFilters.filter(cb => cb.checked).map(cb => cb.value));
  }

  function matchKeyword(entry, kw) {
    if (!kw) return true;
    kw = kw.toLowerCase();
    return (
      (entry.set_id || "").toLowerCase().includes(kw) ||
      (entry.base_name || "").toLowerCase().includes(kw) ||
      (entry.transcript || "").toLowerCase().includes(kw)
    );
  }

  function filteredItems(entry, sysSet) {
    return entry.items.filter(it => sysSet.has(it.system));
  }

  function render(data) {
    grid.innerHTML = "";
    data.forEach(entry => {
      const wrap = document.createElement("article");
      wrap.className = "card";

      const h = document.createElement("div");
      h.className = "meta";
      h.innerHTML = `
        <span class="badge">Set ${entry.set_id}</span>
        <span>Base: ${entry.base_name}</span>
      `;
      wrap.appendChild(h);

      const t = document.createElement("div");
      t.className = "transcript";
      t.textContent = entry.transcript || "";
      wrap.appendChild(t);

      const players = document.createElement("div");
      players.className = "players";

      // 固定顺序 A/B/C/D
      const byCode = Object.fromEntries(entry.items.map(it => [it.item_code, it]));
      ["A", "B", "C", "D"].forEach(code => {
        const it = byCode[code];
        if (!it) return;
        const p = document.createElement("div");
        p.className = "player";
        p.dataset.system = it.system;

        const label = document.createElement("div");
        label.className = "label";
        label.innerHTML = `<strong>${code}</strong><span>${it.system}</span>`;
        p.appendChild(label);

        const audio = document.createElement("audio");
        audio.controls = true;
        audio.src = it.file;
        audio.preload = "none";
        p.appendChild(audio);

        players.appendChild(p);
      });

      wrap.appendChild(players);
      grid.appendChild(wrap);
    });
  }

  function applyFilters() {
    const kw = (searchInput.value || "").trim();
    const sysSet = systemFilterSet();

    const view = allData
      .map(entry => {
        const clone = { ...entry, items: filteredItems(entry, sysSet) };
        return clone;
      })
      .filter(entry => matchKeyword(entry, kw))
      // 如果一个卡片里所有系统都被过滤掉，不显示该卡
      .filter(entry => entry.items.length > 0);

    render(view);
  }

  // 初始渲染
  render(allData);

  // 交互
  searchInput.addEventListener("input", applyFilters);
  sysFilters.forEach(cb => cb.addEventListener("change", applyFilters));
  resetBtn.addEventListener("click", () => {
    searchInput.value = "";
    sysFilters.forEach(cb => cb.checked = true);
    applyFilters();
  });
})();
