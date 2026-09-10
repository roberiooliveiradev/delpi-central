import { describe, expect, it } from "vitest";

import {
  actionLabel,
  artifactKindLabel,
  branchScopeLabel,
  eventLabel,
  formatDateTimePtBr,
  presentationModeLabel,
  requestTypeLabel,
  statusLabel,
} from "./presentationLabels";

describe("presentationLabels", () => {
  it("traduz status conhecidos e usa alias quando amigável", () => {
    expect(statusLabel("submitted")).toBe("Enviada");
    expect(statusLabel("in_progress", "issued")).toBe("Emitida");
    expect(statusLabel("unknown_status")).toBe("Unknown status");
  });

  it("traduz actions e events", () => {
    expect(actionLabel("start")).toBe("Iniciar atendimento");
    expect(actionLabel("weird_action")).toBe("Weird action");
    expect(eventLabel("attachment_added")).toBe("Anexo enviado");
    expect(eventLabel("transition")).toBe("Etapa atualizada");
  });

  it("traduz escopos, modos, kinds e tipos", () => {
    expect(branchScopeLabel("required")).toBe("Filial obrigatória");
    expect(presentationModeLabel("schema_driven")).toBe("Formulário configurável");
    expect(artifactKindLabel("invoice_pdf")).toBe("Nota fiscal — PDF");
    expect(artifactKindLabel("generic")).toBe("Outro documento");
    expect(requestTypeLabel("invoice-issuance")).toBe("Emissão de Notas Fiscais");
    expect(requestTypeLabel("x", "Nome da API")).toBe("Nome da API");
  });

  it("formata data em pt-BR", () => {
    expect(formatDateTimePtBr("")).toBe("—");
    expect(formatDateTimePtBr("2026-09-08T15:20:00.000Z")).toMatch(/\d{2}\/\d{2}\/2026 às \d{2}:\d{2}/);
  });
});
