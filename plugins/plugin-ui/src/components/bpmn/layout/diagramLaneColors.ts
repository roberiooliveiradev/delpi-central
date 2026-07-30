/** Quantidade de tons cíclicos para faixas do diagrama. */
export const DIAGRAM_LANE_TONE_COUNT = 6;

/** Classe CSS `delpi-ui-bpmn-lane--tone-N` para distinguir faixas visualmente. */
export function diagramLaneToneClass(laneIndex: number): string {
  const tone =
    ((laneIndex % DIAGRAM_LANE_TONE_COUNT) + DIAGRAM_LANE_TONE_COUNT) %
    DIAGRAM_LANE_TONE_COUNT;
  return `delpi-ui-bpmn-lane--tone-${tone}`;
}

/** Classe de tom para chips da toolbar de faixas. */
export function diagramLaneChipToneClass(laneIndex: number): string {
  const tone =
    ((laneIndex % DIAGRAM_LANE_TONE_COUNT) + DIAGRAM_LANE_TONE_COUNT) %
    DIAGRAM_LANE_TONE_COUNT;
  return `delpi-ui-bpmn-lane-chip--tone-${tone}`;
}
