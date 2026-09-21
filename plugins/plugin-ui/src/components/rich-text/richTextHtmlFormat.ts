const VOID_TAGS = new Set(["br", "hr", "img", "col", "input", "meta", "link"]);

const DANGEROUS_TAGS = new Set(["script", "style", "iframe", "object", "embed", "form"]);

function serializeNode(node: Node, depth: number, lines: string[]): void {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = (node.textContent ?? "").replace(/\s+/g, " ");
    if (!text.trim()) return;
    lines.push(`${"  ".repeat(depth)}${text}`);
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return;

  const el = node as Element;
  const tag = el.tagName.toLowerCase();
  if (DANGEROUS_TAGS.has(tag)) return;

  const attrs = Array.from(el.attributes)
    .map((attr) => ` ${attr.name}="${attr.value.replace(/"/g, "&quot;")}"`)
    .join("");
  const indent = "  ".repeat(depth);
  const isVoid = VOID_TAGS.has(tag);

  if (isVoid) {
    lines.push(`${indent}<${tag}${attrs}>`);
    return;
  }

  const children = Array.from(el.childNodes);
  const onlyTextChild =
    children.length === 1 && children[0]?.nodeType === Node.TEXT_NODE;

  if (onlyTextChild || children.length === 0) {
    const inner = children[0]?.textContent ?? "";
    lines.push(`${indent}<${tag}${attrs}>${inner}</${tag}>`);
    return;
  }

  lines.push(`${indent}<${tag}${attrs}>`);
  for (const child of children) {
    serializeNode(child, depth + 1, lines);
  }
  lines.push(`${indent}</${tag}>`);
}

/** Indentação leve de HTML de bloco para leitura no modo fonte. */
export function prettyPrintRichTextHtml(html: string): string {
  const raw = (html || "").trim();
  if (!raw) return "<p></p>";
  try {
    const doc = new DOMParser().parseFromString(`<div id="__rt_root">${raw}</div>`, "text/html");
    const root = doc.getElementById("__rt_root");
    if (!root) return raw;
    const lines: string[] = [];
    for (const child of Array.from(root.childNodes)) {
      serializeNode(child, 0, lines);
    }
    return lines.length > 0 ? lines.join("\n") : raw;
  } catch {
    return raw;
  }
}

/**
 * Envolve texto solto de nível raiz em `<p>` para o contentEditable aplicar
 * negrito/alinhamento com confiabilidade (execCommand exige bloco).
 */
export function wrapOrphanRichTextNodes(html: string): string {
  const raw = (html || "").trim();
  if (!raw) return "<p></p>";
  try {
    const doc = new DOMParser().parseFromString(
      `<div id="__rt_root">${raw}</div>`,
      "text/html",
    );
    const root = doc.getElementById("__rt_root");
    if (!root) return raw;
    for (const node of Array.from(root.childNodes)) {
      if (node.nodeType !== Node.TEXT_NODE) continue;
      const text = node.textContent ?? "";
      if (!text.trim()) {
        root.removeChild(node);
        continue;
      }
      const p = doc.createElement("p");
      p.textContent = text;
      root.replaceChild(p, node);
    }
    return root.innerHTML.trim() || "<p></p>";
  } catch {
    return raw;
  }
}

const SAFE_URL_PROTOCOLS = new Set(["http:", "https:", "mailto:"]);

function isSafeUrl(value: string): boolean {
  const raw = (value || "").trim();
  if (!raw) return false;
  if (raw.startsWith("#") || raw.startsWith("/") || raw.startsWith("./") || raw.startsWith("../")) {
    return true;
  }
  if (raw.startsWith("attachment:")) return true;
  try {
    const parsed = new URL(raw, "https://example.invalid");
    return SAFE_URL_PROTOCOLS.has(parsed.protocol);
  } catch {
    return false;
  }
}

/** Remove tags/attrs perigosos no cliente (defesa em profundidade). */
export function stripDangerousRichTextTags(html: string): string {
  const raw = html || "";
  if (!raw.trim()) return "<p></p>";
  try {
    const doc = new DOMParser().parseFromString(raw, "text/html");
    doc.querySelectorAll([...DANGEROUS_TAGS].join(",")).forEach((el) => el.remove());
    for (const el of Array.from(doc.body.querySelectorAll("*"))) {
      for (const attr of Array.from(el.attributes)) {
        const name = attr.name.toLowerCase();
        if (name.startsWith("on") || name === "srcdoc") {
          el.removeAttribute(attr.name);
          continue;
        }
        if (name === "href" || name === "src" || name === "xlink:href") {
          if (!isSafeUrl(attr.value)) {
            el.removeAttribute(attr.name);
          }
        }
      }
      if (el.tagName.toLowerCase() === "a") {
        const href = (el.getAttribute("href") || "").trim();
        if (href && /^https?:/i.test(href)) {
          const rel = new Set(
            (el.getAttribute("rel") || "")
              .split(/\s+/)
              .map((part) => part.trim().toLowerCase())
              .filter(Boolean),
          );
          rel.add("noopener");
          rel.add("noreferrer");
          el.setAttribute("rel", Array.from(rel).join(" "));
          if (!el.getAttribute("target")) {
            el.setAttribute("target", "_blank");
          }
        }
      }
    }
    return wrapOrphanRichTextNodes(doc.body.innerHTML || "<p></p>");
  } catch {
    const stripped = raw
      .replace(/<(script|style|iframe|object|embed|form)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, "")
      .replace(/<(script|style|iframe|object|embed|form)\b[^>]*\/?>/gi, "")
      .replace(/\son\w+\s*=\s*(['"]).*?\1/gi, "")
      .replace(/\s(href|src)\s*=\s*(['"])\s*javascript:[^'"]*\2/gi, "");
    return wrapOrphanRichTextNodes(stripped);
  }
}

export function readInlineFontSizePx(el: Element): number | null {
  if (!(el instanceof HTMLElement)) return null;
  const match = (el.style.fontSize || "").match(/^(\d+(?:\.\d+)?)px$/i);
  if (!match) return null;
  const px = Math.round(Number(match[1]));
  return Number.isFinite(px) ? px : null;
}
