import { describe, expect, it } from "vitest";

import {
  comunicadoBackgroundCssProperties,
  comunicadoBackgroundImageUrl,
  comunicadoBackgroundRootStyle,
} from "./comunicadoBackgroundStyle";

describe("comunicadoBackgroundStyle", () => {
  it("resolve URL da imagem (url ou value)", () => {
    expect(
      comunicadoBackgroundImageUrl({
        type: "image",
        assetId: "a1",
        url: "/apps/tv-dashboard-api/public/present/t/media/a1?x=1",
      }),
    ).toContain("media/a1");
    expect(comunicadoBackgroundImageUrl({ type: "image", value: "https://cdn.example/bg.jpg" })).toBe(
      "https://cdn.example/bg.jpg",
    );
    expect(comunicadoBackgroundImageUrl({ type: "color", value: "#fff" })).toBeUndefined();
  });

  it("imagem: cover + no-repeat + URL entre aspas (query string)", () => {
    const css = comunicadoBackgroundCssProperties(
      { type: "image", assetId: "bg" },
      "/apps/tv-dashboard-api/public/present/t/media/a?x=1",
    );
    expect(css.backgroundSize).toBe("cover");
    expect(css.backgroundRepeat).toBe("no-repeat");
    expect(css.backgroundPosition).toBe("center center");
    expect(css.backgroundImage).toContain(
      'url("/apps/tv-dashboard-api/public/present/t/media/a?x=1")',
    );
  });

  it("root com imagem não pinta background-image (camada <img> cover)", () => {
    const style = comunicadoBackgroundRootStyle({
      type: "image",
      url: "https://cdn.example/bg.jpg",
    });
    expect(style.backgroundImage).toBeUndefined();
    expect(style.backgroundColor).toBe("#ffffff");
  });

  it("cor e gradiente no root", () => {
    expect(comunicadoBackgroundRootStyle({ type: "color", value: "#112233" })).toEqual({
      backgroundColor: "#112233",
    });
    expect(comunicadoBackgroundCssProperties({ type: "gradient", from: "#000", to: "#fff", angle: 90 }))
      .toMatchObject({
        backgroundImage: "linear-gradient(90deg, #000, #fff)",
      });
  });
});
