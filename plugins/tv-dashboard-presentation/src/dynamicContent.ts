import type { ComunicadoTextDataRef } from "./comunicadoTypes";

/**
 * Catálogo de conteúdo dinâmico inserível em texto / Grade.
 * North star: um fluxo único (`{ }`) → kind → payload; `data_field` amarra ao modelo de dados.
 * Outros kinds ficam scaffold até a engine existir.
 */
export type DynamicContentKind = "data_field" | "conditional_text" | "expression";

export type DynamicContentDataField = {
  kind: "data_field";
  dataRef: ComunicadoTextDataRef;
};

/** Scaffold — critérios if/then; ainda não resolvido no render. */
export type DynamicContentConditionalText = {
  kind: "conditional_text";
  label?: string;
  /** Placeholder para regras futuras (não interpretado na v1). */
  criteria?: unknown[];
  fallback?: string;
};

/** Scaffold — expressão / fórmula de texto. */
export type DynamicContentExpression = {
  kind: "expression";
  label?: string;
  expression?: string;
};

export type DynamicContentSpec =
  | DynamicContentDataField
  | DynamicContentConditionalText
  | DynamicContentExpression;

export type DynamicContentKindDescriptor = {
  kind: DynamicContentKind;
  label: string;
  description: string;
  /** false = UI lista o tipo, mas a inserção ainda não aplica payload. */
  implemented: boolean;
};

export const DYNAMIC_CONTENT_KIND_CATALOG: readonly DynamicContentKindDescriptor[] = [
  {
    kind: "data_field",
    label: "Campo do modelo de dados",
    description: "Valor da fonte ligada ao bloco ou à célula (ex.: OEE, PPM).",
    implemented: true,
  },
  {
    kind: "conditional_text",
    label: "Texto condicional",
    description: "Texto que muda segundo critérios (em breve).",
    implemented: false,
  },
  {
    kind: "expression",
    label: "Expressão",
    description: "Texto calculado a partir de campos ou fórmulas (em breve).",
    implemented: false,
  },
] as const;

export function dynamicContentKindDescriptor(
  kind: DynamicContentKind,
): DynamicContentKindDescriptor {
  return (
    DYNAMIC_CONTENT_KIND_CATALOG.find((item) => item.kind === kind) ??
    DYNAMIC_CONTENT_KIND_CATALOG[0]
  );
}

export function isDynamicContentKindImplemented(kind: DynamicContentKind): boolean {
  return dynamicContentKindDescriptor(kind).implemented;
}

export function dataRefToDynamicContent(dataRef: ComunicadoTextDataRef): DynamicContentDataField {
  return { kind: "data_field", dataRef };
}

export function dynamicContentToDataRef(
  spec: DynamicContentSpec,
): ComunicadoTextDataRef | null {
  if (spec.kind !== "data_field") return null;
  const field = spec.dataRef.field?.trim();
  if (!field) return null;
  return { ...spec.dataRef, field };
}
