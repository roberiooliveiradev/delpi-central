import { describe, expect, it, beforeEach } from "vitest";
import "fake-indexeddb/auto";

import { resolveAttachmentDisplaySrc } from "./useAuthenticatedAttachmentSrcs";
import {
  HELPDESK_CREATE_DRAFT_SCOPE,
  canRewritePendingDraftHtml,
  draftPendingFilesCoverHtml,
  enqueueHelpdeskDraftScopeTask,
  listDraftAttachmentSeedKeys,
  pendingFilesMapToDraftRows,
  readHelpdeskDraftPendingFiles,
  rekeyDraftFileToDocument,
  replyDraftPendingScope,
  resetHelpdeskDraftWriteChainsForTests,
  writeHelpdeskDraftPendingFiles,
  type HelpdeskDraftPendingFile,
  type HelpdeskDraftStoredFile,
} from "./helpdeskDraftPendingFiles";

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

describe("helpdeskDraftPendingFiles", () => {
  beforeEach(() => {
    resetHelpdeskDraftWriteChainsForTests();
  });

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

  it("positive: após upload, File fica sob document id e pending (dual cover F5)", () => {
    const file = new File([new Uint8Array([1])], "shot.png", { type: "image/png" });
    const map = new Map<string, File>([["pend-a", file]]);
    rekeyDraftFileToDocument(map, "pend-a", 1201);
    expect(map.get("pend-a")).toBe(file);
    expect(map.get("1201")).toBe(file);
    expect(pendingFilesMapToDraftRows(map).map((row) => row.id).sort()).toEqual([
      "1201",
      "pend-a",
    ]);
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

describe("E0 H1 — race de writes IDB (classe do bug F5)", () => {
  beforeEach(() => {
    resetHelpdeskDraftWriteChainsForTests();
  });

  it("CONFIRMADA: sem fila, snapshot pending (lento) sobrescreve rekey documentId", async () => {
    // Modelo do bug: void write A (uuid) e write B (1201) sem serialização.
    const finalIds: string[][] = [];
    const writeA = (async () => {
      await delay(40);
      finalIds.push(["pend-uuid"]);
    })();
    const writeB = (async () => {
      await delay(5);
      finalIds.push(["1201"]);
    })();
    await Promise.all([writeA, writeB]);
    // Último a terminar vence — IDB ficaria só com uuid; HTML já tem data-attachment-id=1201.
    expect(finalIds.at(-1)).toEqual(["pend-uuid"]);
  });

  it("positive: com enqueueHelpdeskDraftScopeTask, rekey prevalece", async () => {
    const chains = new Map<string, Promise<unknown>>();
    let stored: string[] = [];
    const writeA = enqueueHelpdeskDraftScopeTask(
      "reply:1122",
      async () => {
        await delay(40);
        stored = ["pend-uuid"];
      },
      chains,
    );
    const writeB = enqueueHelpdeskDraftScopeTask(
      "reply:1122",
      async () => {
        stored = ["1201"];
      },
      chains,
    );
    await Promise.all([writeA, writeB]);
    expect(stored).toEqual(["1201"]);
  });

  it("P0 F5: paste→rekey→fila deixa IDB alinhado ao HTML documentId", async () => {
    const chains = new Map<string, Promise<unknown>>();
    let storedIds: string[] = [];
    const map = new Map<string, File>([
      ["pend-a", new File([new Uint8Array([1])], "shot.png", { type: "image/png" })],
    ]);
    // Snapshot at enqueue (same as pendingFilesMapToDraftRows at persist call).
    const pasteSnapshot = pendingFilesMapToDraftRows(map);
    const pasteWrite = enqueueHelpdeskDraftScopeTask(
      "reply:1122",
      async () => {
        await delay(40);
        storedIds = pasteSnapshot.map((row) => row.id);
      },
      chains,
    );
    rekeyDraftFileToDocument(map, "pend-a", 1201);
    const rekeySnapshot = pendingFilesMapToDraftRows(map);
    const rekeyWrite = enqueueHelpdeskDraftScopeTask(
      "reply:1122",
      async () => {
        storedIds = rekeySnapshot.map((row) => row.id);
      },
      chains,
    );
    await Promise.all([pasteWrite, rekeyWrite]);
    const html =
      '<p><img data-attachment-id="1201" src="/apps/helpdesk-api/tickets/1122/attachments/1201" /></p>';
    expect(pasteSnapshot.map((row) => row.id)).toEqual(["pend-a"]);
    expect(storedIds.sort()).toEqual(["1201", "pend-a"]);
    expect(
      draftPendingFilesCoverHtml(html, rekeySnapshot),
    ).toBe(true);
  });

  it("irmão: scopes distintos não se bloqueiam", async () => {
    const chains = new Map<string, Promise<unknown>>();
    const order: string[] = [];
    const a = enqueueHelpdeskDraftScopeTask(
      "reply:1",
      async () => {
        await delay(30);
        order.push("a");
      },
      chains,
    );
    const b = enqueueHelpdeskDraftScopeTask(
      "reply:2",
      async () => {
        order.push("b");
      },
      chains,
    );
    await Promise.all([a, b]);
    expect(order[0]).toBe("b");
    expect(order).toContain("a");
  });
});

describe("E0 H3 — IDB key ≠ HTML key ⇒ resolve null (consequência de H1)", () => {
  it("CONFIRMADA: HTML documentId + IDB só uuid ⇒ seed não cobre; resolve(1201)=null", () => {
    const html =
      '<p><img src="/apps/helpdesk-api/tickets/1122/attachments/1201" data-attachment-id="1201" alt="x" /></p>';
    const idbRows: HelpdeskDraftPendingFile[] = [
      {
        id: "pend-uuid",
        file: new File([new Uint8Array([1])], "x.png", { type: "image/png" }),
      },
    ];
    expect(listDraftAttachmentSeedKeys(html)).toEqual(["1201"]);
    expect(draftPendingFilesCoverHtml(html, idbRows)).toBe(false);
    expect(resolveAttachmentDisplaySrc("1201", { "pend-uuid": "blob:stale" }, {})).toBeNull();
  });

  it("positive: IDB sob document id cobre HTML pós-rekey", () => {
    const html =
      '<p><img src="/apps/helpdesk-api/tickets/1122/attachments/1201" data-attachment-id="1201" alt="x" /></p>';
    const idbRows: HelpdeskDraftPendingFile[] = [
      {
        id: "1201",
        file: new File([new Uint8Array([1])], "x.png", { type: "image/png" }),
      },
    ];
    expect(draftPendingFilesCoverHtml(html, idbRows)).toBe(true);
    expect(
      resolveAttachmentDisplaySrc("1201", { "1201": "blob:ok" }, {}),
    ).toBe("blob:ok");
  });

  it("irmão: pending HTML + IDB uuid cobre F5 antes do upload", () => {
    const html =
      '<p><img src="attachment:pending:abc" data-attachment-pending="abc" alt="x" /></p>';
    const idbRows: HelpdeskDraftPendingFile[] = [
      { id: "abc", file: new File([new Uint8Array([1])], "x.png", { type: "image/png" }) },
    ];
    expect(draftPendingFilesCoverHtml(html, idbRows)).toBe(true);
  });

  it("negativo: texto sem img não exige IDB", () => {
    expect(draftPendingFilesCoverHtml("<p>olá</p>", [])).toBe(true);
  });
});

describe("E0 H5 — GET falha mas IDB seed basta", () => {
  it("CONFIRMADA como fallback: com seed local, resolve não depende do GET", () => {
    expect(
      resolveAttachmentDisplaySrc("1201", { "1201": "blob:from-idb" }, {}),
    ).toBe("blob:from-idb");
  });

  it("negativo: sem seed e sem alias, resolve null (GET precisaria popular srcs)", () => {
    expect(resolveAttachmentDisplaySrc("1201", {}, {})).toBeNull();
  });
});

describe("F5 local — IDB round-trip real (fake-indexeddb)", () => {
  beforeEach(() => {
    resetHelpdeskDraftWriteChainsForTests();
  });

  it("P0: paste→rekey→F5 read cobre HTML documentId e resolve≠null", async () => {
    const scope = replyDraftPendingScope("1122");
    const file = new File([new Uint8Array([7, 7, 7])], "shot.png", { type: "image/png" });
    const map = new Map<string, File>([["pend-a", file]]);

    await writeHelpdeskDraftPendingFiles(scope, pendingFilesMapToDraftRows(map));
    rekeyDraftFileToDocument(map, "pend-a", 1201);
    await writeHelpdeskDraftPendingFiles(scope, pendingFilesMapToDraftRows(map));

    // Simulate F5: new page read
    const rows = await readHelpdeskDraftPendingFiles(scope);
    const html =
      '<p><img data-attachment-id="1201" src="/apps/helpdesk-api/tickets/1122/attachments/1201" alt="shot" /></p>';
    expect(draftPendingFilesCoverHtml(html, rows)).toBe(true);

    const srcs: Record<string, string> = {};
    for (const row of rows) {
      srcs[row.id] = `blob:seed-${row.id}`;
    }
    expect(resolveAttachmentDisplaySrc("1201", srcs, {})).toBe("blob:seed-1201");
  });

  it("irmão: F5 antes do upload — pending key sobrevive no IDB", async () => {
    const scope = replyDraftPendingScope("1122");
    const file = new File([new Uint8Array([1])], "a.png", { type: "image/png" });
    await writeHelpdeskDraftPendingFiles(scope, [{ id: "pend-a", file }]);
    const rows = await readHelpdeskDraftPendingFiles(scope);
    const html =
      '<p><img src="attachment:pending:pend-a" data-attachment-pending="pend-a" alt="a" /></p>';
    expect(draftPendingFilesCoverHtml(html, rows)).toBe(true);
    expect(resolveAttachmentDisplaySrc("pend-a", { "pend-a": "blob:x" }, {})).toBe("blob:x");
  });

  it("H3 gate: sem cover no IDB, não reescrever HTML para documentId", () => {
    const rewritten =
      '<p><img data-attachment-id="1201" src="/apps/helpdesk-api/tickets/1122/attachments/1201" /></p>';
    const idbOnlyUuid: HelpdeskDraftPendingFile[] = [
      {
        id: "pend-a",
        file: new File([new Uint8Array([1])], "x.png", { type: "image/png" }),
      },
    ];
    expect(canRewritePendingDraftHtml(rewritten, idbOnlyUuid)).toBe(false);
    expect(canRewritePendingDraftHtml(rewritten, [
      { id: "1201", file: idbOnlyUuid[0].file },
      { id: "pend-a", file: idbOnlyUuid[0].file },
    ])).toBe(true);
  });

  it("negativo: clear esvazia scope (send followup)", async () => {
    const scope = replyDraftPendingScope("1122");
    await writeHelpdeskDraftPendingFiles(scope, [
      { id: "1", file: new File([new Uint8Array([1])], "a.png", { type: "image/png" }) },
    ]);
    await writeHelpdeskDraftPendingFiles(scope, []);
    expect(await readHelpdeskDraftPendingFiles(scope)).toEqual([]);
  });
});

describe("E0 H4 — seed depois do paint sem rebind (classe do bug reply)", () => {
  it("CONFIRMADA: resolve null no 1º paint; seed posterior precisa nova identidade de resolve", () => {
    // Modelo create: pendingHydrated força re-bind. Reply só seedFile→srcs sem
    // esperar IDB antes do editor (ticket-gated) deixava 1º apply com resolve null.
    const srcsBefore: Record<string, string> = {};
    expect(resolveAttachmentDisplaySrc("1201", srcsBefore, {})).toBeNull();
    const srcsAfter = { ...srcsBefore, "1201": "blob:late-seed" };
    expect(resolveAttachmentDisplaySrc("1201", srcsAfter, {})).toBe("blob:late-seed");
  });
});
