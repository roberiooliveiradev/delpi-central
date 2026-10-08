import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

const PANEL = "features/process-issue/ui/ProcessIssuePayloadPanel.tsx";

describe("ProcessIssuePayloadPanel structural", () => {
  it("renderiza as quatro seções do painel", () => {
    const src = read(PANEL);
    expect(src).toContain("Problema informado");
    expect(src).toContain("Contexto da produção");
    expect(src).toContain("Processo no momento do reporte");
    expect(src).toContain("Materiais vinculados no momento do reporte");
  });

  it("destaca o motivo e separa ferramenta/material informados do snapshot", () => {
    const src = read(PANEL);
    expect(src).toContain("view.issueLabel");
    expect(src).toContain("Ferramenta informada pelo operador");
    expect(src).toContain("Material informado pelo operador");
    expect(src).toContain("Ferramenta vinculada na operação");
    // nunca mistura reportedToolCode com toolSnapshot no mesmo campo
    expect(src).toContain("view.reportedToolCode");
    expect(src).toContain("view.toolSnapshot");
  });

  it("só oferece «Abrir desenho» quando existe PA no snapshot", () => {
    const src = read(PANEL);
    expect(src).toContain("Abrir desenho");
    expect(src).toContain("paCode ?");
    expect(src).toContain(
      "Produto acabado não informado no momento do reporte.",
    );
    // o desenho é do PA — nunca cai para productCode como substituto
    expect(src).not.toMatch(/[^.]productCode\s*\?\s*\(/);
  });

  it("usa o preview autenticado por request id — nunca URL livre", () => {
    const src = read(PANEL);
    expect(src).toContain("RequestFilePreviewModal");
    expect(src).toContain('kind: "product_drawing"');
    expect(src).toContain("requestId");
    expect(src).not.toContain("api-delpi");
    expect(src).not.toContain("/products/");
    expect(src).not.toContain("window.open");
  });

  it("trata os estados do snapshot de materiais", () => {
    const src = read(PANEL);
    expect(src).toContain("materialsSnapshotAvailable");
    expect(src).toContain(
      "Não foi possível consultar os materiais vinculados no momento em",
    );
    expect(src).toContain(
      "Nenhum material vinculado foi encontrado no momento do reporte.",
    );
  });

  it("usa o parser dedicado — nunca acessa o payload bruto em profundidade", () => {
    const src = read(PANEL);
    expect(src).toContain("parseProcessIssuePayload");
    expect(src).not.toMatch(/payload\.(operation|issue|operator|materials)/);
    expect(src).not.toMatch(/payload\[/);
  });

  it("não implementa workflow próprio nem retorno ao operador", () => {
    const src = read(PANEL);
    expect(src).not.toContain("transitionRequest");
    expect(src).not.toContain("ActionBar");
    expect(src).not.toMatch(/cockpit|operator-feedback/i);
  });
});

describe("RequestDetailPage — montagem P4", () => {
  it("monta o painel apenas para process-issue após o card genérico", () => {
    const src = read("pages/RequestDetailPage.tsx");
    expect(src).toContain('request.type_code === "process-issue"');
    expect(src).toContain("ProcessIssuePayloadPanel");
    const idxPanel = src.indexOf('request.type_code === "process-issue"');
    const idxAttach = src.indexOf("<AttachmentsPanel");
    expect(idxPanel).toBeGreaterThan(-1);
    expect(idxAttach).toBeGreaterThan(idxPanel);
  });
});

describe("RequestFilePreviewModal — alvo product_drawing", () => {
  it("resolve o blob pelo endpoint autenticado do request", () => {
    const src = read("components/RequestFilePreviewModal.tsx");
    expect(src).toContain('"product_drawing"');
    expect(src).toContain("downloadProductDrawingBlob");
  });
});
