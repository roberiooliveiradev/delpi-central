/** IDs seguros para mermaid.render — React useId() inclui `:` e quebra seletores CSS. */
export function sanitizeMermaidRenderId(rawId: string): string {
  const cleaned = String(rawId || "")
    .replace(/[^a-zA-Z0-9_-]/g, "_")
    .replace(/^_+|_+$/g, "");
  if (!cleaned) return "tm_mermaid";
  if (/^\d/.test(cleaned)) return `tm_${cleaned}`;
  return cleaned;
}

function flowchartNodeCount(svg: string): number {
  return (String(svg || "").match(/\bclass="node(?:\s|")/g) ?? []).length;
}

/** Mermaid 11 frequentemente devolve SVG de erro em vez de rejeitar a Promise. */
export function isMermaidErrorSvg(svg: string): boolean {
  const normalized = String(svg || "");
  const hasErrorMarker =
    /Syntax error/i.test(normalized) ||
    /class="error-icon"/i.test(normalized) ||
    /class='error-icon'/i.test(normalized) ||
    /class="error-text"/i.test(normalized) ||
    /class='error-text'/i.test(normalized);
  if (!hasErrorMarker) return false;
  // Sandbox/htmlLabels às vezes injetam um error-icon residual num flowchart válido.
  return flowchartNodeCount(normalized) === 0;
}

function decodeMermaidSandboxSrc(src: string): string | null {
  const data = String(src || "").trim();
  const base64 = data.match(/^data:text\/html(?:;charset=[^;,]+)?;base64,(.+)$/i);
  if (base64) {
    try {
      const binary = atob(base64[1]);
      if (typeof TextDecoder !== "undefined") {
        return new TextDecoder("utf-8").decode(
          Uint8Array.from(binary, (char) => char.charCodeAt(0))
        );
      }
      return binary;
    } catch {
      return null;
    }
  }
  const plain = data.match(/^data:text\/html(?:;charset=[^;,]+)?,(.+)$/i);
  if (!plain) return null;
  try {
    return decodeURIComponent(plain[1]);
  } catch {
    return plain[1];
  }
}

/**
 * `securityLevel: "sandbox"` faz mermaid.render() devolver <iframe src="data:...">.
 * O viewport precisa do SVG interno; senão parseia o ícone Lucide (24×24) e o fit vira 135%.
 */
export function unwrapMermaidRenderSvg(raw: string): string {
  const trimmed = String(raw || "").trim();
  if (!trimmed) return trimmed;
  if (/^<svg[\s>]/i.test(trimmed)) return trimmed;

  const src = trimmed.match(/<iframe\b[^>]*\ssrc=["']([^"']+)["']/i)?.[1];
  if (!src) return trimmed;
  const decoded = decodeMermaidSandboxSrc(src);
  if (!decoded) return trimmed;
  const svg = decoded.match(/<svg\b[\s\S]*<\/svg>/i)?.[0];
  return svg || trimmed;
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
