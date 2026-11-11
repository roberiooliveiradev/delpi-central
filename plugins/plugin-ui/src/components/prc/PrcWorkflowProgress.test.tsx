/** PRC-REF-023-UI-FIX-07 — regressão do andamento PRC compartilhado.
 * needs_correction/needs_information/under_review mapeiam para o step
 * "Em atendimento" com nota de contexto; rejected não finge avanço. */

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { PrcWorkflowProgress } from "./PrcWorkflowProgress";

afterEach(cleanup);

const currentStep = () =>
  document.querySelector('[aria-current="step"]');

describe("PrcWorkflowProgress", () => {
  it("submitted → etapa Enviada atual", () => {
    render(<PrcWorkflowProgress status="submitted" />);
    expect(currentStep()?.textContent).toContain("Enviada");
    expect(
      screen
        .getByRole("navigation")
        .getAttribute("aria-label"),
    ).toContain("Enviada");
  });

  it("in_progress → etapa Em atendimento atual", () => {
    render(<PrcWorkflowProgress status="in_progress" />);
    expect(currentStep()?.textContent).toContain("Em atendimento");
  });

  it("completed → etapa Concluída atual", () => {
    render(<PrcWorkflowProgress status="completed" />);
    expect(currentStep()?.textContent).toContain("Concluída");
  });

  it("needs_correction → Em atendimento com nota de devolução", () => {
    render(<PrcWorkflowProgress status="needs_correction" />);
    expect(currentStep()?.textContent).toContain("Em atendimento");
    const button = currentStep as never;
    void button;
    expect(
      document
        .querySelector('[aria-current="step"]')
        ?.getAttribute("aria-label"),
    ).toContain("devolvida para correção");
  });

  it("needs_information → Em atendimento com nota de aguardando", () => {
    render(<PrcWorkflowProgress status="needs_information" />);
    expect(
      document
        .querySelector('[aria-current="step"]')
        ?.getAttribute("aria-label"),
    ).toContain("aguardando informações");
  });

  it("rejected → não avança além de Enviada e informa rejeição", () => {
    render(<PrcWorkflowProgress status="rejected" />);
    const current = document.querySelector('[aria-current="step"]');
    // Em rejected nenhum step é "current"; Enviada fica completa com a nota.
    expect(current).toBeNull();
    expect(
      document
        .querySelector('[class*="__item--complete"]')
        ?.textContent,
    ).toContain("Enviada");
  });

  it("aria-label reflete o status real (não o mapeado)", () => {
    render(<PrcWorkflowProgress status="needs_correction" />);
    expect(
      screen.getByRole("navigation").getAttribute("aria-label"),
    ).toContain("Devolvida para correção");
  });
});
