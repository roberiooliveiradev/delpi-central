import type { ContentFormatKind } from "./assistantContentLayout";
import type { AssistantContentSegment } from "./assistantContentTypes";

export type StackSectionId =
  | "scope"
  | "profile"
  | "highlights"
  | "guide"
  | "inspection"
  | "structure"
  | "attention";

export type StackSectionChrome = {
  /** Seções humanizadas (`scope`, `profile`, …) ou por rota (`route-stock`, …). */
  id: StackSectionId | string;
  title: string;
  showIn: Array<ContentFormatKind | "complete">;
};

const SECTION_BASE_TITLES: Record<StackSectionId, string> = {
  scope: "Escopo da consulta",
  profile: "Ficha cadastral",
  highlights: "Síntese executiva (Destaques)",
  guide: "Roteiro de produção",
  inspection: "Plano de inspeção",
  structure: "Estrutura (BOM)",
  attention: "Alertas e divergências",
};

const SECTION_SHOW_IN: Record<StackSectionId, StackSectionChrome["showIn"]> = {
  scope: ["complete", "text"],
  profile: ["complete", "table", "text"],
  highlights: ["complete", "text"],
  guide: ["complete", "table", "text"],
  inspection: ["complete", "table", "text"],
  structure: ["complete", "tree", "text"],
  attention: ["complete", "text"],
};

export function stripStackSectionNumber(title: string): string {
  return String(title || "").replace(/^\d+\.\s*/, "").trim();
}

export function buildStackSectionChrome(id: StackSectionId): StackSectionChrome {
  return {
    id,
    title: SECTION_BASE_TITLES[id],
    showIn: SECTION_SHOW_IN[id],
  };
}

export function renumberStackSectionTitles(
  segments: AssistantContentSegment[],
  activeKind: ContentFormatKind | null,
): AssistantContentSegment[] {
  let visibleIndex = 0;

  return segments.map((segment) => {
    if (segment.kind !== "stackSection") {
      return segment;
    }

    if (!isStackSectionVisible(segment.section, activeKind)) {
      return segment;
    }

    visibleIndex += 1;
    const baseTitle = stripStackSectionNumber(segment.section.title);

    return {
      kind: "stackSection",
      section: {
        ...segment.section,
        title: `${visibleIndex}. ${baseTitle}`,
      },
    };
  });
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
