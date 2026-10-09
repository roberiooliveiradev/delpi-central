import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeliaAssistantMessage } from "./DeliaAssistantMessage";
import type { ConversationDisplayTurn } from "./ConversationTimeline";

function makeTurn(
  overrides: Partial<ConversationDisplayTurn> = {},
): ConversationDisplayTurn {
  return {
    id: "t-1",
    role: "delia",
    content: "Resposta da DÉLIA.",
    epistemicClass: "OBSERVATION",
    limitations: [],
    groundingStatus: null,
    provenance: null,
    presentation: {
      messageKind: "RESULT",
      semanticStatus: "OBSERVATION",
      groundingStatus: null,
      blocks: [],
      allowedInteractions: ["reply"],
    },
    ...overrides,
  };
}

function renderMessage(turn: ConversationDisplayTurn) {
  const onConfirmation = vi.fn();
  const view = render(
    <ul>
      <li className="delia-turn delia-turn--delia">
        <DeliaAssistantMessage
          turn={turn}
          loading={false}
          onConfirmation={onConfirmation}
        />
      </li>
    </ul>,
  );
  return { ...view, onConfirmation };
}

afterEach(cleanup);

describe("DeliaAssistantMessage — RESULT", () => {
  it("renders glyph, label and content without state badge", () => {
    const { container } = renderMessage(makeTurn());
    expect(container.querySelector(".delia-turn__avatar svg")).toBeTruthy();
    expect(screen.getByText("DÉLIA")).toBeTruthy();
    expect(screen.getByText("Resposta da DÉLIA.")).toBeTruthy();
    expect(
      container.querySelector(".delpi-ui-status-badge"),
    ).toBeNull();
  });

  it("preserves long multi-paragraph content verbatim", () => {
    const long = `Primeiro parágrafo.\n\nSegundo parágrafo com código 10090045 e preço 1234.56.\n\n- item a\n- item b`;
    renderMessage(makeTurn({ content: long }));
    expect(screen.getByText(/Primeiro parágrafo/)).toBeTruthy();
    expect(screen.getByText(/item b/)).toBeTruthy();
    expect(
      (screen.getByText(/Primeiro parágrafo/) as HTMLElement)
        .textContent,
    ).toBe(long);
  });

  it("adversarial content stays inert text", () => {
    renderMessage(
      makeTurn({ content: '<img src=x onerror="alert(1)"><script>x</script>' }),
    );
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });
});

describe("DeliaAssistantMessage — semantic states", () => {
  const cases: Array<[string, string]> = [
    ["CLARIFICATION_REQUIRED", "Esclarecimento necessário"],
    ["CONFIRMATION_REQUIRED", "Confirmação pendente"],
    ["WRITE_REJECTED", "Operação recusada"],
    ["AUTHZ_DENIED", "Acesso não autorizado"],
    ["SOURCE_UNAVAILABLE", "Fonte indisponível"],
    ["PRECONDITION_REQUIRED", "Pré-condição pendente"],
  ];

  for (const [kind, label] of cases) {
    it(`${kind} renders icon + badge`, () => {
      const { container } = renderMessage(
        makeTurn({
          presentation: {
            messageKind: kind as never,
            semanticStatus: null,
            groundingStatus: null,
            blocks: [],
            allowedInteractions: [],
          },
        }),
      );
      expect(screen.getByText(label)).toBeTruthy();
      const state = container.querySelector(".delia-turn__state");
      expect(state).toBeTruthy();
      expect(state!.querySelector("svg")).toBeTruthy();
    });
  }

  it("unknown message_kind renders neutral content, no badge", () => {
    const { container } = renderMessage(
      makeTurn({
        presentation: {
          messageKind: null,
          semanticStatus: null,
          groundingStatus: null,
          blocks: [],
          allowedInteractions: [],
        },
      }),
    );
    expect(screen.getByText("Resposta da DÉLIA.")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-status-badge")).toBeNull();
  });

  it("CONFIRMATION_REQUIRED echoes digests on confirm/reject", () => {
    const request = {
      session_id: "s-9",
      proposal_digest: "d".repeat(64),
      preview_fingerprint: "f".repeat(64),
    };
    const { onConfirmation } = renderMessage(
      makeTurn({
        presentation: {
          messageKind: "CONFIRMATION_REQUIRED",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [],
          allowedInteractions: ["reply", "confirm", "reject"],
        },
        confirmationRequest: request,
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    expect(onConfirmation).toHaveBeenCalledWith(request, "CONFIRM");
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onConfirmation).toHaveBeenCalledWith(request, "REJECT");
    // Digests are transport echoes — never displayed.
    expect(screen.queryByText(/d{64}/)).toBeNull();
  });

  it("answered confirmation is consumed", () => {
    renderMessage(
      makeTurn({
        confirmationRequest: {
          session_id: "s-1",
          proposal_digest: "a".repeat(64),
          preview_fingerprint: "b".repeat(64),
        },
        confirmationAnswered: true,
      }),
    );
    expect(
      screen.queryByRole("group", { name: "Confirmação pendente" }),
    ).toBeNull();
  });
});

describe("DeliaAssistantMessage — provenance, epistemic, limitations", () => {
  it("renders real provenance when GROUNDED", () => {
    renderMessage(
      makeTurn({
        groundingStatus: "GROUNDED",
        provenance: {
          source: { source_id: "s", source_system: "delpi" },
          specialist_id: "delpi",
          protocol: "HTTP",
          observed_at: "2026-10-09T12:00:00Z",
        },
      }),
    );
    const meta = screen.getByLabelText("Detalhes da resposta");
    expect(meta.textContent).toContain("fonte:");
    expect(meta.textContent).toContain("delpi/HTTP");
    expect(meta.textContent).toContain("classificação: OBSERVATION");
  });

  it("renders 'sem fonte vinculada' when NON_GROUNDED", () => {
    renderMessage(makeTurn({ groundingStatus: "NON_GROUNDED" }));
    expect(screen.getByText("sem fonte vinculada")).toBeTruthy();
  });

  it("renders limitations verbatim in subordinate meta", () => {
    renderMessage(
      makeTurn({ limitations: ["deterministic_test_adapter", "bounded"] }),
    );
    const meta = screen.getByLabelText("Detalhes da resposta");
    expect(meta.textContent).toContain(
      "limitações: deterministic_test_adapter, bounded",
    );
  });

  it("owner hint renders once and is deduped from content", () => {
    renderMessage(
      makeTurn({
        content:
          "Não foi possível concluir. A fonte informou: glpi_link_required.",
        presentation: {
          messageKind: "PRECONDITION_REQUIRED",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [
            { kind: "text", text: "Não foi possível concluir." },
            {
              kind: "notice",
              role: "owner_hint",
              text: "glpi_link_required.",
            },
          ],
          allowedInteractions: ["reply"],
        },
      }),
    );
    expect(screen.getAllByText(/glpi_link_required/)).toHaveLength(1);
    expect(screen.getByText("Não foi possível concluir.")).toBeTruthy();
  });
});

describe("DeliaAssistantMessage — copy action", () => {
  it("copies the visible response text via clipboard when available", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText },
    });
    renderMessage(makeTurn({ content: "texto copiável" }));

    fireEvent.click(
      screen.getByRole("button", { name: "Copiar resposta" }),
    );
    expect(writeText).toHaveBeenCalledWith("texto copiável");
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Resposta copiada" }),
      ).toBeTruthy(),
    );
  });

  it("exposes no invented actions (no feedback/share/source buttons)", () => {
    const { container } = renderMessage(makeTurn());
    const labels = Array.from(
      container.querySelectorAll("button"),
    ).map((b) => b.getAttribute("aria-label") ?? b.textContent);
    for (const label of labels) {
      expect(label).not.toMatch(/avaliar|compartilhar|fonte|detalhe/i);
    }
    // Exactly one secondary action — copy.
    expect(container.querySelectorAll("button")).toHaveLength(1);
  });
});
