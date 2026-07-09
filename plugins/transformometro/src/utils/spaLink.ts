import type { MouseEvent as ReactMouseEvent } from "react";

export function shouldInterceptSpaLinkClick(event: ReactMouseEvent<HTMLAnchorElement>): boolean {
  if (event.defaultPrevented) return false;
  if (event.button !== 0) return false;
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
  return true;
}

export function handleSpaLinkClick(
  event: ReactMouseEvent<HTMLAnchorElement>,
  href: string,
  onNavigate: (path: string) => void
): void {
  if (!shouldInterceptSpaLinkClick(event)) return;
  event.preventDefault();
  onNavigate(href);
}
