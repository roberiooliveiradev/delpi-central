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

/** Remove tags perigosas no cliente (defesa em profundidade; servidor permanece canônico). */
export function stripDangerousRichTextTags(html: string): string {
  const raw = html || "";
  if (!raw.trim()) return "<p></p>";
  try {
    const doc = new DOMParser().parseFromString(raw, "text/html");
    doc.querySelectorAll([...DANGEROUS_TAGS].join(",")).forEach((el) => el.remove());
    return wrapOrphanRichTextNodes(doc.body.innerHTML || "<p></p>");
  } catch {
    const stripped = raw
      .replace(/<(script|style|iframe|object|embed|form)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, "")
      .replace(/<(script|style|iframe|object|embed|form)\b[^>]*\/?>/gi, "");
    return wrapOrphanRichTextNodes(stripped);
  }
}
