import { describe, expect, it } from "vitest";

import {
  NC_BASE_PATH,
  NC_PATHS,
  resolveNcPath,
} from "./nonconformityRoutes";

describe("resolveNcPath — caminho standalone fora de /lmps", () => {
  it("base é /apps/engineering/nonconformities (doc 45)", () => {
    expect(NC_BASE_PATH).toBe("/apps/engineering/nonconformities");
    expect(NC_BASE_PATH).not.toContain("/lmps");
  });

  it("raiz e prefixo resolvem a listagem", () => {
    expect(resolveNcPath("")).toEqual({ kind: "list" });
    expect(resolveNcPath("nonconformities")).toEqual({ kind: "list" });
    expect(resolveNcPath("nonconformities/")).toEqual({ kind: "list" });
  });

  it("new resolve o formulário de criação", () => {
    expect(resolveNcPath("nonconformities/new")).toEqual({ kind: "new" });
  });

  it("detail extrai recordId decodificado", () => {
    expect(resolveNcPath("nonconformities/abc-123")).toEqual({
      kind: "detail",
      recordId: "abc-123",
    });
    expect(resolveNcPath("nonconformities/id%20com%20espaco")).toEqual({
      kind: "detail",
      recordId: "id com espaco",
    });
  });

  it("edit extrai recordId com sufixo /edit", () => {
    expect(resolveNcPath("nonconformities/abc-123/edit")).toEqual({
      kind: "edit",
      recordId: "abc-123",
    });
  });

  it("caminhos desconhecidos caem em not_found", () => {
    expect(resolveNcPath("nonconformities/a/b/c")).toEqual({
      kind: "not_found",
    });
    expect(resolveNcPath("outra-coisa/x")).toEqual({ kind: "not_found" });
  });
});

describe("NC_PATHS — construção URL-safe", () => {
  it("detail codifica o recordId", () => {
    expect(NC_PATHS.detail("id/com:barra")).toBe(
      "/apps/engineering/nonconformities/id%2Fcom%3Abarra",
    );
  });

  it("edit codifica o recordId e adiciona sufixo", () => {
    expect(NC_PATHS.edit("abc 123")).toBe(
      "/apps/engineering/nonconformities/abc%20123/edit",
    );
  });
});
