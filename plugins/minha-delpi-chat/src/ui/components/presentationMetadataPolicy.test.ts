import { describe, expect, it } from "vitest";

import {
  resolveInitialContentKindFromDecision,
  resolveVisualKindsFromDecision,
} from "./presentationMetadataPolicy";

describe("presentationMetadataPolicy", () => {
  it("prioriza selected e hasHierarchy do metadata da API", () => {
    expect(
      resolveInitialContentKindFromDecision(
        {
          selected: "tree",
          availableViews: ["text", "table", "tree"],
          visualOrder: ["text", "table", "tree"],
          dataShape: { hasHierarchy: true },
        },
        ["text", "table", "tree"],
      ),
    ).toBe("tree");

    expect(
      resolveInitialContentKindFromDecision(
        {
          selected: "table",
          availableViews: ["text", "table", "chart"],
          visualOrder: ["text", "table", "chart"],
          dataShape: { hasHierarchy: false },
        },
        ["text", "table", "chart"],
      ),
    ).toBe("table");
  });

  it("extrai ordem visual sem texto do decision", () => {
    expect(
      resolveVisualKindsFromDecision({
        visualOrder: ["text", "table", "tree", "chart"],
      }),
    ).toEqual(["table", "tree", "chart"]);
  });
});
