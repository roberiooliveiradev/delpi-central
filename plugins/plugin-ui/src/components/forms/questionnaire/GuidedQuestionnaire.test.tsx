import {
  act,
  cleanup,
  fireEvent,
  render,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { GuidedQuestionnaire } from "./GuidedQuestionnaire";
import type {
  GuidedQuestionnaireTexts,
  QuestionnaireStep,
} from "./guidedQuestionnaireTypes";

afterEach(cleanup);

beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

const TEXTS: GuidedQuestionnaireTexts = {
  back: "Voltar",
  next: "Avançar",
  review: "Revisar",
  backToReview: "Voltar à revisão",
  submit: "Enviar respostas",
  submitting: "Enviando…",
  requiredLabel: "obrigatória",
  optionalLabel: "(opcional)",
  scaleError: "Selecione uma nota.",
  scaleErrorWithNa: "Selecione uma nota ou “Não se aplica”.",
  textError: "Escreva uma resposta.",
  stepFooterPending: (n) => `Responda ${n} pergunta(s) para continuar.`,
  stepLabel: (i, total, title) => `Etapa ${i} de ${total} · ${title}`,
  progressLabel: (d, t) => `${d} de ${t}`,
  progressAriaLabel: (d, t) => `Progresso ${d} de ${t}`,
  reviewTitle: "Revisão final",
  reviewDescription: "Confira antes de enviar.",
  reviewNotice: "Após o envio não será possível alterar.",
  reviewNaValue: "Não se aplica",
  reviewEmptyValue: "Sem resposta",
  submitError: "Não foi possível enviar. Tente novamente.",
  editLabel: "Editar",
  editAriaLabel: (t) => `Editar respostas de ${t}`,
  themeToggleAriaLabel: "Alternar tema",
};

const STEPS: QuestionnaireStep[] = [
  {
    id: "s1",
    title: "Conteúdo",
    questions: [
      {
        kind: "scale",
        key: "s1q1",
        eyebrow: "Didática",
        number: 1,
        prompt: "Como avalia a didática?",
        required: true,
        scale: {
          min: 1, max: 5,
          optionLabel: (n) => `Didática ${n}`,
          endLabels: { min: "Ruim", max: "Ótimo" },
          notApplicable: { label: "Não se aplica" },
          reviewValue: (n) => `${n} de 5`,
        },
      },
      {
        kind: "scale",
        key: "s1q2",
        number: 2,
        prompt: "Probabilidade de recomendar?",
        required: true,
        scale: {
          min: 0, max: 10,
          optionLabel: (n) => `Recomendar ${n}`,
          endLabels: { min: "Baixa", max: "Alta" },
          endLabelsPosition: "above",
          narrowColumns: 6,
        },
      },
    ],
  },
  {
    id: "s2",
    title: "Comentários",
    reviewTitle: "Comentários finais",
    questions: [
      {
        kind: "scale",
        key: "s2q1",
        number: 3,
        prompt: "Avaliação geral?",
        required: true,
        scale: {
          min: 1, max: 5,
          optionLabel: (n) => `Geral ${n}`,
          endLabels: { min: "Ruim", max: "Ótimo" },
        },
      },
      {
        kind: "text",
        key: "s2q2",
        number: 4,
        prompt: "Sugestões?",
        required: false,
        text: { label: "Sugestões", placeholder: "Opcional" },
      },
      {
        kind: "text",
        key: "s2q3",
        number: 5,
        prompt: "Comentário final?",
        required: true,
        text: { label: "Comentário" },
      },
    ],
  },
];

function baseProps(overrides: Record<string, unknown> = {}) {
  return {
    logo: { src: "data:,", alt: "Marca" },
    intro: {
      title: "Avaliação do treinamento",
      description: "Responda em 2 etapas.",
      startLabel: "Começar",
    },
    header: { title: "Avaliação" },
    steps: STEPS,
    texts: TEXTS,
    onSubmit: vi.fn(async () => ({
      type: "result" as const,
      result: { tone: "success" as const, title: "Enviado", message: "Obrigado" },
    })),
    ...overrides,
  };
}

function startFlow(getByRole: ReturnType<typeof render>["getByRole"]) {
  fireEvent.click(getByRole("button", { name: "Começar" }));
}

describe("GuidedQuestionnaire — fluxo", () => {
  it("intro → pendência (foco+contagem) → respostas → voltar preserva → revisão → editar → enviar", async () => {
    const props = baseProps();
    const { getByRole, container, queryByRole } = render(
      <GuidedQuestionnaire {...props} />,
    );

    // Abertura
    expect(getByRole("button", { name: "Começar" })).toBeTruthy();
    startFlow(getByRole);

    // Etapa 1 — foco no título da etapa (tabIndex -1)
    expect(document.activeElement?.textContent).toContain("Etapa 1 de 2 · Conteúdo");

    // Avançar sem responder → 2 pendências, contagem no rodapé, foco na 1ª
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    expect(getByRole("status").textContent).toBe("Responda 2 pergunta(s) para continuar.");
    expect(container.querySelectorAll(".delpi-ui-form-card--tone-invalid")).toHaveLength(2);
    const firstRadio = container.querySelector<HTMLElement>(
      '[data-gq-question="s1q1"] input[type="radio"]',
    )!;
    expect(document.activeElement).toBe(firstRadio);

    // Responde s1q1 → pendência dela some; contagem cai para 1
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    await waitFor(() =>
      expect(container.querySelectorAll(".delpi-ui-form-card--tone-invalid")).toHaveLength(1),
    );
    expect(getByRole("status").textContent).toBe("Responda 1 pergunta(s) para continuar.");

    // Responde s1q2 → avança para etapa 2 (foco no título)
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    expect(document.activeElement?.textContent).toContain("Etapa 2 de 2 · Comentários");

    // Responde s2q1 e s2q3 (s2q2 opcional fica vazia)
    fireEvent.click(getByRole("radio", { name: "Geral 5" }));
    fireEvent.change(
      container.querySelector('[data-gq-question="s2q3"] textarea')!,
      { target: { value: "  Muito bom o curso.  " } },
    );

    // Voltar preserva respostas (progresso 3/3 mantido)
    fireEvent.click(getByRole("button", { name: "Voltar" }));
    expect(
      container.querySelector<HTMLInputElement>(
        '[data-gq-question="s1q1"] input[value="4"]',
      )!.checked,
    ).toBe(true);
    fireEvent.click(getByRole("button", { name: "Avançar" }));

    // Revisar → tela de revisão com seções por etapa
    fireEvent.click(getByRole("button", { name: "Revisar" }));
    expect(document.activeElement?.textContent).toBe("Revisão final");
    const rows = [...container.querySelectorAll("dd")].map((d) => d.textContent);
    expect(rows).toContain("4 de 5");          // reviewValue
    expect(rows).toContain("9");               // número puro
    expect(rows).toContain("5");               // s2q1
    expect(rows).toContain("Sem resposta");    // opcional vazia → muted
    expect(rows).toContain("Muito bom o curso."); // texto trimado
    expect(container.textContent).toContain("Após o envio não será possível alterar.");

    // Editar etapa 1 → só o primário "Voltar à revisão" (sem Voltar)
    fireEvent.click(getByRole("button", { name: "Editar respostas de Conteúdo" }));
    expect(queryByRole("button", { name: "Voltar" })).toBeNull();
    fireEvent.click(getByRole("button", { name: "Voltar à revisão" }));
    expect(getByRole("button", { name: "Enviar respostas" })).toBeTruthy();

    // Envio
    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(props.onSubmit).toHaveBeenCalledTimes(1),
    );
    expect(props.onSubmit).toHaveBeenCalledWith({
      s1q1: 4,
      s1q2: 9,
      s2q1: 5,
      s2q3: "Muito bom o curso.",
    });
    await waitFor(() =>
      expect(getByRole("heading", { name: "Enviado" })).toBeTruthy(),
    );
    // foco no título do resultado (§10.8.2)
    expect(document.activeElement?.textContent).toBe("Enviado");
  });

  it("duplo clique no envio dispara onSubmit uma única vez", async () => {
    const props = baseProps();
    const { getByRole, container } = render(<GuidedQuestionnaire {...props} />);
    startFlow(getByRole);
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    fireEvent.click(getByRole("radio", { name: "Geral 5" }));
    fireEvent.change(
      container.querySelector('[data-gq-question="s2q3"] textarea')!,
      { target: { value: "ok" } },
    );
    fireEvent.click(getByRole("button", { name: "Revisar" }));
    const send = getByRole("button", { name: "Enviar respostas" });
    fireEvent.click(send);
    fireEvent.click(getByRole("button", { name: "Enviando…" }));
    await waitFor(() => expect(props.onSubmit).toHaveBeenCalledTimes(1));
  });

  it("dois cliques no mesmo ciclo disparam onSubmit uma única vez", async () => {
    const props = baseProps();
    const { getByRole, container } = render(<GuidedQuestionnaire {...props} />);
    startFlow(getByRole);
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    fireEvent.click(getByRole("radio", { name: "Geral 5" }));
    fireEvent.change(
      container.querySelector('[data-gq-question="s2q3"] textarea')!,
      { target: { value: "ok" } },
    );
    fireEvent.click(getByRole("button", { name: "Revisar" }));
    const send = getByRole("button", { name: "Enviar respostas" });
    // dois cliques dentro do mesmo ciclo de renderização (antes do re-render)
    act(() => {
      fireEvent.click(send);
      fireEvent.click(send);
    });
    await waitFor(() => expect(props.onSubmit).toHaveBeenCalledTimes(1));
  });

  it("após retry, novo clique envia de novo (trava liberada)", async () => {
    const onSubmit = vi
      .fn()
      .mockResolvedValueOnce({ type: "retry", message: "Tente de novo." })
      .mockResolvedValue({
        type: "result",
        result: { tone: "success", title: "Enviado", message: "ok" },
      });
    const props = baseProps({ onSubmit });
    const { getByRole, container } = render(<GuidedQuestionnaire {...props} />);
    startFlow(getByRole);
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    fireEvent.click(getByRole("radio", { name: "Geral 5" }));
    fireEvent.change(
      container.querySelector('[data-gq-question="s2q3"] textarea')!,
      { target: { value: "ok" } },
    );
    fireEvent.click(getByRole("button", { name: "Revisar" }));
    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(container.textContent).toContain("Tente de novo."),
    );
    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(getByRole("heading", { name: "Enviado" })).toBeTruthy(),
    );
    expect(onSubmit).toHaveBeenCalledTimes(2);
  });

  it("retry mantém respostas, mostra aviso com foco; exceção vira erro genérico", async () => {
    const onSubmit = vi
      .fn()
      .mockResolvedValueOnce({ type: "retry", message: "Conflito temporário." })
      .mockRejectedValueOnce(new Error("rede"))
      .mockResolvedValue({ type: "result", result: { tone: "success", title: "Enviado", message: "ok" } });
    const props = baseProps({ onSubmit });
    const { getByRole, container } = render(<GuidedQuestionnaire {...props} />);
    startFlow(getByRole);
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    fireEvent.click(getByRole("radio", { name: "Geral 5" }));
    fireEvent.change(
      container.querySelector('[data-gq-question="s2q3"] textarea')!,
      { target: { value: "ok" } },
    );
    fireEvent.click(getByRole("button", { name: "Revisar" }));

    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(container.textContent).toContain("Conflito temporário."),
    );
    expect(document.activeElement?.textContent).toContain("Conflito temporário.");
    // respostas intactas na revisão
    expect(container.textContent).toContain("4 de 5");

    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(container.textContent).toContain("Não foi possível enviar. Tente novamente."),
    );

    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(getByRole("heading", { name: "Enviado" })).toBeTruthy(),
    );
    expect(onSubmit).toHaveBeenCalledTimes(3);
  });

  it("não persiste nada no navegador durante o fluxo", async () => {
    const lsSet = vi.spyOn(Storage.prototype, "setItem");
    const ssSet = vi.spyOn(window.sessionStorage, "setItem");
    let cookieSet: ReturnType<typeof vi.spyOn> | undefined;
    try {
      cookieSet = vi.spyOn(document, "cookie", "set");
    } catch {
      cookieSet = undefined; // jsdom pode não expor setter espiável
    }
    const props = baseProps();
    const { getByRole } = render(<GuidedQuestionnaire {...props} />);
    startFlow(getByRole);
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    await waitFor(() => expect(lsSet).not.toHaveBeenCalled());
    expect(ssSet).not.toHaveBeenCalled();
    if (cookieSet) expect(cookieSet).not.toHaveBeenCalled();
    lsSet.mockRestore();
    ssSet.mockRestore();
    cookieSet?.mockRestore();
  });

  it("beforeunload registra após a 1ª resposta e remove no resultado", async () => {
    const add = vi.spyOn(window, "addEventListener");
    const remove = vi.spyOn(window, "removeEventListener");
    const props = baseProps();
    const { getByRole, container, unmount } = render(
      <GuidedQuestionnaire {...props} />,
    );
    startFlow(getByRole);
    expect(add).not.toHaveBeenCalledWith("beforeunload", expect.any(Function));
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    await waitFor(() =>
      expect(add).toHaveBeenCalledWith("beforeunload", expect.any(Function)),
    );
    // conclui até o resultado
    fireEvent.click(getByRole("radio", { name: "Recomendar 9" }));
    fireEvent.click(getByRole("button", { name: "Avançar" }));
    fireEvent.click(getByRole("radio", { name: "Geral 5" }));
    fireEvent.change(
      container.querySelector('[data-gq-question="s2q3"] textarea')!,
      { target: { value: "ok" } },
    );
    fireEvent.click(getByRole("button", { name: "Revisar" }));
    fireEvent.click(getByRole("button", { name: "Enviar respostas" }));
    await waitFor(() =>
      expect(remove).toHaveBeenCalledWith("beforeunload", expect.any(Function)),
    );
    unmount();
    add.mockRestore();
    remove.mockRestore();
  });

  it("trocar o tema no meio do fluxo preserva as respostas", async () => {
    const props = baseProps();
    const { getByRole, container } = render(<GuidedQuestionnaire {...props} />);
    startFlow(getByRole);
    fireEvent.click(getByRole("radio", { name: "Didática 4" }));
    fireEvent.click(getByRole("button", { name: "Alternar tema" }));
    expect(
      container.querySelector<HTMLInputElement>(
        '[data-gq-question="s1q1"] input[value="4"]',
      )!.checked,
    ).toBe(true);
    expect(
      container.querySelector(".delpi-ui-form-root")!.getAttribute("data-color-scheme"),
    ).toBe("dark");
  });
});
