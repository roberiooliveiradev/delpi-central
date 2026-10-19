// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { makeMachineLoadOperation } from "../utils/machineLoadTestPayload";
import { MachineLoadRowContextMenu } from "./MachineLoadRowContextMenu";

const operation = makeMachineLoadOperation();

type MenuProps = ComponentProps<typeof MachineLoadRowContextMenu>;

function makeProps(overrides: Partial<MenuProps> = {}): MenuProps {
  return {
    open: true,
    position: { x: 100, y: 100 },
    operation,
    onClose: vi.fn(),
    onTraceConjunto: vi.fn(),
    onPrioritizeConjunto: vi.fn(),
    onWithdrawConjunto: vi.fn(),
    onTransferConjunto: vi.fn(),
    onTransferOperation: vi.fn(),
    ...overrides,
  };
}

afterEach(() => cleanup());

describe("MachineLoadRowContextMenu — modo individual", () => {
  it("mantém as ações individuais sem seleção múltipla", () => {
    const props = makeProps({ selectionCount: 0, onClearSelection: vi.fn() });
    render(<MachineLoadRowContextMenu {...props} />);

    expect(screen.getByRole("menu", { name: /ações/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Rastrear produção do conjunto/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Priorizar conjunto/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Retirar conjunto/i })).toBeTruthy();
    expect(
      screen.getByRole("menuitem", { name: /Enviar conjunto para outro centro/i }),
    ).toBeTruthy();
    expect(
      screen.getByRole("menuitem", { name: /Enviar item para outro centro/i }),
    ).toBeTruthy();
    expect(screen.queryByRole("menuitem", { name: /operações selecionadas/i })).toBeNull();
  });

  it("oferece «Solicitar correção a Processos» e repassa a operação clicada", () => {
    const onReportProcessIssue = vi.fn();
    const onClose = vi.fn();
    const props = makeProps({ onReportProcessIssue, onClose });
    render(<MachineLoadRowContextMenu {...props} />);

    const item = screen.getByRole("menuitem", {
      name: /Solicitar correção a Processos/i,
    });
    fireEvent.click(item);

    expect(onReportProcessIssue).toHaveBeenCalledWith(operation);
    expect(onClose).toHaveBeenCalled();
  });

  it("uma única operação selecionada ainda mostra o menu individual", () => {
    const props = makeProps({ selectionCount: 1, onClearSelection: vi.fn() });
    render(<MachineLoadRowContextMenu {...props} />);
    expect(screen.getByRole("menuitem", { name: /Rastrear produção do conjunto/i })).toBeTruthy();
    expect(screen.queryByRole("menuitem", { name: /Limpar seleção/i })).toBeNull();
  });
});

describe("MachineLoadRowContextMenu — modo coletivo", () => {
  it("mostra contagem e mantém ações sem handler desabilitadas", () => {
    const props = makeProps({ selectionCount: 3, onClearSelection: vi.fn() });
    render(<MachineLoadRowContextMenu {...props} />);

    expect(screen.getByRole("menu", { name: /seleção/i })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /3 operações selecionadas/i })).toBeTruthy();

    const group = screen.getByRole("menuitem", { name: /Agrupar operações selecionadas/i });
    const transfer = screen.getByRole("menuitem", { name: /Enviar selecionadas/i });
    const withdraw = screen.getByRole("menuitem", { name: /Retirar selecionadas/i });
    // Sem handler a ação nunca simula disponibilidade — disabled é o default.
    expect(group).toHaveProperty("disabled", true);
    expect(transfer).toHaveProperty("disabled", true);
    expect(withdraw).toHaveProperty("disabled", true);

    // Menu individual não aparece no modo coletivo — e a abertura de
    // chamado a Processos é sempre unitária (nunca em lote).
    expect(screen.queryByRole("menuitem", { name: /Rastrear produção do conjunto/i })).toBeNull();
    expect(screen.queryByRole("menuitem", { name: /Solicitar correção a Processos/i })).toBeNull();
  });

  it("transferir e retirar a seleção executam os callbacks coletivos", () => {
    const onTransferSelected = vi.fn();
    const onWithdrawSelected = vi.fn();
    const props = makeProps({
      selectionCount: 3,
      onClearSelection: vi.fn(),
      onTransferSelected,
      onWithdrawSelected,
    });
    render(<MachineLoadRowContextMenu {...props} />);

    const transfer = screen.getByRole("menuitem", { name: /Enviar selecionadas/i });
    expect(transfer).toHaveProperty("disabled", false);
    fireEvent.click(transfer);
    expect(onTransferSelected).toHaveBeenCalledTimes(1);
    expect(props.onClose).toHaveBeenCalledTimes(1);

    cleanup();
    render(<MachineLoadRowContextMenu {...props} />);
    const withdraw = screen.getByRole("menuitem", { name: /Retirar selecionadas/i });
    expect(withdraw).toHaveProperty("disabled", false);
    fireEvent.click(withdraw);
    expect(onWithdrawSelected).toHaveBeenCalledTimes(1);
    // As ações coletivas nunca tocam os callbacks individuais.
    expect(props.onWithdrawConjunto).not.toHaveBeenCalled();
    expect(props.onTransferOperation).not.toHaveBeenCalled();
  });

  it("bloqueio coletivo desabilita transferir e retirar com hint", () => {
    const onTransferSelected = vi.fn();
    const onWithdrawSelected = vi.fn();
    const props = makeProps({
      selectionCount: 2,
      onClearSelection: vi.fn(),
      onTransferSelected,
      onWithdrawSelected,
      collectiveDisabled: true,
      collectiveDisabledHint: "Estado de execução indisponível",
    });
    render(<MachineLoadRowContextMenu {...props} />);

    const transfer = screen.getByRole("menuitem", { name: /Enviar selecionadas/i });
    const withdraw = screen.getByRole("menuitem", { name: /Retirar selecionadas/i });
    expect(transfer).toHaveProperty("disabled", true);
    expect(withdraw).toHaveProperty("disabled", true);
    fireEvent.click(transfer);
    fireEvent.click(withdraw);
    expect(onTransferSelected).not.toHaveBeenCalled();
    expect(onWithdrawSelected).not.toHaveBeenCalled();
  });

  it("«Limpar seleção» é a única ação executável no modo coletivo", () => {
    const props = makeProps({ selectionCount: 2, onClearSelection: vi.fn() });
    render(<MachineLoadRowContextMenu {...props} />);

    fireEvent.click(screen.getByRole("menuitem", { name: /Limpar seleção/i }));
    expect(props.onClearSelection).toHaveBeenCalledTimes(1);
    expect(props.onClose).toHaveBeenCalledTimes(1);
    expect(props.onWithdrawConjunto).not.toHaveBeenCalled();
    expect(props.onTransferConjunto).not.toHaveBeenCalled();
    expect(props.onTransferOperation).not.toHaveBeenCalled();
  });

  it("cliques nas ações coletivas desabilitadas não executam mutação", () => {
    const onGroupSelected = vi.fn();
    const props = makeProps({
      selectionCount: 4,
      onClearSelection: vi.fn(),
      onGroupSelected,
      groupDisabled: true,
      groupDisabledHint: "Motivo de bloqueio",
    });
    render(<MachineLoadRowContextMenu {...props} />);

    fireEvent.click(screen.getByRole("menuitem", { name: /Agrupar operações selecionadas/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /Retirar selecionadas/i }));
    expect(onGroupSelected).not.toHaveBeenCalled();
    expect(props.onWithdrawConjunto).not.toHaveBeenCalled();
    expect(props.onTransferConjunto).not.toHaveBeenCalled();
    expect(props.onTransferOperation).not.toHaveBeenCalled();
    expect(props.onClose).not.toHaveBeenCalled();
  });

  it("«Agrupar» elegível executa o callback e fecha o menu", () => {
    const onGroupSelected = vi.fn();
    const props = makeProps({
      selectionCount: 3,
      onClearSelection: vi.fn(),
      onGroupSelected,
      groupDisabled: false,
    });
    render(<MachineLoadRowContextMenu {...props} />);

    const group = screen.getByRole("menuitem", { name: /Agrupar operações selecionadas/i });
    expect(group).toHaveProperty("disabled", false);
    fireEvent.click(group);
    expect(onGroupSelected).toHaveBeenCalledTimes(1);
    expect(props.onClose).toHaveBeenCalledTimes(1);
    // A ação nunca toca os callbacks das operações individuais.
    expect(props.onWithdrawConjunto).not.toHaveBeenCalled();
    expect(props.onTransferOperation).not.toHaveBeenCalled();
  });

  it("«Agrupar» bloqueado exibe o motivo como hint", () => {
    const props = makeProps({
      selectionCount: 2,
      onClearSelection: vi.fn(),
      onGroupSelected: vi.fn(),
      groupDisabled: true,
      groupDisabledHint: "Agrupamento bloqueado: OP 1 · operação 02 está em execução.",
    });
    render(<MachineLoadRowContextMenu {...props} />);
    expect(
      screen.getByRole("menuitem", { name: /Agrupar operações selecionadas/i }),
    ).toHaveProperty("disabled", true);
  });
});
