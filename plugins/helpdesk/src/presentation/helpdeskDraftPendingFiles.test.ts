import { describe, expect, it } from "vitest";

import {
  HELPDESK_CREATE_DRAFT_SCOPE,
  pendingFilesMapToDraftRows,
  rekeyDraftFileToDocument,
  replyDraftPendingScope,
  type HelpdeskDraftPendingFile,
  type HelpdeskDraftStoredFile,
} from "./helpdeskDraftPendingFiles";

describe("helpdeskDraftPendingFiles", () => {
  it("positive: scope create e reply são estáveis", () => {
    expect(HELPDESK_CREATE_DRAFT_SCOPE).toBe("create");
    expect(replyDraftPendingScope("1122")).toBe("reply:1122");
    expect(replyDraftPendingScope(" 42 ")).toBe("reply:42");
  });

  it("irmão: Map de pending vira rows IDB", () => {
    const map = new Map<string, File>([
      ["p1", new File([new Uint8Array([1])], "a.png", { type: "image/png" })],
      ["p2", new File([new Uint8Array([2])], "b.png", { type: "image/png" })],
    ]);
    const rows = pendingFilesMapToDraftRows(map);
    expect(rows.map((row) => row.id)).toEqual(["p1", "p2"]);
    expect(rows.every((row) => row.file instanceof File)).toBe(true);
  });

  it("positive: após upload, File fica sob document id (F5)", () => {
    const file = new File([new Uint8Array([1])], "shot.png", { type: "image/png" });
    const map = new Map<string, File>([["pend-a", file]]);
    rekeyDraftFileToDocument(map, "pend-a", 1201);
    expect(map.has("pend-a")).toBe(false);
    expect(map.get("1201")).toBe(file);
    expect(pendingFilesMapToDraftRows(map).map((row) => row.id)).toEqual(["1201"]);
  });

  it("negativo: rekey sem pending não inventa File", () => {
    const map = new Map<string, File>();
    rekeyDraftFileToDocument(map, "missing", 9);
    expect(map.size).toBe(0);
  });

  it("negativo: payload stored mantém id/nome/tipo (contrato IDB)", () => {
    const pending: HelpdeskDraftPendingFile = {
      id: "x1",
      file: new File([new Uint8Array([9])], "shot.png", { type: "image/png", lastModified: 10 }),
    };
    const stored: HelpdeskDraftStoredFile = {
      id: pending.id,
      name: pending.file.name,
      type: pending.file.type,
      lastModified: pending.file.lastModified,
      buffer: new Uint8Array([9]).buffer,
    };
    expect(stored.id).toBe("x1");
    expect(stored.name).toBe("shot.png");
    expect(stored.type).toBe("image/png");
  });
});
