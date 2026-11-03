// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MachineLoadHorizonModal } from "./MachineLoadHorizonModal";
import type { MachineLoadHorizonPreview } from "../types";

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

const preview: MachineLoadHorizonPreview = {
  branch: "01",
  work_center: "CT-A",
  generation_id: "gen-1",
  base_end_date: "2026-09-02",
  requested_end_date: "2026-09-16",
  additional_start_date: "2026-09-03",
  additional_end_date: "2026-09-16",
  horizon_days: 28,
  preset_days: [21, 28, 42],
  max_horizon_days_from_today: 90,
  existing_operation_count: 2,
  new_operation_count: 3,
  requires_publish: true,
  message: "ok",
};

function renderModal(
  props: Partial<Parameters<typeof MachineLoadHorizonModal>[0]> = {},
) {
  const onClose = vi.fn();
  const onPreview = vi.fn();
  const onConfirm = vi.fn();
  const utils = render(
    <MachineLoadHorizonModal
      open
      workCenter="CT-A"
      workCenterName="CORTE"
      baseEndDate="2026-09-02"
      publicationState="draft"
      preview={null}
      onClose={onClose}
      onPreview={onPreview}
      onConfirm={onConfirm}
      {...props}
    />,
  );
  return { onClose, onPreview, onConfirm, ...utils };
}

afterEach(cleanup);

describe("MachineLoadHorizonModal", () => {
  it("mostra CT e bloqueia confirmação sem prévia", () => {
    renderModal();
    expect(screen.getByText(/Ampliar horizonte do centro/)).toBeTruthy();
    expect(screen.getByText(/CT-A — CORTE/)).toBeTruthy();
    expect(
      (screen.getByRole("button", { name: /Incluir na preparação/ }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("LIVE bloqueia ampliação e orienta Atualizar", () => {
    renderModal({ publicationState: "live" });
    expect(screen.getByText(/Execute «Atualizar»/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Calcular prévia/ })).toBeNull();
  });

  it("com prévia habilita confirmação", () => {
    const { onConfirm } = renderModal({ preview });
    const confirm = screen.getByRole("button", {
      name: /Incluir na preparação/,
    }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(false);
    fireEvent.click(confirm);
    expect(onConfirm).toHaveBeenCalled();
  });
});
