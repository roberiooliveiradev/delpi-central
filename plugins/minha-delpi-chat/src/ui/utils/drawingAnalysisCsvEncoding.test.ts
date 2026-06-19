import { describe, expect, it } from "vitest";
import { buildExcelCsvBlob, buildExcelCsvContent } from "./drawingAnalysisCsvEncoding";

describe("drawingAnalysisCsvEncoding", () => {
  it("prefixa sep=; para o Excel reconhecer delimitador", () => {
    expect(buildExcelCsvContent("Seção;Item\r\nBOM;Falha")).toMatch(/^sep=;\r\n/);
  });

  it("gera blob UTF-16 LE com acentos preservados", async () => {
    const blob = buildExcelCsvBlob("Seção;Observação\r\nInspeção;Operação CT-99");
    const buffer = await blob.arrayBuffer();
    const view = new DataView(buffer);

    expect(view.getUint16(0, true)).toBe(0xfeff);
    expect(new TextDecoder("utf-16le").decode(buffer)).toContain("Observação");
    expect(new TextDecoder("utf-16le").decode(buffer)).toContain("Inspeção");
  });
});
