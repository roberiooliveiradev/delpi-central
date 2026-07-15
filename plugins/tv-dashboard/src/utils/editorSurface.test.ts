import { describe, expect, it } from "vitest";

import { isDeckEditorSurfaceActive, shouldKeepEditorUnderPreview } from "./editorSurface";

describe("shouldKeepEditorUnderPreview", () => {
  it("mantém editor na rota edit", () => {
    expect(shouldKeepEditorUnderPreview("edit", "pl-1", null)).toBe(true);
    expect(shouldKeepEditorUnderPreview("edit", "pl-1", "pl-1")).toBe(true);
  });

  it("mantém editor sob preview da mesma sessão", () => {
    expect(shouldKeepEditorUnderPreview("preview", "pl-1", "pl-1")).toBe(true);
  });

  it("não monta editor em preview direto (sem sessão de edição)", () => {
    expect(shouldKeepEditorUnderPreview("preview", "pl-1", null)).toBe(false);
    expect(shouldKeepEditorUnderPreview("preview", "pl-2", "pl-1")).toBe(false);
  });

  it("não mantém editor em list/share", () => {
    expect(shouldKeepEditorUnderPreview("list", undefined, "pl-1")).toBe(false);
    expect(shouldKeepEditorUnderPreview("share", "pl-1", "pl-1")).toBe(false);
  });
});

describe("isDeckEditorSurfaceActive", () => {
  it("só ativa atalhos na superfície de edição", () => {
    expect(isDeckEditorSurfaceActive("edit")).toBe(true);
    expect(isDeckEditorSurfaceActive("preview")).toBe(false);
    expect(isDeckEditorSurfaceActive("list")).toBe(false);
  });
});
