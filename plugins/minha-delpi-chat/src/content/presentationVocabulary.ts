import presentationVocabulary from "./presentation_vocabulary.json";

type StructureDedupVocabulary = {
  structureTableTitleMarkers: string[];
  parentsTableTitleMarkers: string[];
};

const structureDedup = presentationVocabulary.structureDedup as StructureDedupVocabulary;

export function structureTableTitleMarkers(): readonly string[] {
  return structureDedup.structureTableTitleMarkers;
}

export function parentsTableTitleMarkers(): readonly string[] {
  return structureDedup.parentsTableTitleMarkers;
}
