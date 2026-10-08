// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MachineLoadOptimizationModal } from "./MachineLoadOptimizationModal";

vi.mock("./PpcConfirmModal", () => ({
  HostContainedDialog: ({
    open,
    title,
    children,
    onClose,
  }: {
    open: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        <h2>{title}</h2>
        <button type="button" onClick={onClose}>
          Fechar
        </button>
        {children}
      </div>
    ) : null,
}));

function renderModal(props: Partial<Parameters<typeof MachineLoadOptimizationModal>[0]> = {}) {
  const onClose = vi.fn();
  const onConfirm = vi.fn();
  const utils = render(
    <MachineLoadOptimizationModal
      open
      onClose={onClose}
      onConfirm={onConfirm}
      {...props}
    />,
  );
  return { onClose, onConfirm, ...utils };
}

afterEach(cleanup);

describe("MachineLoadOptimizationModal", () => {
  it("abre com título, Data de entrega marcada e obrigatória", () => {
    renderModal();

    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText("Otimizar fila de produção")).toBeTruthy();
    expect(screen.getByText("Obrigatório")).toBeTruthy();
    const delivery = screen.getByLabelText(/Data de entrega/);
    expect((delivery as HTMLInputElement).checked).toBe(true);
    expect((delivery as HTMLInputElement).disabled).toBe(true);
  });

  it("Ferramenta inicia desmarcada e pode ser marcada", () => {
    renderModal();

    const tool = screen.getByLabelText(/^Ferramenta/) as HTMLInputElement;
    expect(tool.checked).toBe(false);
    fireEvent.click(tool);
    expect(tool.checked).toBe(true);
  });

  it("data de entrega não pode ser desmarcada", () => {
    renderModal();

    const delivery = screen.getByLabelText(/Data de entrega/) as HTMLInputElement;
    fireEvent.click(delivery);
    expect(delivery.checked).toBe(true);
  });

  it("cancelar fecha sem confirmar", () => {
    const { onClose, onConfirm } = renderModal();

    fireEvent.click(screen.getByText("Cancelar"));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("confirma data-only com ferramenta desmarcada", () => {
    const { onConfirm } = renderModal();

    fireEvent.click(screen.getByRole("button", { name: "Otimizar fila" }));

    expect(onConfirm).toHaveBeenCalledWith(false);
  });

  it("confirma data+ferramenta quando marcada", () => {
    const { onConfirm } = renderModal();

    fireEvent.click(screen.getByLabelText(/^Ferramenta/));
    fireEvent.click(screen.getByRole("button", { name: "Otimizar fila" }));

    expect(onConfirm).toHaveBeenCalledWith(true);
  });

  it("busy desabilita submit e mostra texto de progresso", () => {
    renderModal({ busy: true });

    const confirm = screen.getByRole("button", { name: "Otimizando fila…" });
    expect((confirm as HTMLButtonElement).disabled).toBe(true);
    expect(confirm.getAttribute("aria-busy")).toBe("true");
  });

  it("erro fica visível e a escolha permanece", () => {
    renderModal({ error: "falha simulada" });

    fireEvent.click(screen.getByLabelText(/^Ferramenta/));

    expect(screen.getByRole("alert").textContent).toContain("falha simulada");
    expect((screen.getByLabelText(/^Ferramenta/) as HTMLInputElement).checked).toBe(true);
  });

  it("estado de ferramenta reinicia a cada abertura", () => {
    const { rerender } = renderModal();
    fireEvent.click(screen.getByLabelText(/^Ferramenta/));
    expect((screen.getByLabelText(/^Ferramenta/) as HTMLInputElement).checked).toBe(true);

    rerender(
      <MachineLoadOptimizationModal open={false} onClose={vi.fn()} onConfirm={vi.fn()} />,
    );
    rerender(
      <MachineLoadOptimizationModal open onClose={vi.fn()} onConfirm={vi.fn()} />,
    );

    expect((screen.getByLabelText(/^Ferramenta/) as HTMLInputElement).checked).toBe(false);
  });
});
