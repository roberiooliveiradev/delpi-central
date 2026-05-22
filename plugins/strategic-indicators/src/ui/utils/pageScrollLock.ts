const PORTAL_CONTENT_SELECTOR = ".main-area .content, .content";

/**
 * Trava scroll da página ao abrir gaveta/modal.
 * O portal DELPI rola em `.content`, não só em `document.body`.
 */
export function lockPageScroll(): () => void {
  const previousBodyOverflow = document.body.style.overflow;
  document.body.style.overflow = "hidden";

  const contentElement = document.querySelector(PORTAL_CONTENT_SELECTOR);
  const previousContentOverflow =
    contentElement instanceof HTMLElement ? contentElement.style.overflow : "";

  if (contentElement instanceof HTMLElement) {
    contentElement.style.overflow = "hidden";
  }

  return () => {
    document.body.style.overflow = previousBodyOverflow;
    if (contentElement instanceof HTMLElement) {
      contentElement.style.overflow = previousContentOverflow;
    }
  };
}
