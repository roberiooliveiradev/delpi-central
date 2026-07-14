/**
 * Registry canônico de blocos complexos (KPI / gráfico / tabela / filtro).
 * Escala tipográfica no resize, drag e chrome de parte usam este ponto de verdade.
 */

import type { ComunicadoBlock } from "./comunicadoTypes";

export const COMPLEX_VIEW_BLOCK_TYPES = [
  "kpi_view",
  "chart_view",
  "table_view",
  "input",
] as const;

export type ComplexViewBlockType = (typeof COMPLEX_VIEW_BLOCK_TYPES)[number];

export type ComplexViewBlock = Extract<ComunicadoBlock, { type: ComplexViewBlockType }>;

export function isComplexViewBlockType(type: string): type is ComplexViewBlockType {
  return (COMPLEX_VIEW_BLOCK_TYPES as readonly string[]).includes(type);
}

export function isComplexViewBlock(block: ComunicadoBlock): block is ComplexViewBlock {
  return isComplexViewBlockType(block.type);
}
