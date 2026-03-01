// themes/delpi-energy/login/resources/js/lightning.js
(function () {
  const svg = document.querySelector(".lightning-svg");
  const card = document.querySelector(".login-energy-card");

  if (!svg || !card) return;

  function random(min, max) {
    return Math.random() * (max - min) + min;
  }

  function generateLightning(width, height) {
    const lines = [];
    const count = Math.floor(random(3, 6));

    for (let i = 0; i < count; i++) {
      const startLeft = Math.random() > 0.5;
      const yBase = random(height * 0.3, height * 0.7);
      const segments = 8;

      let x = startLeft ? 0 : width;
      let y = yBase;

      let d = `M ${x} ${y}`;
      const branches = [];

      for (let s = 0; s < segments; s++) {
        const stepX = width / segments;
        const dir = startLeft ? 1 : -1;

        x += stepX * dir;
        y += random(-40, 40);

        d += ` L ${x} ${y}`;

        if (Math.random() > 0.7) {
          const branchX = x + random(-80, 80);
          const branchY = y + random(-80, 80);
          branches.push(`M ${x} ${y} L ${branchX} ${branchY}`);
        }
      }

      lines.push({ d, branches });
    }

    return lines;
  }

  function renderLightning() {
    const width = window.innerWidth;
    const height = window.innerHeight;

    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";

    const lightning = generateLightning(width, height);

    lightning.forEach((line) => {
      const main = document.createElementNS("http://www.w3.org/2000/svg", "path");
      main.setAttribute("d", line.d);
      main.setAttribute("class", "lightning-line");
      svg.appendChild(main);

      line.branches.forEach((b) => {
        const branch = document.createElementNS("http://www.w3.org/2000/svg", "path");
        branch.setAttribute("d", b);
        branch.setAttribute("class", "lightning-branch");
        svg.appendChild(branch);
      });
    });

    // choque no card
    card.classList.remove("lightning-hit");
    void card.offsetWidth;
    card.classList.add("lightning-hit");
  }

  // ✅ 1) Entrada do card
  card.classList.add("card-enter");
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      card.classList.remove("card-enter");
    });
  });

  // ✅ 2) Só começa os raios depois da entrada (pra não roubar o efeito)
  setTimeout(() => {
    renderLightning();
    setInterval(renderLightning, 2000);
  }, 500);
})();