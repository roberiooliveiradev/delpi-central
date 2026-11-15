/** Catálogo único de campos de Produtos acompanhados — mesma fonte
 * para Tabela e Cards. Preferências (`engineering:prc:products:columns`)
 * controlam visibilidade e ordem nos dois modos; o código oficial é a
 * identidade e permanece sempre acessível. */

import { PRC_PRODUCTS_COPY } from "./prcCopy";

export const PRC_PRODUCT_FIELD_KEYS = [
  "officialCode",
  "description",
  "currentRevisionNumber",
  "openFlagCount",
  "lastEvolution",
] as const;

export type PrcProductFieldKey = (typeof PRC_PRODUCT_FIELD_KEYS)[number];

export const PRC_PRODUCT_FIELD_LABELS: Record<PrcProductFieldKey, string> = {
  officialCode: PRC_PRODUCTS_COPY.colCode,
  description: PRC_PRODUCTS_COPY.colDescription,
  currentRevisionNumber: PRC_PRODUCTS_COPY.colVersion,
  openFlagCount: PRC_PRODUCTS_COPY.colOpenFlags,
  lastEvolution: PRC_PRODUCTS_COPY.colLastEvolution,
};

export const PRC_PRODUCT_COLUMN_CATALOG = PRC_PRODUCT_FIELD_KEYS.map(
  (key) => ({ key, label: PRC_PRODUCT_FIELD_LABELS[key] }),
);

export function isPrcProductFieldKey(
  value: string,
): value is PrcProductFieldKey {
  return (PRC_PRODUCT_FIELD_KEYS as readonly string[]).includes(value);
}

/** Tom visual do campo no card — identidade dominante; métricas de
 * versão/bandeiras em destaque; descrição e data como metadado. */
export type PrcProductCardFieldTone = "title" | "value" | "meta";

export function prcProductCardFieldTone(
  key: PrcProductFieldKey,
): PrcProductCardFieldTone {
  if (key === "officialCode") return "title";
  if (key === "currentRevisionNumber" || key === "openFlagCount") {
    return "value";
  }
  return "meta";
}
