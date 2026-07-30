import type { LucideIcon } from "lucide-react";
import {
  Columns3,
  Grid3x3,
  Heading2,
  PanelLeft,
  PanelRight,
  Rows3,
  Sigma,
  Type,
  X,
} from "lucide-react";
import {
  TABLE_ELEMENT_CATALOG,
  isTableElementEnabled,
  setTableElementEnabled,
  type ComunicadoTableOptions,
  type TableElementId,
} from "@delpi/tv-dashboard-presentation";

export type TableAddElementChoiceId = `${TableElementId}:on` | `${TableElementId}:off`;

export type TableAddElementFlyoutChoice = {
  id: TableAddElementChoiceId;
  label: string;
  icon: LucideIcon;
};

export type TableAddElementMenuRoot = {
  elementId: TableElementId;
  label: string;
  icon: LucideIcon;
  moreOptionsLabel: string;
  choices: TableAddElementFlyoutChoice[];
};

const ROOT_META: Record<
  TableElementId,
  { icon: LucideIcon; moreOptionsLabel: string; shortLabel: string }
> = {
  tableTitle: {
    icon: Type,
    shortLabel: "Título",
    moreOptionsLabel: "Mais opções de título…",
  },
  header: {
    icon: Heading2,
    shortLabel: "Cabeçalho",
    moreOptionsLabel: "Mais opções de cabeçalho…",
  },
  totalRow: {
    icon: Sigma,
    shortLabel: "Totais",
    moreOptionsLabel: "Mais opções de totais…",
  },
  firstColumn: {
    icon: PanelLeft,
    shortLabel: "1ª coluna",
    moreOptionsLabel: "Mais opções da primeira coluna…",
  },
  lastColumn: {
    icon: PanelRight,
    shortLabel: "Última coluna",
    moreOptionsLabel: "Mais opções da última coluna…",
  },
  zebraStripe: {
    icon: Rows3,
    shortLabel: "Linhas alt.",
    moreOptionsLabel: "Mais opções de listras nas linhas…",
  },
  bandedColumns: {
    icon: Columns3,
    shortLabel: "Colunas alt.",
    moreOptionsLabel: "Mais opções de listras nas colunas…",
  },
  borders: {
    icon: Grid3x3,
    shortLabel: "Bordas",
    moreOptionsLabel: "Mais opções de bordas…",
  },
};

/** Ordem PPT-ish / Excel Table Design. */
const ROOT_ORDER: TableElementId[] = [
  "tableTitle",
  "header",
  "totalRow",
  "firstColumn",
  "lastColumn",
  "zebraStripe",
  "bandedColumns",
  "borders",
];

function choicesFor(elementId: TableElementId, showIcon: LucideIcon): TableAddElementFlyoutChoice[] {
  return [
    { id: `${elementId}:on`, label: "Mostrar", icon: showIcon },
    { id: `${elementId}:off`, label: "Ocultar", icon: X },
  ];
}

/**
 * Catálogo UI do menu «Adicionar elemento» da tabela (flyouts Mostrar/Ocultar).
 * Compartilhado ribbon + float `+`.
 */
export function resolveTableAddElementMenuRoots(): TableAddElementMenuRoot[] {
  return ROOT_ORDER.flatMap((elementId) => {
    const def = TABLE_ELEMENT_CATALOG.find((entry) => entry.id === elementId);
    const meta = ROOT_META[elementId];
    if (!def || !meta) return [];
    return [
      {
        elementId,
        label: def.label,
        icon: meta.icon,
        moreOptionsLabel: meta.moreOptionsLabel,
        choices: choicesFor(elementId, meta.icon),
      },
    ];
  });
}

export function parseTableAddElementChoice(choiceId: TableAddElementChoiceId): {
  elementId: TableElementId;
  enabled: boolean;
} {
  const sep = choiceId.lastIndexOf(":");
  const elementId = choiceId.slice(0, sep) as TableElementId;
  const state = choiceId.slice(sep + 1);
  return { elementId, enabled: state === "on" };
}

export function isTableAddElementChoiceActive(
  choiceId: TableAddElementChoiceId,
  options: ComunicadoTableOptions,
): boolean {
  const { elementId, enabled } = parseTableAddElementChoice(choiceId);
  return isTableElementEnabled(elementId, options) === enabled;
}

export function applyTableAddElementChoice(
  choiceId: TableAddElementChoiceId,
  options: ComunicadoTableOptions,
): Partial<ComunicadoTableOptions> {
  const { elementId, enabled } = parseTableAddElementChoice(choiceId);
  return setTableElementEnabled(elementId, enabled);
}
