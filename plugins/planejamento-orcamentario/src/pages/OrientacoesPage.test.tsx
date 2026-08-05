import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard:
    () =>
    function SectionCard({
      title,
      children,
    }: {
      title: string;
      children: ReactNode;
    }) {
      return (
        <section>
          <h2>{title}</h2>
          {children}
        </section>
      );
    },
  createDashboardLoadingActivityCard:
    () =>
    function LoadingActivityCard({ title }: { title: string }) {
      return <div>{title}</div>;
    },
  createDashboardStateBox:
    () =>
    function StateBox({ children }: { children: ReactNode }) {
      return <div role="alert">{children}</div>;
    },
}));

import { OrientacoesPage, DECLARATION_TEXT } from "./OrientacoesPage";
import * as budgetApi from "../api/budgetPlanningApi";

vi.mock("../api/budgetPlanningApi");

const guidanceFixture = {
  id: "g1",
  version_number: 1,
  title: "Carta 2027",
  published_at: "2026-08-01T12:00:00Z",
  board_message: "Mensagem institucional de abertura.",
  objective: "Consolidar metas e investimentos alinhados à estratégia.",
  premises: [
    { id: "p1", name: "Câmbio", value_text: "Taxa média projetada de R$ 5,10." },
    { id: "p2", name: "Inflação", value_text: "IPCA meta de 4,5%.", unit_label: "%" },
  ],
  general_guidance: "Elaborar projeções com base no histórico e premissas aprovadas.",
  schedule: [
    {
      id: "s1",
      title: "Publicação das orientações",
      starts_on: "2026-08-01",
      description: "Disponibilização oficial.",
    },
  ],
  acknowledged: false,
};

const documentsFixture = [
  {
    id: "d1",
    display_name: "Manual do ciclo",
    original_name: "manual-ciclo.pdf",
    mime_type: "application/pdf",
    size_bytes: 204800,
    document_kind: "pdf",
  },
];

beforeEach(() => {
  vi.mocked(budgetApi.fetchCurrentGuidance).mockResolvedValue(guidanceFixture as never);
  vi.mocked(budgetApi.fetchCurrentGuidanceDocuments).mockResolvedValue(documentsFixture as never);
  vi.mocked(budgetApi.acknowledgeCurrentGuidance).mockResolvedValue({ acknowledged: true });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("OrientacoesPage", () => {
  it("mantém o botão de confirmação desabilitado até marcar a declaração", async () => {
    render(<OrientacoesPage />);

    await waitFor(() => {
      expect(screen.getByText(DECLARATION_TEXT)).toBeTruthy();
    });

    const confirmButton = screen.getByTestId("orientacoes-confirm-button") as HTMLButtonElement;
    expect(confirmButton.disabled).toBe(true);

    fireEvent.click(screen.getByTestId("orientacoes-declaration-checkbox"));
    expect(confirmButton.disabled).toBe(false);
  });

  it("exibe estado de sucesso após confirmar leitura", async () => {
    render(<OrientacoesPage />);

    await waitFor(() => {
      expect(screen.getByTestId("orientacoes-confirm-button")).toBeTruthy();
    });

    fireEvent.click(screen.getByTestId("orientacoes-declaration-checkbox"));
    fireEvent.click(screen.getByTestId("orientacoes-confirm-button"));

    await waitFor(() => {
      expect(budgetApi.acknowledgeCurrentGuidance).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId("orientacoes-confirmed")).toBeTruthy();
    });

    expect(screen.queryByTestId("orientacoes-confirm-button")).toBeNull();
  });

  it("renderiza seções institucionais após carregar", async () => {
    render(<OrientacoesPage />);

    await waitFor(() => {
      expect(screen.getByText("Mensagem da diretoria")).toBeTruthy();
      expect(screen.getByText("Premissas")).toBeTruthy();
      expect(screen.getByText("Cronograma")).toBeTruthy();
      expect(screen.getByText("Manual do ciclo")).toBeTruthy();
    });
  });
});
