import { lookupPtBr, translateBpmnTypeName } from "./ptBR";

/**
 * Serviço `translate` oficial do diagram-js: função injetada via
 * `additionalModules` que recebe o template EN do vendor (com
 * placeholders `{key}`) e devolve PT-BR.
 *
 * Assinatura idêntica ao stub do vendor (translate.js do diagram-js):
 * não traduzido → template original (fallback seguro, nunca quebra).
 */
export function translate(
  template: string,
  replacements?: Record<string, string>,
): string {
  const translated = lookupPtBr(template);
  const params = replacements ?? {};
  return translated.replace(/{([^}]+)}/g, (_, key: string) =>
    params[key] ?? `{${key}}`,
  );
}

/** Módulo didi que sobrescreve o stub `translate` do vendor. */
export const ptBrTranslateModule = {
  translate: ["value", translate],
};

/**
 * Nome amigável PT-BR para o `element.type` bruto do moddle
 * (ex.: "bpmn:StartEvent" → "Evento inicial"). Uso: ElementInspector
 * (read-only), que é product-owned e não passa pelo serviço vendor.
 */
export function bpmnTypeLabel(moddleType: string): string {
  const raw = moddleType.includes(":")
    ? moddleType.slice(moddleType.indexOf(":") + 1)
    : moddleType;
  // mesma normalização do vendor: CamelCase → espaçado
  const spaced = raw.replace(/(\B[A-Z])/g, " $1");
  return translateBpmnTypeName(spaced);
}
