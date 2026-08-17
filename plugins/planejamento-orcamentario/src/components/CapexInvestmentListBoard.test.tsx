import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard: () => () => null,
  createDashboardLoadingActivityCard: () => () => null,
  createDashboardStateBox: () => () => null,
  createHostContainedModalShell:
    () =>
    function HostContainedDialog({
      open,
      title,
      description,
      onClose,
      children,
    }: {
      open: boolean;
      title: ReactNode;
      description?: ReactNode;
      onClose: () => void;
      children?: ReactNode;
    }) {
      if (!open) return null;
      return (
        <div role="dialog" aria-modal="true" aria-label={String(title)}>
          {description ? <p>{description}</p> : null}
          <button type="button" aria-label="Fechar" onClick={onClose}>
            Fechar
          </button>
          {children}
        </div>
      );
    },
}));

import { CapexInvestmentListBoard } from "./CapexInvestmentListBoard";
import type { CapexInvestment } from "../types/budgetPlanning";

const row: CapexInvestment = {
  id: "inv-1",
  exercise_id: "ex-2027",
  unit_id: "01",
  cost_center_id: "205",
  category_id: "cat-1",
  description: "Sala de Interação",
  estimated_amount: "30000.00",
  currency: "BRL",
  required_date: "2027-10-01",
  priority: "2",
  origin: "national",
  status: "draft",
  version: 1,
  is_complete: true,
  missing_fields: [],
  justification: "Melhorar o atendimento ao cliente interno.",
};

describe("CapexInvestmentListBoard", () => {
  afterEach(() => {
    cleanup();
  });

  it("renderiza colunas do mockup e menu de ações", () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(
      <div className="dashboard-planejamento-orcamentario">
        <CapexInvestmentListBoard
          items={[row]}
          categoryMap={
            new Map([
              [
                "cat-1",
                {
                  id: "cat-1",
                  code: "OBRAS",
                  name: "Obras e Construção Civil",
                  display_order: 1,
                  icon_key: "building",
                  is_active: true,
                  is_system_default: true,
                },
              ],
            ])
          }
          planEditable
          onEdit={onEdit}
          onDelete={onDelete}
        />
      </div>,
    );

    expect(screen.getByText("Sala de Interação")).toBeTruthy();
    expect(screen.getByText("Obras e Construção Civil")).toBeTruthy();
    expect(screen.queryByText(/· CAPEX/i)).toBeNull();
    expect(screen.getByText("Alta")).toBeTruthy();
    expect(screen.getByText("R$ 30.000,00")).toBeTruthy();
    expect(screen.queryByLabelText(/concluído/i)).toBeNull();
    expect(screen.getByText(/Pronto para revisão/i)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Ações do investimento/i }));
    const menu = screen.getByRole("menu");
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Editar/i }));
    expect(onEdit).toHaveBeenCalledWith("inv-1");
  });

  it("mostra Aguardando decisão quando o plano foi enviado", () => {
    render(
      <div className="dashboard-planejamento-orcamentario">
        <CapexInvestmentListBoard
          items={[row]}
          categoryMap={new Map()}
          planEditable={false}
          planStatus="submitted"
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      </div>,
    );
    expect(screen.getByText(/Aguardando decisão/i)).toBeTruthy();
    expect(screen.queryByText(/Pronto para revisão/i)).toBeNull();
  });

  it("abre modal de detalhes ao clicar na linha", () => {
    const onEdit = vi.fn();
    render(
      <div className="dashboard-planejamento-orcamentario">
        <CapexInvestmentListBoard
          items={[row]}
          categoryMap={
            new Map([
              [
                "cat-1",
                {
                  id: "cat-1",
                  code: "OBRAS",
                  name: "Obras e Construção Civil",
                  display_order: 1,
                  icon_key: "building",
                  is_active: true,
                  is_system_default: true,
                },
              ],
            ])
          }
          planEditable
          onEdit={onEdit}
          onDelete={vi.fn()}
        />
      </div>,
    );

    fireEvent.click(screen.getByRole("button", { name: /Ver detalhes de Sala de Interação/i }));
    const dialog = screen.getByRole("dialog", { name: /Sala de Interação/i });
    expect(within(dialog).getByText(/Valor solicitado/i)).toBeTruthy();
    expect(within(dialog).getByText(/Outubro de 2027/i)).toBeTruthy();
    expect(within(dialog).getByText(/Melhorar o atendimento/i)).toBeTruthy();

    fireEvent.click(within(dialog).getByRole("button", { name: /^Editar$/i }));
    expect(onEdit).toHaveBeenCalledWith("inv-1");
  });
});
