let eficienciaFabrilNavStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    eficienciaFabrilNavStackDepth = Math.max(0, eficienciaFabrilNavStackDepth - 1);
  });
}

export function navigateEficienciaFabril(path: string) {
  const target = path.startsWith("/") ? path : `/${path}`;

  if (window.location.pathname + window.location.search === target) {
    return;
  }

  window.history.pushState(null, "", target);
  eficienciaFabrilNavStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateEficienciaFabrilBack(fallbackPath: string) {
  if (typeof window === "undefined") return;

  if (eficienciaFabrilNavStackDepth > 0) {
    window.history.back();
    return;
  }

  navigateEficienciaFabril(fallbackPath);
}
