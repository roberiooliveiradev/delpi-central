import { describe, expect, it } from "vitest";

import {
  buildUtf8CsvBlob,
  csvCell,
  sanitizeFilename,
  sanitizeSheetName,
} from "./primitives";
import { exportPayloadToCsv, exportTableFormat } from "./exportUtils";
import { configureExportAlert } from "./exportAlert";
import type { TableExportPayload } from "./types";

describe("export primitives", () => {
  it("escapa células CSV com separador", () => {
    expect(csvCell("a;b")).toBe('"a;b"');
    expect(csvCell('diz "oi"')).toBe('"diz ""oi"""');
  });

  it("sanitiza nome de arquivo", () => {
    expect(sanitizeFilename("Dashboard / Comercial")).toBe("Dashboard_Comercial");
  });

  it("limita nome de aba Excel", () => {
    expect(sanitizeSheetName("Nome muito longo para planilha Excel")).toHaveLength(31);
  });

  it("gera CSV UTF-8 com BOM", async () => {
    const blob = buildUtf8CsvBlob("a;b");
    const bytes = new Uint8Array(await blob.arrayBuffer());
    // UTF-8 BOM: EF BB BF
    expect([...bytes.slice(0, 3)]).toEqual([0xef, 0xbb, 0xbf]);
    expect(new TextDecoder().decode(bytes.slice(3))).toBe("a;b");
  });
});

describe("exportPayloadToCsv", () => {
  it("alerta quando não há colunas", () => {
    const messages: string[] = [];
    configureExportAlert((message) => {
      messages.push(message);
    });

    exportPayloadToCsv({ title: "vazio", columns: [], rows: [] });
    expect(messages[0]).toMatch(/CSV/);
  });

  it("dispara download quando há colunas", () => {
    const clicks: string[] = [];
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    URL.createObjectURL = () => "blob:test";
    URL.revokeObjectURL = () => undefined;

    const appendChild = document.body.appendChild.bind(document.body);
    document.body.appendChild = ((node: Node) => {
      if (node instanceof HTMLAnchorElement) {
        clicks.push(node.download);
        node.click = () => undefined;
      }
      return appendChild(node);
    }) as typeof document.body.appendChild;

    configureExportAlert(() => undefined);

    const payload: TableExportPayload = {
      title: "Propostas",
      columns: [{ key: "n", label: "Número" }],
      rows: [{ n: "1" }],
    };

    exportTableFormat(payload, "csv");
    expect(clicks[0]).toMatch(/Propostas\.csv$/);

    document.body.appendChild = appendChild;
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
  });
});
