import { describe, expect, it } from "vitest";

import { DELPI_UI_OVERLAY_Z_INDEX } from "./overlayLayers";

describe("DELPI_UI_OVERLAY_Z_INDEX", () => {
  it("anchoredPanel fica acima do modal (selects dentro de diálogos)", () => {
    expect(DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel).toBeGreaterThan(
      DELPI_UI_OVERLAY_Z_INDEX.modal,
    );
    expect(DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel).toBeGreaterThan(
      DELPI_UI_OVERLAY_Z_INDEX.shapeDialog,
    );
  });

  it("helpTooltip fica acima de painéis ancorados e modais", () => {
    expect(DELPI_UI_OVERLAY_Z_INDEX.helpTooltip).toBeGreaterThan(
      DELPI_UI_OVERLAY_Z_INDEX.anchoredPanel,
    );
    expect(DELPI_UI_OVERLAY_Z_INDEX.helpTooltip).toBeGreaterThan(DELPI_UI_OVERLAY_Z_INDEX.modal);
    expect(DELPI_UI_OVERLAY_Z_INDEX.helpTooltip).toBeGreaterThan(
      DELPI_UI_OVERLAY_Z_INDEX.shapeDialog,
    );
  });
});
