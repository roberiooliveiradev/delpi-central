import { describe, expect, it } from "vitest";

import {
  applyBackgroundImagePreservingUnderlay,
  fillToBackgroundUnderlay,
  patchBackgroundUnderlay,
  removeBackgroundImage,
} from "./comunicadoBackgroundPatch";

describe("comunicadoBackgroundPatch", () => {
  it("patchBackgroundUnderlay atualiza underlay sem apagar imagem", () => {
    const current = {
      type: "image" as const,
      assetId: "bg-1",
      url: "/media/bg-1",
    };
    const next = patchBackgroundUnderlay(current, { kind: "solid", color: "#003866" });
    expect(next).toMatchObject({
      type: "image",
      assetId: "bg-1",
      underlay: { type: "color", value: "#003866" },
    });
  });

  it("patchBackgroundUnderlay em cor substitui o fundo", () => {
    expect(
      patchBackgroundUnderlay({ type: "color", value: "#ffffff" }, { kind: "solid", color: "#003866" }),
    ).toEqual({ type: "color", value: "#003866" });
  });

  it("applyBackgroundImagePreservingUnderlay promove cor atual para underlay", () => {
    const next = applyBackgroundImagePreservingUnderlay(
      { type: "color", value: "#003866" },
      { assetId: "bg-2", url: "/media/bg-2" },
    );
    expect(next).toEqual({
      type: "image",
      assetId: "bg-2",
      url: "/media/bg-2",
      underlay: { type: "color", value: "#003866" },
    });
  });

  it("removeBackgroundImage restaura underlay como fundo principal", () => {
    expect(
      removeBackgroundImage({
        type: "image",
        assetId: "bg-1",
        underlay: { type: "color", value: "#003866" },
      }),
    ).toEqual({ type: "color", value: "#003866" });
  });

  it("removeBackgroundImage legado sem underlay usa branco", () => {
    expect(removeBackgroundImage({ type: "image", assetId: "bg-1" })).toEqual({
      type: "color",
      value: "#ffffff",
    });
  });

  it("cor, imagem, underlay e remoção restauram o fundo anterior", () => {
    const solid = { type: "color" as const, value: "#112233" };
    const withImage = applyBackgroundImagePreservingUnderlay(solid, { assetId: "bg-3" });
    expect(withImage).toMatchObject({
      type: "image",
      assetId: "bg-3",
      underlay: { type: "color", value: "#112233" },
    });
    const recolored = patchBackgroundUnderlay(withImage, { kind: "solid", color: "#445566" });
    expect(recolored).toMatchObject({
      type: "image",
      assetId: "bg-3",
      underlay: { type: "color", value: "#445566" },
    });
    expect(removeBackgroundImage(recolored)).toEqual({ type: "color", value: "#445566" });
  });

  it("gradiente vira underlay da imagem e volta ao remover", () => {
    const gradient = {
      type: "gradient" as const,
      from: "#111111",
      to: "#eeeeee",
      angle: 90,
    };
    const withImage = applyBackgroundImagePreservingUnderlay(gradient, { assetId: "bg-4" });
    expect(withImage).toMatchObject({
      type: "image",
      underlay: { type: "gradient", from: "#111111", to: "#eeeeee", angle: 90 },
    });
    expect(removeBackgroundImage(withImage)).toMatchObject({
      type: "gradient",
      from: "#111111",
      to: "#eeeeee",
    });
  });

  it("underlay explícito permanece ao trocar a imagem", () => {
    const next = applyBackgroundImagePreservingUnderlay(
      {
        type: "image",
        assetId: "old",
        underlay: { type: "color", value: "#abcabc" },
      },
      { assetId: "new" },
    );
    expect(next.underlay).toEqual({ type: "color", value: "#abcabc" });
  });

  it("imagem sem fundo anterior usa underlay branco", () => {
    expect(applyBackgroundImagePreservingUnderlay(undefined, { assetId: "solo" })).toMatchObject({
      type: "image",
      underlay: { type: "color", value: "#ffffff" },
    });
  });

  it("fillToBackgroundUnderlay converte gradiente", () => {
    expect(
      fillToBackgroundUnderlay({
        kind: "gradient",
        angle: 90,
        stops: [
          { color: "#111111", position: 0 },
          { color: "#eeeeee", position: 100 },
        ],
      }),
    ).toMatchObject({
      type: "gradient",
      from: "#111111",
      to: "#eeeeee",
      angle: 90,
    });
  });
});
