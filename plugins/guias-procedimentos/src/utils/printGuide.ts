export function printGuide() {
  if (typeof window === "undefined") return;
  requestAnimationFrame(() => window.print());
}
