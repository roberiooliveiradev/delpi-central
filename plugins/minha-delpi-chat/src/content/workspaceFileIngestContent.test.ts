import { describe, expect, it } from "vitest";

import {
  workspaceFileAgentIngestLabels,
  workspaceFileComposerAttachmentsHeader,
  workspaceFileContextBinaryLine,
  workspaceFileDropzoneContent,
  workspaceFileProjectFileKindLabel,
  workspaceFileReadingStatusLabel,
} from "./workspaceFileIngestContent";

describe("workspaceFileIngestContent", () => {
  it("resolve status de leitura a partir do JSON", () => {
    expect(workspaceFileReadingStatusLabel("indexed")).toBe("Indexado");
    expect(workspaceFileReadingStatusLabel("indexing")).toBe("Indexando para consulta");
    expect(workspaceFileReadingStatusLabel("queued")).toBe("Aguardando envio");
    expect(workspaceFileReadingStatusLabel("index_failed")).toBe("Falha na leitura");
  });

  it("expõe copy do dropzone por variante", () => {
    expect(workspaceFileDropzoneContent("agent").hint).toContain("PDF");
    expect(workspaceFileDropzoneContent("workspace").hint).toContain("txt");
  });

  it("formata cabeçalho de anexos do composer", () => {
    expect(workspaceFileComposerAttachmentsHeader(2)).toBe("2 arquivo(s) anexado(s)");
  });

  it("expõe labels de ingestão do agente", () => {
    expect(workspaceFileAgentIngestLabels().uploadingStatus).toContain("Enviando");
    expect(workspaceFileAgentIngestLabels().duplicateMarked).toContain("indexado");
  });

  it("formata rótulo de fonte do projeto com data", () => {
    expect(workspaceFileProjectFileKindLabel("10 jun. 2026")).toContain("Arquivo");
    expect(workspaceFileProjectFileKindLabel()).toBe("Arquivo");
  });

  it("formata linha de arquivo binário no contexto", () => {
    expect(workspaceFileContextBinaryLine("nota.pdf", "application/pdf")).toContain("nota.pdf");
  });

  it("expõe hint de contexto no dropzone", () => {
    expect(workspaceFileDropzoneContent("context").hint).toContain("TXT");
  });
});
