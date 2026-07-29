import { describe, expect, it } from "vitest";

import {
  applySlideDraftToPayload,
  mergeSlideDraftOntoNative,
} from "./applySlideDraftToPayload";
import type { PresentationPayloadLike } from "./types";

const basePayload: PresentationPayloadLike = {
  playlist: {
    viewportProfile: "1080p",
    transitionStyle: "fade",
    globalRefreshSec: 300,
    defaultDurationSec: 30,
  },
  slides: [
    {
      id: "slide-a",
      sortOrder: 0,
      slideType: "native",
      title: "A",
      native: {
        config: { blocks: [{ id: "b1", type: "kpi_view", title: "Old" }] },
        data: {
          blocks: [
            {
              id: "b1",
              type: "kpi_view",
              title: "Old",
              resolved: { value: 22 },
            },
          ],
        },
      },
    },
  ],
};

describe("applySlideDraftToPayload", () => {
  it("preserva resolved do servidor ao aplicar rascunho", () => {
    const merged = mergeSlideDraftOntoNative(
      { blocks: [{ id: "b1", type: "kpi_view", title: "Novo" }] },
      {
        blocks: [
          {
            id: "b1",
            type: "kpi_view",
            title: "Old",
            resolved: { value: 22 },
          },
        ],
      },
    );
    const block = (merged.blocks as Record<string, unknown>[])[0];
    expect(block.title).toBe("Novo");
    expect(block.resolved).toEqual({ value: 22 });
  });

  it("atualiza o slide alvo no payload", () => {
    const next = applySlideDraftToPayload(basePayload, "slide-a", {
      blocks: [{ id: "b1", type: "kpi_view", title: "Ao vivo" }],
    });
    expect(next).not.toBe(basePayload);
    expect(next.slides[0].native?.config).toEqual({
      blocks: [{ id: "b1", type: "kpi_view", title: "Ao vivo" }],
    });
    const dataBlock = (next.slides[0].native?.data?.blocks as Record<string, unknown>[])[0];
    expect(dataBlock.title).toBe("Ao vivo");
    expect(dataBlock.resolved).toEqual({ value: 22 });
  });

  it("ignora slideId inexistente", () => {
    const next = applySlideDraftToPayload(basePayload, "missing", {
      blocks: [],
    });
    expect(next).toBe(basePayload);
  });
});
