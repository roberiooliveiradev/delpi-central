/**
 * Página `commercial.form` (§14.6.4/§14.6.5): estados terminais sem nome da
 * campanha e fiação do `onSubmit` → `submitPublicSurvey` (kit simulado).
 * O fluxo completo com o kit real está em `guidedSurvey.integration.test.tsx`.
 */
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GuidedQuestionnaireProps } from "@delpi/plugin-ui/index";
import type { SubmitOutcome } from "../api.ts";
import {
  normalizeQuestionnaire,
  submitPublicSurvey,
  type PublicSurveyState,
} from "../api.ts";
import { rawQuestionnaire } from "../testFixtures.ts";
import { SatisfactionSurveyPage } from "./SatisfactionSurveyPage.tsx";
import { SURVEY_TEXTS } from "./surveyTexts.ts";

const h = vi.hoisted(() => ({
  guidedProps: { current: null as GuidedQuestionnaireProps | null },
  resultProps: {
    current: null as {
      tone?: string;
      title?: ReactNode;
      message?: ReactNode;
      hint?: ReactNode;
    } | null,
  },
  submitPublicSurvey: vi.fn(
    async (): Promise<SubmitOutcome> => ({ outcome: "submitted" }),
  ),
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  GuidedQuestionnaire: (props: GuidedQuestionnaireProps) => {
    h.guidedProps.current = props;
    return <div data-testid="guided-questionnaire" />;
  },
  QuestionnaireThemeScope: ({ children }: { children?: ReactNode }) => (
    <>{children}</>
  ),
  FormPageLayout: ({ children }: { children?: ReactNode }) => <>{children}</>,
  FormResultPanel: (props: {
    tone?: string;
    title?: ReactNode;
    message?: ReactNode;
    hint?: ReactNode;
    action?: ReactNode;
  }) => {
    h.resultProps.current = props;
    return (
      <div data-testid="result-panel">
        <h1>{props.title}</h1>
        <p>{props.message}</p>
        {props.hint != null ? <p>{props.hint}</p> : null}
        {props.action}
      </div>
    );
  },
  FormLogo: () => null,
  FormButton: ({
    children,
    onClick,
  }: {
    children?: ReactNode;
    onClick?: () => void;
  }) => (
    <button type="button" onClick={onClick}>
      {children}
    </button>
  ),
}));

vi.mock("../api.ts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api.ts")>();
  return { ...actual, submitPublicSurvey: h.submitPublicSurvey };
});

const WINDOW = {
  campaignName: "CAMPANHA-INTERNA-SEGREDO",
  startsAt: "2026-03-02T12:00:00Z",
  endsAt: "2026-03-20T12:00:00Z",
};

function openSurvey(): Extract<PublicSurveyState, { status: "open" }> {
  const questionnaire = normalizeQuestionnaire(rawQuestionnaire());
  if (!questionnaire) throw new Error("fixture inválida");
  return {
    status: "open",
    token: "tok-pagina",
    companyName: "Empresa Teste",
    questionnaire,
    ...WINDOW,
  };
}

beforeEach(() => {
  h.guidedProps.current = null;
  h.resultProps.current = null;
  vi.mocked(submitPublicSurvey).mockClear();
  vi.mocked(submitPublicSurvey).mockResolvedValue({ outcome: "submitted" });
});

describe("estado open", () => {
  it("monta o formulário guiado com a definição, textos e logo reais", () => {
    render(<SatisfactionSurveyPage state={openSurvey()} />);
    const props = h.guidedProps.current;
    expect(props).not.toBeNull();
    expect(props?.logo.src).toBe("/p/logoMinhaDelpi.svg");
    expect(props?.steps).toHaveLength(3);
    expect(props?.steps.flatMap((s) => s.questions)).toHaveLength(15);
    expect(props?.texts).toBe(SURVEY_TEXTS);
    expect(props?.colorScheme).toBe("auto");
    expect(props?.showThemeToggle).toBe(true);
  });

  it("abertura traz empresa, propósito e prazo sem hora", () => {
    render(<SatisfactionSurveyPage state={openSurvey()} />);
    const intro = h.guidedProps.current?.intro;
    expect(intro?.title).toBe("Pesquisa de Satisfação de Clientes");
    expect(intro?.context?.value).toBe("Empresa Teste");
    const items = (intro?.items ?? []).map((item) =>
      typeof item.content === "string" ? item.content : "",
    );
    expect(
      items.some((text) => text.includes("15 perguntas em 3 etapas")),
    ).toBe(true);
    expect(h.guidedProps.current?.header.meta).toBe("Responda até 20/03/2026");
  });

  it("omite o bloco da empresa quando companyName é nulo", () => {
    render(
      <SatisfactionSurveyPage
        state={{ ...openSurvey(), companyName: null }}
      />,
    );
    expect(h.guidedProps.current?.intro.context).toBeUndefined();
    expect(h.guidedProps.current?.header.subtitle).toBeUndefined();
  });

  it("onSubmit entrega o payload mapeado ao submitPublicSurvey uma vez", async () => {
    render(<SatisfactionSurveyPage state={openSurvey()} />);
    const onSubmit = h.guidedProps.current?.onSubmit;
    expect(onSubmit).toBeTypeOf("function");
    const outcome = await onSubmit?.({
      quality: 4,
      overall_score: 5,
      recommendation_score: 0,
      strengths: "  texto  ",
    });
    expect(submitPublicSurvey).toHaveBeenCalledTimes(1);
    const [token, payload] = vi.mocked(submitPublicSurvey).mock.calls[0] ?? [];
    expect(token).toBe("tok-pagina");
    expect(payload).toMatchObject({
      overall_score: 5,
      recommendation_score: 0,
      strengths: "texto",
      improvements: null,
      unmet_needs: null,
    });
    expect(payload?.dimensions.quality).toBe(4);
    expect(outcome?.type).toBe("result");
    if (outcome?.type === "result") {
      expect(outcome.result.tone).toBe("success");
      expect(outcome.result.logo).toBeTruthy();
    }
  });
});

describe("estados terminais", () => {
  const terminalCases: Array<{
    status: Exclude<PublicSurveyState["status"], "open">;
    title: string;
  }> = [
    { status: "not_open", title: "A pesquisa ainda não está aberta" },
    { status: "closed", title: "A pesquisa foi encerrada" },
    { status: "already_submitted", title: "Resposta já registrada" },
    { status: "invalid", title: "Link inválido ou indisponível" },
    {
      status: "temporary_error",
      title: "Pesquisa temporariamente indisponível",
    },
  ];

  for (const { status, title } of terminalCases) {
    it(`${status} → ${title} (sem nome da campanha)`, () => {
      const state: PublicSurveyState =
        status === "invalid" || status === "temporary_error"
          ? { status }
          : { status, ...WINDOW };
      render(<SatisfactionSurveyPage state={state} />);
      expect(screen.getByTestId("result-panel")).toHaveTextContent(title);
      const html = document.body.innerHTML;
      expect(html).not.toContain("CAMPANHA-INTERNA-SEGREDO");
    });
  }

  it("indisponibilidade temporária oferece «Tentar novamente»", () => {
    render(
      <SatisfactionSurveyPage state={{ status: "temporary_error" }} />,
    );
    expect(
      screen.getByRole("button", { name: "Tentar novamente" }),
    ).toBeInTheDocument();
  });

  it("not_open exibe o período sem hora", () => {
    render(
      <SatisfactionSurveyPage state={{ status: "not_open", ...WINDOW }} />,
    );
    expect(screen.getByTestId("result-panel")).toHaveTextContent(
      "Período da pesquisa: 02/03/2026 a 20/03/2026",
    );
  });
});


