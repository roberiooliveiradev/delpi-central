/** @vitest-environment jsdom */
import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { MachineLoadOperation } from "./api.ts";
import { ProcessIssueModal } from "./ProcessIssueModal.tsx";
import {
  PROCESS_ISSUE_REASONS,
  type ProcessIssueDraft,
} from "./processIssue.ts";
import type { ProcessIssueSubmitResult } from "./useProcessIssue.ts";

const OPERATION = {
  work_center: "CT-63",
  work_center_name: "Montagem 03",
  scheduled_date: "2026-10-09",
  scheduled_start_time: "07:30",
  scheduled_end_date: "2026-10-09",
  scheduled_end_time: "17:30",
  production_order: "24640401002",
  operation_code: "03",
  operation_description: "MONTAGEM",
  tool: "F99999",
  resource: null,
  product_code: "10045678",
  product_description: "Componente X",
  unit: "PC",
  planned_qty: 100,
  produced_qty: 50,
  pending_qty: 50,
  pa_product_code: "90264238",
  pa_product_description: "Produto acabado",
  pa_due_date: "2026-10-15",
  due_date: "2026-10-15",
  production_status: "not_started",
  is_in_production: false,
  production_started_date: null,
  production_started_time: null,
  active_operator_name: null,
  active_operator_count: null,
  appointment_count: null,
  last_appointment_date: null,
} satisfies MachineLoadOperation;

function setup(overrides: Partial<Parameters<typeof ProcessIssueModal>[0]> = {}) {
  const onSubmit = vi.fn(
    async (_draft: ProcessIssueDraft): Promise<ProcessIssueSubmitResult> => ({
      ok: true,
      message: null,
    }),
  );
  const onClose = vi.fn();
  render(
    <ProcessIssueModal
      open
      operation={OPERATION}
      workCenter="CT-63"
      busy={false}
      error={null}
      onSubmit={onSubmit}
      onClose={onClose}
      {...overrides}
    />,
  );
  return { onSubmit, onClose };
}

describe("ProcessIssueModal", () => {
  it("renders title and operation context", () => {
    setup();
    expect(
      screen.getByRole("heading", { name: "Informar problema de processo" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/OP 24640401002 · Operação 03 · CT-63/),
    ).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("shows the six reason options as selectable buttons", () => {
    setup();
    const buttons = screen
      .getAllByRole("button")
      .filter((el) => el.getAttribute("aria-pressed") !== null);
    expect(buttons).toHaveLength(6);
    for (const item of PROCESS_ISSUE_REASONS) {
      expect(
        screen.getByRole("button", { name: item.label }),
      ).toHaveAttribute("aria-pressed", "false");
    }
  });

  it("requires a reason before submitting", async () => {
    const { onSubmit } = setup();
    fireEvent.click(screen.getByRole("button", { name: "Enviar para Processos" }));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Selecione o tipo de problema encontrado.",
      ),
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows tool code only for tool_not_linked", () => {
    setup();
    expect(screen.queryByLabelText(/Código da ferramenta/)).toBeNull();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Ferramenta não informada ou não vinculada",
      }),
    );
    expect(
      screen.getByLabelText(/Código da ferramenta \(opcional\)/),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/Código do material/)).toBeNull();
    // trocar de motivo esconde o campo de ferramenta
    fireEvent.click(
      screen.getByRole("button", { name: "Limitação da máquina ou bancada" }),
    );
    expect(screen.queryByLabelText(/Código da ferramenta/)).toBeNull();
  });

  it("shows material code only for material_not_linked", () => {
    setup();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Matéria-prima não vinculada à operação",
      }),
    );
    const input = screen.getByLabelText(/Código do material \(opcional\)/);
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("maxLength", "60");
    // o campo é texto livre — NÃO lista materiais SD4
    expect(
      screen.queryByText(/Carregando materiais/),
    ).toBeNull();
  });

  it("submits the draft with optional fields", async () => {
    const { onSubmit, onClose } = setup();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Ferramenta não informada ou não vinculada",
      }),
    );
    fireEvent.change(screen.getByLabelText(/Código da ferramenta/), {
      target: { value: "F12345" },
    });
    fireEvent.change(screen.getByLabelText(/Observação/), {
      target: { value: "Ferramenta não consta." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar para Processos" }),
    );
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toEqual({
      issueCode: "tool_not_linked",
      toolCode: "F12345",
      materialCode: null,
      note: "Ferramenta não consta.",
    });
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("keeps the modal open and shows the error on failure", async () => {
    const onSubmit = vi.fn(
      async (_draft: ProcessIssueDraft): Promise<ProcessIssueSubmitResult> => ({
        ok: false,
        message:
          "Não foi possível enviar a solicitação para Processos. Tente novamente.",
      }),
    );
    const { onClose } = setup({ onSubmit, error: null });
    fireEvent.click(screen.getByRole("button", { name: "Outro problema de processo" }));
    fireEvent.click(screen.getByRole("button", { name: "Enviar para Processos" }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onClose).not.toHaveBeenCalled();
    // modal segue aberto com o rascunho intacto
    expect(
      screen.getByRole("button", { name: "Outro problema de processo" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("renders the submit error from props as alert", () => {
    setup({ error: "Esta operação não está mais disponível neste posto." });
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Esta operação não está mais disponível neste posto.",
    );
  });

  it("Escape closes only when not busy", () => {
    const { onClose } = setup();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("Escape does NOT close while busy", () => {
    const { onClose } = setup({ busy: true });
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).not.toHaveBeenCalled();
  });

  it("busy disables submit and shows Enviando", () => {
    setup({ busy: true });
    const send = screen.getByRole("button", { name: "Enviando…" });
    expect(send).toBeDisabled();
    expect(send).toHaveAttribute("aria-busy", "true");
  });

  it("disclaimer is shown and no internal jargon leaks", () => {
    setup();
    expect(screen.getByText(/departamento de Processos/)).toBeInTheDocument();
    const html = document.body.innerHTML;
    for (const jargon of ["S2S", "snapshot", "idempoten", "requests-api"]) {
      expect(html.toLowerCase()).not.toContain(jargon.toLowerCase());
    }
  });

  it("resets the form when reopened", async () => {
    const onSubmit = vi.fn(
      async (_draft: ProcessIssueDraft): Promise<ProcessIssueSubmitResult> => ({
        ok: false,
        message: "erro",
      }),
    );
    const { rerender } = render(
      <ProcessIssueModal
        open={false}
        operation={OPERATION}
        workCenter="CT-63"
        busy={false}
        error={null}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />,
    );
    rerender(
      <ProcessIssueModal
        open
        operation={OPERATION}
        workCenter="CT-63"
        busy={false}
        error={null}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />,
    );
    await waitFor(() =>
      screen.getByRole("button", { name: "Outro problema de processo" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Outro problema de processo" }),
    );
    fireEvent.change(screen.getByLabelText(/Observação/), {
      target: { value: "rascunho" },
    });
    // fecha e reabre → campos limpos
    rerender(
      <ProcessIssueModal
        open={false}
        operation={OPERATION}
        workCenter="CT-63"
        busy={false}
        error={null}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />,
    );
    rerender(
      <ProcessIssueModal
        open
        operation={OPERATION}
        workCenter="CT-63"
        busy={false}
        error={null}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Outro problema de processo" }),
      ).toHaveAttribute("aria-pressed", "false");
      expect(screen.getByLabelText(/Observação/)).toHaveValue("");
    });
  });
});
