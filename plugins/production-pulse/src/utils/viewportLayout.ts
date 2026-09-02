import type { ViewportBucket } from "./deviceDisplay";

/** Mobile + tablet — formulários com footer sticky e alvos touch maiores. */
export function isCompactViewport(viewport: ViewportBucket): boolean {
  return viewport === "mobile" || viewport === "tablet";
}

export function isMobileViewport(viewport: ViewportBucket): boolean {
  return viewport === "mobile";
}
