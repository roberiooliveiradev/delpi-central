import type { ContentFormatKind } from "./assistantContentLayout";
import type { StackTableRole } from "./presentationStackPlan";

export type StackSectionId =
  | "scope"
  | "profile"
  | "highlights"
  | "guide"
  | "inspection"
  | "structure"
  | "attention";

export type StackSectionChrome = {
  id: StackSectionId;
  title: string;
  description: string;
  showIn: Array<ContentFormatKind | "complete">;
};

export const STACK_SECTION_BY_ID: Record<StackSectionId, StackSectionChrome> = {
  scope: {
    id: "scope",
    title: "1. Escopo da consulta",
    description:
      "O que foi pedido e qual produto está em análise — leitura de abertura antes dos dados.",
    showIn: ["complete", "text"],
  },
  profile: {
    id: "profile",
    title: "2. Ficha cadastral",
    description:
      "Primeiro bloco de dados: quem é o produto antes de roteiro, inspeção e BOM. Fonte: cadastro na API.",
    showIn: ["complete", "table"],
  },
  highlights: {
    id: "highlights",
    title: "3. Síntese executiva (Destaques)",
    description:
      "Resumo em bullets após a ficha: leitura rápida do que importa nas demais seções.",
    showIn: ["complete", "text"],
  },
  guide: {
    id: "guide",
    title: "4. Roteiro de produção",
    description:
      "Como o item é fabricado (operações por PA e PIs). Fonte: roteiro na API.",
    showIn: ["complete", "table"],
  },
  inspection: {
    id: "inspection",
    title: "5. Plano de inspeção",
    description:
      "O que a API retorna para inspeção na hierarquia — referências quando QP não vêm preenchidos.",
    showIn: ["complete", "table"],
  },
  structure: {
    id: "structure",
    title: "6. Estrutura (BOM)",
    description:
      "Composição hierárquica PA → PI → MP. Substitui lista em texto e tabela plana de componentes.",
    showIn: ["complete", "tree"],
  },
  attention: {
    id: "attention",
    title: "7. Alertas e divergências",
    description:
      "Riscos e inconsistências depois que o cadastro, roteiro, inspeção e BOM já foram apresentados.",
    showIn: ["complete", "text"],
  },
};

export function stackSectionForRole(role: StackTableRole): StackSectionChrome | null {
  if (role === "guide") {
    return STACK_SECTION_BY_ID.guide;
  }

  if (role === "inspection") {
    return STACK_SECTION_BY_ID.inspection;
  }

  return null;
}

export function isStackSectionVisible(
  section: StackSectionChrome,
  activeKind: ContentFormatKind | null,
): boolean {
  if (activeKind === null) {
    return section.showIn.includes("complete");
  }

  return section.showIn.includes(activeKind);
}
