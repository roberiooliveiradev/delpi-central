let scrapNavStackDepth = 0;
let suppressPopstateDepthChange = false;

if (typeof window !== "undefined") {
  window.addEventListener("popstate", () => {
    if (suppressPopstateDepthChange) return;
    scrapNavStackDepth = Math.max(0, scrapNavStackDepth - 1);
  });
}

export function navigateScrap(path: string) {
  const questionIndex = path.indexOf("?");
  const basePath = questionIndex >= 0 ? path.slice(0, questionIndex) : path;
  const query = questionIndex >= 0 ? path.slice(questionIndex) : "";

  if (window.location.pathname === basePath && window.location.search === query) {
    return;
  }

  window.history.pushState(null, "", path);
  scrapNavStackDepth += 1;
  suppressPopstateDepthChange = true;
  window.dispatchEvent(new PopStateEvent("popstate"));
  suppressPopstateDepthChange = false;
}

export function navigateScrapBack(fallbackPath: string) {
  if (typeof window === "undefined") return;

  if (scrapNavStackDepth > 0) {
    window.history.back();
    return;
  }

  navigateScrap(fallbackPath);
}
