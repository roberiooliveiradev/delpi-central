import presentationVocabulary from "./presentation_vocabulary.json";

type StructureDedupVocabulary = {
  structureTableTitleMarkers: string[];
  parentsTableTitleMarkers: string[];
};

type RichPresentationToolbarVocabulary = {
  searchLabel: string;
  searchPlaceholderTable: string;
  searchPlaceholderTree: string;
  searchAriaLabelTable: string;
  searchAriaLabelTree: string;
  filterColumnLabel: string;
  filterContainsLabel: string;
  filterContainsPlaceholder: string;
  filterValueLabel: string;
  footerTableFiltered: string;
  footerTableAll: string;
  footerTreeFiltered: string;
  footerTreeAll: string;
  exportReflectsFiltersHint: string;
};

const structureDedup = presentationVocabulary.structureDedup as StructureDedupVocabulary;
const richToolbar =
  presentationVocabulary.richPresentationToolbar as RichPresentationToolbarVocabulary;

export function structureTableTitleMarkers(): readonly string[] {
  return structureDedup.structureTableTitleMarkers;
}

export function parentsTableTitleMarkers(): readonly string[] {
  return structureDedup.parentsTableTitleMarkers;
}

export function richPresentationToolbar(): RichPresentationToolbarVocabulary {
  return richToolbar;
}

export function formatRichToolbarTemplate(
  template: string,
  vars: Record<string, string | number>,
): string {
  return Object.entries(vars).reduce(
    (text, [key, value]) => text.replaceAll(`{${key}}`, String(value)),
    template,
  );
}
