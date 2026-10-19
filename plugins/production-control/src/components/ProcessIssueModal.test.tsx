// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { makeMachineLoadOperation } from "../utils/machineLoadTestPayload";
import { ProcessIssueModal } from "./ProcessIssueModal";

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

const operation = makeMachineLoadOperation();

function renderModal(
  props: Partial<Parameters<typeof ProcessIssueModal>[0]> = {},
) {
  const onClose = vi.fn();
  const onSubmit = vi.fn();
  const utils = render(
    <ProcessIssueModal
      open
      operation={operation}
      onClose={onClose}
      onSubmit={onSubmit}
      {...props}
    />,
  );
  return { onClose, onSubmit, ...utils };
}

function selectReason(code: string) {
  const select = screen.getByLabelText(/Problema encontrado/i);
  fireEvent.change(select, { target: { value: code } });
}

afterEach(cleanup);

describe("ProcessIssueModal", () => {
  it("abre com título, contexto da operação e disclaimer", () => {
    renderModal();

    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText("Solicitar correção a Processos")).toBeTruthy();
    expect(screen.getByText(/24640401002/)).toBeTruthy();
    expect(screen.getByText(/CT-01A/)).toBeTruthy();
    expect(screen.getByText(/50320064/)).toBeTruthy();
    expect(screen.getByText(/PA-1/)).toBeTruthy();
    expect(screen.getByText(/23-B31/)).toBeTruthy();
    expect(
      screen.getByText(/não altera automaticamente a produção/i),
    ).toBeTruthy();
  });

  it("lista os seis motivos do catálogo", () => {
    renderModal();
    const select = screen.getByLabelText(/Problema encontrado/i);
    const options = Array.from(
      (select as HTMLSelectElement).querySelectorAll("option"),
    ).map((opt) => opt.textContent);

    expect(options).toEqual(
      expect.arrayContaining([
        "CT / posto não adequado",
        "Limitação da máquina ou bancada",
        "Ferramenta não informada ou não vinculada",
        "Matéria-prima não vinculada à operação",
        "Informação de processo incompleta",
        "Outro problema de processo",
      ]),
    );
  });

  it("exige motivo antes de enviar", () => {
    const { onSubmit } = renderModal();
    fireEvent.click(screen.getByRole("button", { name: /Enviar solicitação/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toMatch(
      /Selecione o tipo de problema/i,
    );
  });

  it("campo de ferramenta só aparece no motivo de ferramenta", () => {
    renderModal();
    expect(screen.queryByLabelText(/Código da ferramenta/i)).toBeNull();

    selectReason("tool_not_linked");
    expect(screen.getByLabelText(/Código da ferramenta/i)).toBeTruthy();

    selectReason("material_not_linked");
    expect(screen.queryByLabelText(/Código da ferramenta/i)).toBeNull();
    expect(screen.getByLabelText(/Código do material/i)).toBeTruthy();

    selectReason("other");
    expect(screen.queryByLabelText(/Código do material/i)).toBeNull();
  });

  it("envia o rascunho com motivo, auxiliar e observação", () => {
    const { onSubmit } = renderModal();
    selectReason("tool_not_linked");
    fireEvent.change(screen.getByLabelText(/Código da ferramenta/i), {
      target: { value: "F-9000" },
    });
    fireEvent.change(screen.getByLabelText(/Observação/i), {
      target: { value: "Ferramenta diverge do roteiro." },
    });
    fireEvent.click(screen.getByRole("button", { name: /Enviar solicitação/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      issueCode: "tool_not_linked",
      toolCode: "F-9000",
      materialCode: null,
      note: "Ferramenta diverge do roteiro.",
    });
  });

  it("busy bloqueia o envio e exibe o estado de envio", () => {
    renderModal({ busy: true });
    const submit = screen.getByRole("button", { name: /Enviando/i });
    expect((submit as HTMLButtonElement).disabled).toBe(true);
  });

  it("exibe o erro de envio vindo do servidor", () => {
    renderModal({ error: "Serviço de solicitações indisponível." });
    expect(screen.getByRole("alert").textContent).toMatch(/indisponível/i);
  });

  it("cancelar fecha sem criar solicitação", () => {
    const { onClose, onSubmit } = renderModal();
    fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));
    expect(onClose).toHaveBeenCalled();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
