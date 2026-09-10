import { describe, expect, it } from "vitest";

import {
  actionLabel,
  artifactKindLabel,
  branchScopeLabel,
  commentTimeLabel,
  eventLabel,
  formatDateTimePtBr,
  presentationModeLabel,
  requestTypeLabel,
  statusLabel,
  timelineEventJustification,
  timelineEventTitle,
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
    expect(eventLabel("attachment_added")).toBe("Documento anexado");
    expect(eventLabel("attachment_removed")).toBe("Documento removido");
    expect(eventLabel("transition")).toBe("Etapa atualizada");
  });

  it("monta título rico da timeline a partir do payload", () => {
    expect(
      timelineEventTitle({
        event_type: "transition",
        payload: {
          action: "complete",
          action_requested: "issue",
          from_status: "in_progress",
          to_status: "awaiting_requester_confirmation",
        },
      }),
    ).toBe("Registrar emissão — Aguardando confirmação do solicitante");

    expect(
      timelineEventTitle({
        event_type: "transition",
        payload: {
          action: "complete",
          from_status: "in_progress",
          to_status: "awaiting_requester_confirmation",
        },
      }),
    ).toBe("Registrar emissão — Aguardando confirmação do solicitante");

    expect(
      timelineEventTitle({
        event_type: "transition",
        payload: {
          action: "confirm_fulfillment",
          to_status: "completed",
        },
      }),
    ).toBe("Confirmar atendimento — Concluída");

    expect(
      timelineEventTitle({
        event_type: "artifact_added",
        payload: { kind: "invoice_pdf", name: "nf-123.pdf" },
      }),
    ).toBe("Documento gerado anexado · Nota fiscal — PDF · nf-123.pdf");

    expect(
      timelineEventTitle({
        event_type: "attachment_removed",
        payload: { name: "pedido.pdf" },
      }),
    ).toBe("Documento removido · pedido.pdf");

    expect(timelineEventTitle({ event_type: "created" })).toBe("Solicitação criada");
  });

  it("extrai justificativa do payload da timeline", () => {
    expect(
      timelineEventJustification({ justification: "Nota com CNPJ errado" }),
    ).toBe("Nota com CNPJ errado");
    expect(timelineEventJustification({})).toBeNull();
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

  it("marca mensagem editada no rótulo de tempo", () => {
    expect(commentTimeLabel("2026-09-10T19:00:00.000Z")).toMatch(/10\/09\/2026 às/);
    expect(
      commentTimeLabel("2026-09-10T19:00:00.000Z", "2026-09-10T19:05:00.000Z"),
    ).toMatch(/editada às/);
  });
});
