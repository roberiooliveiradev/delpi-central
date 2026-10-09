/**
 * text-fit-v1 — dimensionamento de elementos BPMN guiado pelo texto.
 *
 * Problema (G9): task 100×80 (default vendor) força 5–7 linhas quebradas
 * em rótulos longos. O auto-layout mede o rótulo antes do ELK e cresce o
 * elemento — largura primeiro (wrap natural por palavra), altura pelo
 * número de linhas resultante. Nunca encolhe bounds DI existentes
 * maiores que o fit (grow-only — não destrói sizing manual do usuário).
 *
 * Métrica determinística por classe de caractere — nenhuma medição DOM
 * (Worker/jsdom-safe, output estável → preview e ops reproduzíveis).
 */

import { LAYOUT_PROFILE_V1 } from "./layoutProfile";

/** Largura estimada de um caractere em em-fração do fontSize.
 *  Tabela calibrada para Arial 12px (fonte padrão do renderer bpmn-js);
 *  superestimar ligeiramente é preferível a clipping. */
function charWidthFactor(ch: string): number {
  if ("ilIjtf.,:;'!| ".includes(ch)) return 0.3;
  if ("mwMW@#%&".includes(ch)) return 0.85;
  if (ch >= "A" && ch <= "Z") return 0.7;
  return 0.55;
}

export function estimateTextWidth(text: string, fontSize: number): number {
  let width = 0;
  for (const ch of text) width += charWidthFactor(ch) * fontSize;
  return width;
}

export type WrapResult = {
  lines: number;
  /** Largura real da linha mais larga após o wrap. */
  maxLineWidth: number;
};

/** Word-wrap determinístico: acumula palavras até estourar availWidth;
 *  palavra individual maior que availWidth vira linha própria (renderer
 *  quebra dentro da palavra — a caixa cresce até caber a maior palavra). */
export function wrapText(
  text: string,
  availWidth: number,
  fontSize: number,
): WrapResult {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (!words.length) return { lines: 1, maxLineWidth: 0 };
  const spaceWidth = charWidthFactor(" ") * fontSize;
  let lines = 1;
  let lineWidth = 0;
  let maxLineWidth = 0;
  for (const word of words) {
    const w = estimateTextWidth(word, fontSize);
    if (lineWidth > 0 && lineWidth + spaceWidth + w > availWidth) {
      maxLineWidth = Math.max(maxLineWidth, lineWidth);
      lines += 1;
      lineWidth = w;
    } else {
      lineWidth = lineWidth > 0 ? lineWidth + spaceWidth + w : w;
    }
  }
  maxLineWidth = Math.max(maxLineWidth, lineWidth);
  return { lines, maxLineWidth };
}

export type TextFitSize = {
  width: number;
  height: number;
  lines: number;
};

/** Tamanho mínimo para o rótulo caber com wrap natural.
 *
 *  Estratégia: busca a menor largura em [minWidth, maxWidth] que produz
 *  ≤ maxLines; se nem maxWidth resolve, fixa maxWidth e deixa a altura
 *  crescer até maxHeight. A largura final acomoda também a maior palavra
 *  única (evita quebra intra-palavra quando possível). */
export function fitTextSize(
  text: string,
  cfg = LAYOUT_PROFILE_V1.textFit,
): TextFitSize {
  const { fontSize, padX, padY, lineHeight, minWidth, maxWidth, maxLines, maxHeight } =
    cfg;
  if (!text.trim()) return { width: minWidth, height: cfg.minHeight, lines: 1 };

  const wrapAt = (w: number) => wrapText(text, Math.max(w - padX * 2, 8), fontSize);
  const longestWord = Math.max(
    ...text.trim().split(/\s+/).map((w) => estimateTextWidth(w, fontSize)),
  );

  // Menor largura que atinge maxLines — busca binária discreta (1px).
  let lo: number = minWidth;
  let hi: number = maxWidth;
  let best: number = hi;
  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (wrapAt(mid).lines <= maxLines) {
      best = mid;
      hi = mid - 1;
    } else {
      lo = mid + 1;
    }
  }
  // Acomoda a maior palavra sem clipping (quando o maxWidth permite).
  const needed = Math.ceil(longestWord + padX * 2);
  const width: number = Math.max(
    minWidth,
    Math.min(maxWidth, Math.max(best, needed)),
  );
  const { lines } = wrapAt(width);
  const height: number = Math.min(
    maxHeight,
    Math.max(cfg.minHeight, Math.ceil(lines * lineHeight + padY * 2)),
  );
  return { width, height, lines };
}

/** Famílias cujo rótulo vive DENTRO da shape — candidatas a text-fit.
 *  Eventos/gateways têm label externa (bounds próprios) — nunca redimensionar
 *  pela label aqui. */
const TEXT_FIT_TYPES = new Set([
  "task",
  "userTask",
  "serviceTask",
  "scriptTask",
  "manualTask",
  "businessRuleTask",
  "sendTask",
  "receiveTask",
  "callActivity",
  "textAnnotation",
  "subProcess",
  "transaction",
  "adHocSubProcess",
  "eventSubProcess",
]);

export function isTextFitNodeType(bpmnType: string): boolean {
  return TEXT_FIT_TYPES.has(bpmnType.replace(/^bpmn:/, ""));
}
