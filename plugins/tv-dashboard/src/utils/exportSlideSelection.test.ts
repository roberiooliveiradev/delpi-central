import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import {
  orderSlidesForExport,
  resolveExportPptxTargets,
  resolveExportSlideTargets,
  uniqueExportFileName,
} from "./exportSlideSelection";

function slide(partial: Partial<Slide> & Pick<Slide, "id" | "sortOrder">): Slide {
  return {
    playlistId: "p1",
    slideType: "native",
    title: partial.title ?? partial.id,
    isActive: true,
    ...partial,
  };
}

describe("exportSlideSelection", () => {
  const customA = slide({
    id: "a",
    sortOrder: 0,
    title: "Uma",
    nativeScreenKey: "custom_message",
  });
  const customB = slide({
    id: "b",
    sortOrder: 2,
    title: "Duas",
    nativeScreenKey: "custom_message",
  });
  const native = slide({
    id: "n",
    sortOrder: 1,
    title: "KPI",
    nativeScreenKey: "quality_ppm_summary",
    isActive: false,
  });
  const all = [customA, native, customB];

  it("selected usa a ordem da playlist, não a do clique", () => {
    expect(orderSlidesForExport([customB, customA], all).map((item) => item.id)).toEqual([
      "a",
      "b",
    ]);
    expect(
      resolveExportSlideTargets({
        scope: "selected",
        slides: all,
        selectedSlides: [customB, customA],
        primary: customB,
      }).map((item) => item.id),
    ).toEqual(["a", "b"]);
  });

  it("playlist ignora pausada; current é só a primária", () => {
    expect(
      resolveExportSlideTargets({
        scope: "playlist",
        slides: all,
        selectedSlides: [customA],
        primary: customA,
      }).map((item) => item.id),
    ).toEqual(["a", "b"]);
    expect(
      resolveExportSlideTargets({
        scope: "current",
        slides: all,
        selectedSlides: [customA, customB],
        primary: customB,
      }).map((item) => item.id),
    ).toEqual(["b"]);
  });

  it("PPTX só leva tela livre e conta skip", () => {
    expect(
      resolveExportPptxTargets([customA, native, customB], customA, all),
    ).toEqual({ targets: [customA, customB], skipped: 1 });
  });

  it("evita colisão de nome de arquivo", () => {
    const used = new Set<string>();
    expect(uniqueExportFileName("Personalizado", used, "png")).toBe("Personalizado.png");
    expect(uniqueExportFileName("Personalizado", used, "png")).toBe("Personalizado-2.png");
  });
});
