/** IDs seguros para mermaid.render — React useId() inclui `:` e quebra seletores CSS. */
export function sanitizeMermaidRenderId(rawId: string): string {
  const cleaned = String(rawId || "")
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .replace(/^_+|_+$/g, "");
  if (!cleaned) return "tm_mermaid";
  if (/^\d/.test(cleaned)) return `tm_${cleaned}`;
  return cleaned;
}

/** Mermaid 11 frequentemente devolve SVG de erro em vez de rejeitar a Promise. */
export function isMermaidErrorSvg(svg: string): boolean {
  const normalized = String(svg || "");
  return (
    /Syntax error/i.test(normalized) ||
    /class="error-icon"/i.test(normalized) ||
    /class='error-icon'/i.test(normalized) ||
    /class="error-text"/i.test(normalized) ||
    /class='error-text'/i.test(normalized)
  );
}

/**
 * Remove nós temporários que o Mermaid anexa ao document.body
 * (`#d{renderId}` / `#i{renderId}`). Evita SVG de erro órfão na página.
 */
export function cleanupMermaidRenderArtifacts(renderId: string): void {
  if (typeof document === "undefined") return;
  const id = sanitizeMermaidRenderId(renderId);
  for (const prefix of ["d", "i", ""]) {
    const el = document.getElementById(`${prefix}${id}`);
    if (el?.parentNode) {
      el.parentNode.removeChild(el);
    }
  }
}
