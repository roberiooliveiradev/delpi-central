import { describe, expect, it } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import {
  applySlideBatchPatch,
  buildSparseSlidePatch,
  isCustomMessageSlide,
  resolveMixedSlideField,
  resolveSelectedSlides,
  slideBatchFieldApplicability,
} from "./applySlideBatchPatch";

function slide(partial: Partial<Slide> & Pick<Slide, "id">): Slide {
  return {
    playlistId: "p1",
    sortOrder: 0,
    slideType: "native",
    title: partial.title ?? partial.id,
    isActive: true,
    ...partial,
  };
}

describe("applySlideBatchPatch", () => {
  const custom = slide({
    id: "c1",
    nativeScreenKey: "custom_message",
    nativeConfig: { headline: "A" },
  });
  const native = slide({
    id: "n1",
    nativeScreenKey: "quality_ppm_summary",
    nativeConfig: { branch: "01", periodDays: 30 },
  });
  const external = slide({
    id: "e1",
    slideType: "external",
    externalUrl: "https://exemplo.test",
  });

  it("aplica duração e transição em todos os tipos", () => {
    const result = applySlideBatchPatch([custom, native, external], {
      durationSec: null,
      transitionStyle: "wipe",
    });
    expect(result.skipped).toEqual([]);
    expect(result.applied.map((item) => item.slideId)).toEqual(["c1", "n1", "e1"]);
    expect(result.applied[0]?.payload).toEqual({ durationSec: null, transitionStyle: "wipe" });
  });

  it("pula URL em tela que não é externa", () => {
    const result = applySlideBatchPatch([custom, external], { externalUrl: "https://nova.test" });
    expect(result.applied).toEqual([
      { slideId: "e1", payload: { externalUrl: "https://nova.test" } },
    ]);
    expect(result.skipped).toEqual([{ slideId: "c1", reason: "not_external" }]);
  });

  it("aplica filial só em nativa operacional", () => {
    const result = applySlideBatchPatch([custom, native], { branch: "02" });
    expect(result.skipped).toEqual([{ slideId: "c1", reason: "not_native_operational" }]);
    expect(result.applied).toEqual([
      {
        slideId: "n1",
        payload: { nativeConfig: { branch: "02", periodDays: 30 } },
      },
    ]);
  });

  it("mescla nativeConfig só em personalizada", () => {
    const result = applySlideBatchPatch([custom, native], {
      nativeConfig: { headline: "B" },
    });
    expect(result.skipped).toEqual([{ slideId: "n1", reason: "not_custom" }]);
    expect(result.applied[0]?.payload.nativeConfig).toMatchObject({ headline: "B" });
  });

  it("não reenvia campos omitidos", () => {
    const result = applySlideBatchPatch([custom], { transitionStyle: "fade" });
    expect(result.applied[0]?.payload).toEqual({ transitionStyle: "fade" });
    expect(result.applied[0]?.payload).not.toHaveProperty("title");
    expect(result.applied[0]?.payload).not.toHaveProperty("durationSec");
  });
});

describe("slideBatchFieldApplicability / mixed", () => {
  it("expõe quais grupos de campo cabem na seleção", () => {
    expect(
      slideBatchFieldApplicability([
        { slideType: "native", nativeScreenKey: "custom_message" },
        { slideType: "external", nativeScreenKey: null },
      ]),
    ).toEqual({
      common: true,
      externalUrl: true,
      branch: false,
      nativeConfig: true,
    });
  });

  it("detecta valor misto sem inventar default", () => {
    expect(resolveMixedSlideField(["a", "a"])).toEqual({ mixed: false, value: "a" });
    expect(resolveMixedSlideField(["a", "b"])).toEqual({ mixed: true });
    expect(isCustomMessageSlide({ nativeScreenKey: "custom_message" })).toBe(true);
  });

  it("monta patch esparso e resolve a seleção na ordem dos ids", () => {
    expect(buildSparseSlidePatch({ transitionStyle: "wipe" })).toEqual({
      transitionStyle: "wipe",
    });
    expect(buildSparseSlidePatch({ durationInherit: true, title: "  " })).toEqual({
      durationSec: null,
    });
    expect(buildSparseSlidePatch({ transitionStyle: "" })).toEqual({
      transitionStyle: null,
    });
    const a = slide({ id: "a", title: "A" });
    const b = slide({ id: "b", title: "B" });
    expect(resolveSelectedSlides([a, b], ["b", "a"], a).map((item) => item.id)).toEqual([
      "b",
      "a",
    ]);
  });
});
