/**
 * Sanitização defensiva de HTML (DOMPurify).
 * Allowlist alinhada ao GuideHtmlSanitizer da api-delpi.
 */
import DOMPurify from "dompurify";

const ALLOWED_TAGS = [
  "h2",
  "h3",
  "h4",
  "h5",
  "p",
  "br",
  "strong",
  "em",
  "b",
  "i",
  "ul",
  "ol",
  "li",
  "blockquote",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "a",
  "div",
  "span",
  "figure",
  "figcaption",
  "img",
  "video",
];

const ALLOWED_ATTR = [
  "href",
  "title",
  "target",
  "rel",
  "colspan",
  "rowspan",
  "class",
  "src",
  "alt",
  "loading",
  "controls",
  "preload",
  "playsinline",
];

const ALLOWED_CLASSES = new Set([
  "gp-callout",
  "gp-emphasis",
  "guide-media",
  "guide-media--image",
  "guide-media--video",
  "guide-media--video-external",
  "guide-media__link",
  "guide-attachment",
  "guide-attachment__link",
]);

const PROTECTED_MEDIA_SRC =
  /^\/(?:apps\/api-delpi\/)?guias-procedimentos\/media\/[0-9a-fA-F-]{36}\/file$/;

export function sanitizeGuideHtml(rawHtml: string): string {
  if (!rawHtml) return "";

  const cleaned = DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto):|\/|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i,
    ALLOW_DATA_ATTR: false,
  });

  if (typeof document === "undefined") {
    return cleaned;
  }

  const container = document.createElement("div");
  container.innerHTML = cleaned;
  container.querySelectorAll("[class]").forEach((node) => {
    const el = node as HTMLElement;
    const kept = (el.getAttribute("class") || "")
      .split(/\s+/)
      .filter((token) => ALLOWED_CLASSES.has(token));
    if (kept.length === 0) {
      el.removeAttribute("class");
    } else {
      el.setAttribute("class", kept.join(" "));
    }
  });

  container.querySelectorAll("img, video").forEach((node) => {
    const el = node as HTMLImageElement | HTMLVideoElement;
    const src = (el.getAttribute("src") || "").trim();
    if (!PROTECTED_MEDIA_SRC.test(src)) {
      el.remove();
    }
  });

  return container.innerHTML;
}
