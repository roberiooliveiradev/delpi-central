import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { normalizeQuestionnaire, type PublicSurveyState } from "./api.ts";
import { SurveyFormView } from "./FormPage";
import { rawQuestionnaire } from "./testFixtures.ts";

const questionnaire = normalizeQuestionnaire(rawQuestionnaire());
if (!questionnaire) throw new Error("fixture inválida");

const survey: Extract<PublicSurveyState, { status: "open" }> = {
  status: "open",
  token: "tok_ABCDEFGHIJKLMNOP",
  campaignName: "Pesquisa 2026",
  startsAt: "2026-03-01T03:00:00Z",
  endsAt: "2026-03-31T20:59:00Z",
  companyName: "Alfa",
  questionnaire,
};

function jsonResponse(status: number, body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }),
  );
}

/** Responde a etapa atual: nota 5 nas dimensões, ou geral + recomendação na etapa 3. */
function fillStep(index: 1 | 2 | 3) {
  const keys =
    index === 1
      ? ["quality", "delivery_deadline", "service", "agility", "communication"]
      : index === 2
        ? ["technical_support", "commercial_support", "flexibility", "reliability", "partnership"]
        : [];
  for (const key of keys) {
    const radios = document.querySelectorAll<HTMLInputElement>(`input[name="${key}"]`);
    fireEvent.click(radios[4]);
  }
  if (index === 3) {
    fireEvent.click(document.querySelectorAll<HTMLInputElement>('input[name="overall_score"]')[4]);
    fireEvent.click(document.querySelector<HTMLInputElement>('input[name="recommendation_score"][value="0"]')!);
  }
}

function goToReview() {
  fireEvent.click(screen.getByRole("button", { name: "Iniciar pesquisa" }));
  fillStep(1);
  fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
  fillStep(2);
  fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
  fillStep(3);
  fireEvent.click(screen.getByRole("button", { name: "Revisar respostas" }));
}

describe("SurveyFormView", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("não pede identificação pessoal e bloqueia avanço com pendências, destacando a primeira", () => {
    render(<SurveyFormView survey={survey} />);
    expect(screen.queryByLabelText(/nome|e-?mail|cpf/i)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Iniciar pesquisa" }));
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Faltam 5 avaliações obrigatórias");
    expect(screen.getByText(/Etapa 1 de 3/)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("progresso conta 12 avaliações e N/A vale como resposta; sem POST entre etapas", () => {
    render(<SurveyFormView survey={survey} />);
    fireEvent.click(screen.getByRole("button", { name: "Iniciar pesquisa" }));
    fireEvent.click(document.querySelectorAll<HTMLInputElement>('input[name="quality"]')[5]);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuetext", "1 de 12 avaliações concluídas");
    fillStep(1);
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    expect(screen.getByText(/Etapa 2 de 3/)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "42");
    fireEvent.click(screen.getByRole("button", { name: "Anterior" }));
    expect(screen.getByText(/Etapa 1 de 3/)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("beforeunload só enquanto há respostas não enviadas", () => {
    render(<SurveyFormView survey={survey} />);
    const untouched = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(untouched);
    expect(untouched.defaultPrevented).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Iniciar pesquisa" }));
    fireEvent.click(document.querySelectorAll<HTMLInputElement>('input[name="quality"]')[0]);
    const dirty = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(dirty);
    expect(dirty.defaultPrevented).toBe(true);
  });

  it("revisão lista as 15 perguntas, permite editar por etapa e só envia ao confirmar", async () => {
    fetchMock.mockImplementation(() => jsonResponse(201, { success: true, data: {} }));
    render(<SurveyFormView survey={survey} />);
    goToReview();
    expect(screen.getByRole("heading", { name: "Revisar respostas" })).toBeInTheDocument();
    expect(document.querySelectorAll(".satform-review-item")).toHaveLength(15);
    expect(fetchMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /Editar etapa 2/ }));
    expect(screen.getByText(/Etapa 2 de 3/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Voltar à revisão" }));
    expect(screen.getByRole("heading", { name: "Revisar respostas" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    const confirm = screen.getByRole("button", { name: "Confirmar e enviar" });
    fireEvent.click(confirm);
    fireEvent.click(confirm); // duplo clique não gera segundo POST
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Obrigado por participar!" })).toBeInTheDocument(),
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/public\/satisfaction-surveys\/tok_ABCDEFGHIJKLMNOP\/response$/);
    const body = JSON.parse(String(init.body)) as Record<string, unknown>;
    expect(body.recommendation_score).toBe(0);
    expect(Object.keys(body)).not.toContain("respondent_name");
    // Tela final sem resumo, sem notas e sem nome da empresa.
    expect(document.body.textContent).not.toMatch(/Alfa|Pergunta 1/);
    expect(window.localStorage.length + window.sessionStorage.length).toBe(0);
  });

  it("409 já respondida mostra estado específico (não o agradecimento)", async () => {
    fetchMock.mockImplementation(() =>
      jsonResponse(409, { success: false, message: "Esta pesquisa já foi respondida.", data: { code: "already_submitted" } }),
    );
    render(<SurveyFormView survey={survey} />);
    goToReview();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar e enviar" }));
    await waitFor(() => expect(screen.getByText("Resposta já registrada")).toBeInTheDocument());
    expect(screen.queryByText("Obrigado por participar!")).toBeNull();
  });

  it("falha de rede mantém as respostas na revisão e não declara sucesso", async () => {
    fetchMock.mockImplementation(() => Promise.reject(new TypeError("network")));
    render(<SurveyFormView survey={survey} />);
    goToReview();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar e enviar" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Não foi possível confirmar o envio"));
    expect(screen.queryByText("Obrigado por participar!")).toBeNull();
    const review = screen.getByRole("region", { name: "Revisão das respostas" });
    expect(within(review).getByRole("button", { name: "Confirmar e enviar" })).toBeEnabled();
    expect(document.querySelectorAll(".satform-review-item")).toHaveLength(15);
  });
});
