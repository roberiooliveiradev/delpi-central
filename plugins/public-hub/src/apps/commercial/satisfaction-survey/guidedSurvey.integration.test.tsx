/**
 * §14.10.4 — integração com o `GuidedQuestionnaire` REAL do plugin-ui,
 * importado do código-fonte (não do stub de Federation). Responde as 12
 * avaliações obrigatórias, revisa, envia e verifica o payload entregue ao
 * `submitPublicSurvey` — a mesma fiação usada pela página.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeAll, describe, expect, it, vi } from "vitest";

// Caminho relativo: contorna o alias `@delpi/plugin-ui` → stub. Sem isso o
// componente renderizado seria o no-op de teste, não o kit real.
import { GuidedQuestionnaire } from "../../../../../plugin-ui/src/components/forms/questionnaire/index";

import {
  normalizeQuestionnaire,
  submitPublicSurvey,
  type PublicSurveyState,
  type SubmitOutcome,
} from "../api.ts";
import { rawQuestionnaire } from "../testFixtures.ts";
import { buildSurveySteps } from "./surveyDefinition.ts";
import { submitSurveyAnswers } from "./surveyResults.ts";
import { SURVEY_TEXTS } from "./surveyTexts.ts";

vi.mock("../api.ts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api.ts")>();
  return { ...actual, submitPublicSurvey: vi.fn() };
});

beforeAll(() => {
  // jsdom não implementa scrollIntoView (chamado pelo kit nas transições).
  window.HTMLElement.prototype.scrollIntoView = vi.fn();
});

function openSurvey(): Extract<PublicSurveyState, { status: "open" }> {
  const questionnaire = normalizeQuestionnaire(rawQuestionnaire());
  if (!questionnaire) throw new Error("fixture do questionário inválida");
  return {
    status: "open",
    token: "tok-integracao",
    companyName: "Empresa Teste",
    campaignName: "CAMPANHA-INTERNA",
    startsAt: "2026-03-02T12:00:00Z",
    endsAt: "2026-03-20T12:00:00Z",
    questionnaire,
  };
}

function pickNote(container: HTMLElement, key: string, name: string) {
  const question = container.querySelector(`[data-gq-question="${key}"]`);
  if (!(question instanceof HTMLElement)) {
    throw new Error(`pergunta ${key} não encontrada`);
  }
  fireEvent.click(within(question).getByRole("radio", { name }));
}

describe("GuidedQuestionnaire real + definição da Pesquisa", () => {
  it("fluxo completo: 12 obrigatórias → revisão → envio → payload correto", async () => {
    const survey = openSurvey();
    vi.mocked(submitPublicSurvey).mockResolvedValue({
      outcome: "submitted",
    } satisfies SubmitOutcome);

    const { container } = render(
      <GuidedQuestionnaire
        logo={{ src: "/p/logoMinhaDelpi.svg", alt: "Minha DELPI" }}
        intro={{
          eyebrow: "PESQUISA DE SATISFAÇÃO",
          title: "Pesquisa de Satisfação de Clientes",
          startLabel: "Começar",
        }}
        header={{ title: "Pesquisa de Satisfação de Clientes" }}
        steps={buildSurveySteps(survey.questionnaire)}
        texts={SURVEY_TEXTS}
        colorScheme="auto"
        onSubmit={(answers) => submitSurveyAnswers(survey, answers)}
      />,
    );

    // Abertura → etapa 1 (dimensões 1–5, todas nota 4).
    fireEvent.click(screen.getByRole("button", { name: "Começar" }));
    for (const key of [
      "quality",
      "delivery_deadline",
      "service",
      "agility",
      "communication",
    ]) {
      pickNote(container, key, "4 — Satisfeito");
    }
    fireEvent.click(screen.getByRole("button", { name: "Avançar" }));

    // Etapa 2 (dimensões 6–10): uma N/A, demais nota 3.
    pickNote(container, "technical_support", "Não se aplica");
    for (const key of [
      "commercial_support",
      "flexibility",
      "reliability",
      "partnership",
    ]) {
      pickNote(container, key, "3 — Neutro");
    }
    fireEvent.click(screen.getByRole("button", { name: "Avançar" }));

    // Etapa 3: geral 5, recomendação 9 e uma aberta preenchida.
    pickNote(container, "overall_score", "5 — Muito satisfeito");
    pickNote(container, "recommendation_score", "9");
    const strengths = container.querySelector(
      '[data-gq-question="strengths"]',
    );
    if (!(strengths instanceof HTMLElement)) {
      throw new Error("pergunta strengths não encontrada");
    }
    fireEvent.change(within(strengths).getByRole("textbox"), {
      target: { value: "Atendimento ágil" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Revisar respostas" }),
    );

    // Revisão → envio.
    await screen.findByText("Revise suas respostas");
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar respostas" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText("Obrigado por participar!"),
      ).toBeInTheDocument(),
    );

    expect(submitPublicSurvey).toHaveBeenCalledTimes(1);
    expect(submitPublicSurvey).toHaveBeenCalledWith("tok-integracao", {
      overall_score: 5,
      recommendation_score: 9,
      dimensions: {
        quality: 4,
        delivery_deadline: 4,
        service: 4,
        agility: 4,
        communication: 4,
        technical_support: null,
        commercial_support: 3,
        flexibility: 3,
        reliability: 3,
        partnership: 3,
      },
      strengths: "Atendimento ágil",
      improvements: null,
      unmet_needs: null,
    });
  });
});
