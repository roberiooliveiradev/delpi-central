import { describe, expect, it } from "vitest";

import type { PresentationPayload } from "../api/tvDashboardApi";
import {
  clearPreviewPayloadCache,
  peekPreviewPayloadCache,
  rememberPreviewPayloadCache,
} from "./PlaylistPreviewPage";

describe("previewPayloadCache", () => {
  it("guarda e limpa payload por playlist", () => {
    clearPreviewPayloadCache();
    const payload = {
      playlist: { id: "pl-1", name: "Teste" },
      slides: [],
    } as unknown as PresentationPayload;

    rememberPreviewPayloadCache("pl-1", payload);
    expect(peekPreviewPayloadCache("pl-1")).toBe(payload);

    clearPreviewPayloadCache("pl-1");
    expect(peekPreviewPayloadCache("pl-1")).toBeNull();
  });
});
