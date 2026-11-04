// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HttpRequestError } from "../api/httpClient";
import { LineFeederCollectModal } from "./LineFeederCollectModal";

const queueMock = vi.fn();

vi.mock("../api/ppcApi", () => ({
  fetchLineFeederPublishedQueue: (...args: unknown[]) => queueMock(...args),
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  createHostContainedModalShell: () =>
    function FakeDialog({
      open,
      title,
      children,
      onClose,
    }: {
      open: boolean;
      title: string;
      children: React.ReactNode;
      onClose: () => void;
    }) {
      if (!open) return null;
      return (
        <div role="dialog" aria-label={title}>
          <button type="button" onClick={onClose}>
            fechar-dialog
          </button>
          {children}
        </div>
      );
    },
  createDashboardMultiSelectField: () =>
    function FakeMultiSelect({
      label,
      options,
      selectedValues,
      onChange,
      disabled,
    }: {
      label: string;
      options: Array<{ value: string; label: string }>;
      selectedValues: string[];
      onChange: (values: string[]) => void;
      disabled?: boolean;
    }) {
      return (
        <div>
          <span>{label}</span>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onChange(options.map((option) => option.value))}
          >
            Selecionar todos
          </button>
          <ul>
            {options.map((option) => (
              <li key={option.value}>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedValues.includes(option.value)}
                    disabled={disabled}
                    onChange={(event) => {
                      if (event.target.checked) {
                        onChange([...selectedValues, option.value]);
                      } else {
                        onChange(
                          selectedValues.filter((value) => value !== option.value),
                        );
                      }
                    }}
                  />
                  {option.label}
                </label>
              </li>
            ))}
          </ul>
        </div>
      );
    },
  ConfirmModalPanel: () => null,
  confirmModalBemClasses: () => ({}),
}));

vi.mock("./PpcConfirmModal", () => ({
  HostContainedWideDialog: ({
    open,
    title,
    children,
    onClose,
  }: {
    open: boolean;
    title: string;
    children: React.ReactNode;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog" aria-label={title}>
        <button type="button" onClick={onClose}>
          fechar-dialog
        </button>
        {children}
      </div>
    ) : null,
  HostContainedDialog: () => null,
  PpcConfirmModal: () => null,
}));

vi.mock("./lineFeederUi", () => ({
  LineFeederWorkCenterMultiSelect: ({
    label,
    options,
    selectedValues,
    onChange,
    disabled,
  }: {
    label: string;
    options: Array<{ value: string; label: string }>;
    selectedValues: string[];
    onChange: (values: string[]) => void;
    disabled?: boolean;
  }) => (
    <div>
      <span>{label}</span>
      <button
        type="button"
        disabled={disabled}
        onClick={() => onChange(options.map((option) => option.value))}
      >
        Selecionar todos
      </button>
      <ul>
        {options.map((option) => (
          <li key={option.value}>
            <label>
              <input
                type="checkbox"
                checked={selectedValues.includes(option.value)}
                disabled={disabled}
                onChange={(event) => {
                  if (event.target.checked) {
                    onChange([...selectedValues, option.value]);
                  } else {
                    onChange(selectedValues.filter((value) => value !== option.value));
                  }
                }}
              />
              {option.label}
            </label>
          </li>
        ))}
      </ul>
    </div>
  ),
}));

afterEach(() => {
  cleanup();
  queueMock.mockReset();
});

describe("LineFeederCollectModal", () => {
  it("carrega CTs da fila publicada e permite selecionar todos", async () => {
    queueMock.mockResolvedValue({
      work_centers: [
        { work_center: "CT-A", work_center_name: "Prensa", operation_count: 2 },
        { work_center: "CT-B", work_center_name: "Montagem", operation_count: 1 },
      ],
    });
    const onSubmit = vi.fn();
    render(
      <LineFeederCollectModal
        open
        branch="01"
        onClose={() => undefined}
        onSubmit={onSubmit}
      />,
    );
    expect(await screen.findByText(/CT-A · Prensa/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Selecionar todos" }));
    fireEvent.click(screen.getByRole("button", { name: "3h" }));
    fireEvent.click(screen.getByRole("button", { name: "Consultar materiais" }));
    expect(onSubmit).toHaveBeenCalledWith({
      workCenters: ["CT-A", "CT-B"],
      hoursPerWorkCenter: 3,
    });
  });

  it("lista postos em ordem alfabética pelo código", async () => {
    queueMock.mockResolvedValue({
      work_centers: [
        { work_center: "TOR-02", work_center_name: "Torno", operation_count: 1 },
        { work_center: "012", work_center_name: "Banco", operation_count: 1 },
        { work_center: "CNC-01", work_center_name: "CNC", operation_count: 1 },
      ],
    });
    render(
      <LineFeederCollectModal
        open
        branch="01"
        onClose={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    const first = await screen.findByText(/012 · Banco/);
    const second = screen.getByText(/CNC-01 · CNC/);
    const third = screen.getByText(/TOR-02 · Torno/);
    expect(
      first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      second.compareDocumentPosition(third) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("bloqueia submit sem CT ou com horas inválidas", async () => {
    queueMock.mockResolvedValue({
      work_centers: [
        { work_center: "CT-A", work_center_name: "A", operation_count: 1 },
      ],
    });
    const onSubmit = vi.fn();
    render(
      <LineFeederCollectModal
        open
        branch="01"
        onClose={() => undefined}
        onSubmit={onSubmit}
      />,
    );
    await screen.findByText(/CT-A/);
    const submit = screen.getByRole("button", {
      name: "Consultar materiais",
    }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Horas de produção por posto"), {
      target: { value: "0" },
    });
    expect(submit.disabled).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("mostra estado sem programação publicada (404)", async () => {
    queueMock.mockRejectedValue(new HttpRequestError("missing", 404));
    render(
      <LineFeederCollectModal
        open
        branch="01"
        onClose={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText(/ainda não publicou uma fila/i),
      ).toBeTruthy(),
    );
  });
});
