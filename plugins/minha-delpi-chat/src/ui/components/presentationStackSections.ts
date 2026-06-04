import type { ContentFormatKind } from "./assistantContentLayout";

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

const SECTION_TITLES: Record<StackSectionId, string> = {
  scope: "1. Escopo da consulta",
  profile: "2. Ficha cadastral",
  highlights: "3. Síntese executiva (Destaques)",
  guide: "4. Roteiro de produção",
  inspection: "5. Plano de inspeção",
  structure: "6. Estrutura (BOM)",
  attention: "7. Alertas e divergências",
};

const SECTION_SHOW_IN: Record<StackSectionId, StackSectionChrome["showIn"]> = {
  scope: ["complete", "text"],
  profile: ["complete", "table"],
  highlights: ["complete", "text"],
  guide: ["complete", "table"],
  inspection: ["complete", "table"],
  structure: ["complete", "tree"],
  attention: ["complete", "text"],
};

export function buildStackSectionChrome(
  id: StackSectionId,
  intro?: string | null,
): StackSectionChrome {
  return {
    id,
    title: SECTION_TITLES[id],
    description: String(intro || "").trim(),
    showIn: SECTION_SHOW_IN[id],
  };
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
