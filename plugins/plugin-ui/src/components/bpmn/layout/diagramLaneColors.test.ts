import { describe, expect, it } from "vitest";

import {
  DIAGRAM_LANE_TONE_COUNT,
  diagramLaneChipToneClass,
  diagramLaneToneClass,
} from "./diagramLaneColors";

describe("diagramLaneColors", () => {
  it("retorna classes cíclicas de tom para faixas", () => {
    expect(diagramLaneToneClass(0)).toBe("delpi-ui-bpmn-lane--tone-0");
    expect(diagramLaneToneClass(5)).toBe("delpi-ui-bpmn-lane--tone-5");
    expect(diagramLaneToneClass(6)).toBe("delpi-ui-bpmn-lane--tone-0");
    expect(diagramLaneToneClass(-1)).toBe(
      `delpi-ui-bpmn-lane--tone-${DIAGRAM_LANE_TONE_COUNT - 1}`
    );
  });

  it("espelha tom nos chips da toolbar", () => {
    expect(diagramLaneChipToneClass(2)).toBe("delpi-ui-bpmn-lane-chip--tone-2");
  });
});
