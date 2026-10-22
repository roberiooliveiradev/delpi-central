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
    ["PROCESSING_TIMEOUT", "Processamento interrompido"],
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
      const state = container.querySelector(
        ".delpi-ui-conversation-status",
      );
      expect(state).toBeTruthy();
      expect(state!.querySelector("svg")).toBeTruthy();
      expect(
        state!.querySelector(".delpi-ui-status-badge"),
      ).toBeTruthy();
    });
  }

  it("RESULT renders no ConversationStatus", () => {
    const { container } = renderMessage(
      makeTurn({
        presentation: {
          messageKind: "RESULT",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [],
          allowedInteractions: [],
        },
      }),
    );
    expect(
      container.querySelector(".delpi-ui-conversation-status"),
    ).toBeNull();
  });

  it("prose containing state words does not create a status", () => {
    const { container } = renderMessage(
      makeTurn({ content: "Acesso negado, erro e fonte indisponível." }),
    );
    expect(
      container.querySelector(".delpi-ui-conversation-status"),
    ).toBeNull();
  });

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
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar e executar" }),
    );
    expect(onConfirmation).toHaveBeenCalledWith(request, "CONFIRM");
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onConfirmation).toHaveBeenCalledWith(request, "REJECT");
    // Technical fields are transport echoes — never displayed.
    expect(screen.queryByText(/d{64}/)).toBeNull();
    expect(screen.queryByText(/f{64}/)).toBeNull();
    expect(screen.queryByText(/s-[0-9]/)).toBeNull();
  });

  it("CONFIRMATION_REQUIRED without request renders no action surface", () => {
    renderMessage(
      makeTurn({
        presentation: {
          messageKind: "CONFIRMATION_REQUIRED",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [],
          allowedInteractions: ["reply", "confirm", "reject"],
        },
        confirmationRequest: null,
      }),
    );
    // The semantic status remains, but the action surface does not.
    expect(screen.getByText("Confirmação pendente")).toBeTruthy();
    expect(
      screen.queryByRole("group", { name: "Confirmação necessária" }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Confirmar e executar" }),
    ).toBeNull();
  });

  it("execution-scope choice renders the scope-choice card", () => {
    // §6.184: pending_purpose=execution_scope_choice — owner declared
    // no extra confirmation; a single Executar is the scope decision.
    const request = {
      session_id: "s-9",
      proposal_digest: "d".repeat(64),
      preview_fingerprint: "f".repeat(64),
      pending_purpose: "execution_scope_choice" as const,
    };
    const { onConfirmation } = renderMessage(
      makeTurn({ confirmationRequest: request }),
    );
    expect(
      screen.getByRole("group", { name: "Operação pronta para execução" }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Executar" }));
    expect(onConfirmation).toHaveBeenCalledWith(request, "CONFIRM");
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onConfirmation).toHaveBeenCalledWith(request, "REJECT");
  });

  it("owner confirmation purpose renders the confirmation copy", () => {
    const request = {
      session_id: "s-9",
      proposal_digest: "d".repeat(64),
      preview_fingerprint: "f".repeat(64),
      pending_purpose:
        "execution_scope_plus_owner_confirmation" as const,
    };
    renderMessage(makeTurn({ confirmationRequest: request }));
    expect(
      screen.getByRole("group", { name: "Confirmação necessária" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Confirmar e executar" }),
    ).toBeTruthy();
    expect(
      screen.getByText(/exige confirmação explícita/),
    ).toBeTruthy();
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
      screen.queryByRole("group", { name: "Confirmação necessária" }),
    ).toBeNull();
  });
});

describe("DeliaAssistantMessage — provenance, epistemic, limitations", () => {
  it("renders real provenance when GROUNDED", () => {
    renderMessage(
      makeTurn({
        groundingStatus: "GROUNDED",
        epistemicClass: "OBSERVATION",
        provenance: {
          source: { source_id: "s", source_system: "delpi" },
          specialist_id: "delpi",
          protocol: "HTTP",
          observed_at: "2026-10-09T12:00:00Z",
        },
      }),
    );
    // Visible summary without opening the disclosure.
    expect(screen.getByText(/Fonte · delpi/)).toBeTruthy();
    const trigger = screen.getByRole("button", {
      name: /Detalhes da evidência/,
    });
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(trigger);
    // dl/dt/dd pairs: class, source, specialist, observed time.
    expect(screen.getByText("OBSERVATION")).toBeTruthy();
    expect(screen.getByText("Especialista")).toBeTruthy();
    expect(screen.getByText("Observado em")).toBeTruthy();
    // protocol is technical-only — never on the user-facing surface.
    expect(document.body.textContent).not.toContain("HTTP");
    expect(document.body.textContent).not.toContain("delpi/");
  });

  it("renders 'Sem fonte vinculada' when NON_GROUNDED", () => {
    renderMessage(makeTurn({ groundingStatus: "NON_GROUNDED" }));
    expect(screen.getByText("Sem fonte vinculada")).toBeTruthy();
  });

  it("omits the observed time when the value is invalid", () => {
    renderMessage(
      makeTurn({
        groundingStatus: "GROUNDED",
        provenance: {
          source: { source_id: "s", source_system: "delpi" },
          observed_at: "not-a-date",
        },
      }),
    );
    expect(screen.getByText(/Fonte · delpi/)).toBeTruthy();
    expect(screen.queryByText(/consultado em/)).toBeNull();
    expect(screen.queryByText(/not-a-date/)).toBeNull();
  });

  it("renders limitations verbatim inside the disclosure", () => {
    renderMessage(
      makeTurn({ limitations: ["deterministic_test_adapter", "bounded"] }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /Detalhes da evidência/ }),
    );
    expect(screen.getByText("deterministic_test_adapter")).toBeTruthy();
    expect(screen.getByText("bounded")).toBeTruthy();
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

describe("DeliaAssistantMessage — presentation.v2 frontend reader", () => {
  it("keeps v1 / unmarked turns as literal text (Markdown inactive)", () => {
    const source = "**não** deve virar negrito\n- item";
    const { container } = renderMessage(makeTurn({ content: source }));
    const paragraph = container.querySelector("p.delia-turn__content");
    expect(paragraph?.textContent).toBe(source);
    expect(
      container.querySelector(
        ".delia-turn__content strong, .delia-turn__content ul",
      ),
    ).toBeNull();
    expect(
      container.querySelector(".delpi-ui-conversation-markdown"),
    ).toBeNull();
  });

  it("renders markdown_safe only from an explicit synthetic v2 admission", () => {
    const markdown = "## Resultado\n\n- OP-10293\n- 3 KG";
    const { container } = renderMessage(
      makeTurn({
        content: "Resultado\n\n- OP-10293\n- 3 KG",
        contentFormat: "markdown_safe",
        markdownSource: markdown,
        presentation: {
          messageKind: "RESULT",
          semanticStatus: "OBSERVATION",
          groundingStatus: null,
          blocks: [{ kind: "text", format: "markdown_safe", text: markdown }],
          allowedInteractions: ["reply"],
        },
      }),
    );
    const md = container.querySelector(".delpi-ui-conversation-markdown");
    expect(md).toBeTruthy();
    expect(md?.querySelector("h4")?.textContent).toBe("Resultado");
    expect(md?.querySelectorAll("li")).toHaveLength(2);
    expect(md?.querySelector("a")).toBeNull();
  });

  it("renders v2 plain as literal text", () => {
    const { container } = renderMessage(
      makeTurn({
        content: "**ainda literal**",
        contentFormat: "plain",
        markdownSource: null,
        presentation: {
          messageKind: "RESULT",
          semanticStatus: null,
          groundingStatus: null,
          blocks: [{ kind: "text", format: "plain", text: "**ainda literal**" }],
          allowedInteractions: ["reply"],
        },
      }),
    );
    expect(container.querySelector("strong")).toBeNull();
    expect(container.querySelector("p.delia-turn__content")?.textContent).toBe(
      "**ainda literal**",
    );
  });

  it("shows a neutral error for presentationFault without activating Markdown", () => {
    const { container } = renderMessage(
      makeTurn({
        content: "não usar",
        presentationFault: "neutral_error",
        contentFormat: "markdown_safe",
        markdownSource: "## x",
      }),
    );
    expect(container.querySelector(".delpi-ui-conversation-markdown")).toBeNull();
    expect(
      screen.getByText("Não foi possível apresentar esta resposta."),
    ).toBeTruthy();
  });

  it("does not navigate unauthorized URLs even under markdown_safe", () => {
    const { container } = renderMessage(
      makeTurn({
        content: "link",
        contentFormat: "markdown_safe",
        markdownSource: "[abrir](https://example.org)",
        authorizedLinks: [],
      }),
    );
    expect(container.querySelector("a")).toBeNull();
    expect(container.textContent).toContain("abrir");
  });

  it("preserves EvidenceDetails and GovernedConfirmation beside markdown", () => {
    renderMessage(
      makeTurn({
        content: "plain",
        contentFormat: "markdown_safe",
        markdownSource: "**ok**",
        groundingStatus: "NON_GROUNDED",
        confirmationRequest: {
          session_id: "s",
          proposal_digest: "d",
          preview_fingerprint: "f",
          pending_purpose: "execution_scope_choice",
        },
      }),
    );
    expect(screen.getByText("Sem fonte vinculada")).toBeTruthy();
    expect(screen.getByText("Operação pronta para execução")).toBeTruthy();
    expect(screen.getByText("ok")).toBeTruthy();
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

  it("renders actions through ConversationAssistantActions", () => {
    const { container } = renderMessage(makeTurn());
    const bar = container.querySelector(
      ".delpi-ui-conversation-assistant-actions",
    );
    expect(bar).toBeTruthy();
    expect(bar!.getAttribute("aria-label")).toBe("Ações da resposta");
    expect(
      bar!.querySelector('button[aria-label="Copiar resposta"]'),
    ).toBeTruthy();
    expect(container.querySelector(".delia-turn__action")).toBeNull();
  });

  it("does not report success when the clipboard write rejects", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("denied"));
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText },
    });
    renderMessage(makeTurn({ content: "x" }));
    fireEvent.click(
      screen.getByRole("button", { name: "Copiar resposta" }),
    );
    await Promise.resolve();
    await Promise.resolve();
    expect(
      screen.getByRole("button", { name: "Copiar resposta" }),
    ).toBeTruthy();
    expect(
      screen.queryByRole("button", { name: "Resposta copiada" }),
    ).toBeNull();
  });

  it("prepares feedback/regenerate disabled without backend and keeps copy active", () => {
    renderMessage(makeTurn());
    expect(
      (screen.getByRole("button", { name: "Copiar resposta" }) as HTMLButtonElement)
        .disabled,
    ).toBe(false);
    expect(
      (screen.getByRole("button", { name: "Útil" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Não útil" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(
      (screen.getByRole("button", { name: "Refazer resposta" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(screen.queryByRole("button", { name: "Mais opções" })).toBeNull();
  });

  it("copies markdown_safe readable text when presentation admits Markdown", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", {
      ...navigator,
      clipboard: { writeText },
    });
    renderMessage(
      makeTurn({
        content: "Resultado\n\n- OP-10293",
        contentFormat: "markdown_safe",
        markdownSource: "## Resultado\n\n- OP-10293",
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Copiar resposta" }));
    expect(writeText).toHaveBeenCalled();
    const copied = writeText.mock.calls[0]?.[0] as string;
    expect(copied).toContain("Resultado");
    expect(copied).toContain("OP-10293");
    expect(copied).not.toContain("##");
  });
});
