import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoMediaBlock } from "@delpi/tv-dashboard-presentation";

const editor = vi.hoisted(() => ({ playlistId: "p1", publicToken: null as string | null }));

vi.mock("./comunicadoEditorContext", () => ({
  useComunicadoEditor: () => editor,
}));

import { ComunicadoEditorVideoPreview } from "./ComunicadoEditorVideoPreview";

const frame = { x: 0, y: 0, w: 30, h: 20 };

function renderVideo(block: Partial<ComunicadoMediaBlock>) {
  const { container } = render(
    <ComunicadoEditorVideoPreview
      block={{ id: "v1", type: "video", frame, ...block } as ComunicadoMediaBlock}
      style={{}}
    />,
  );
  const element = container.querySelector("video");
  if (!element) throw new Error("video element not rendered");
  return element;
}

afterEach(() => {
  cleanup();
  editor.publicToken = null;
});

describe("ComunicadoEditorVideoPreview poster opcional", () => {
  it("sem posterUrl (hasPoster=false / legado): não pede /poster e o vídeo carrega", () => {
    const element = renderVideo({ assetId: "72e3abbd-legacy" });
    expect(element.hasAttribute("poster")).toBe(false);
    expect(element.getAttribute("src")).toMatch(/\/playlists\/p1\/media\/72e3abbd-legacy(\?|$)/);
  });

  it("com posterUrl hidratado (hasPoster=true): usa o poster do asset", () => {
    const element = renderVideo({
      assetId: "8a9c5a28-teo",
      posterUrl: "/api/tv-dashboard/v1/playlists/p1/media/8a9c5a28-teo/poster",
    });
    expect(element.getAttribute("poster")).toMatch(/\/playlists\/p1\/media\/8a9c5a28-teo\/poster(\?|$)/);
  });

  it("com token público: poster e stream pelo caminho público", () => {
    editor.publicToken = "tok-abc";
    const legacy = renderVideo({ assetId: "legacy-sibling" });
    expect(legacy.hasAttribute("poster")).toBe(false);
    cleanup();
    const teo = renderVideo({ assetId: "8a9c5a28-teo", posterUrl: "x/poster" });
    expect(teo.getAttribute("poster")).toMatch(/\/media\/8a9c5a28-teo\/poster$/);
    expect(teo.getAttribute("poster")).toContain("tok-abc");
  });
});
