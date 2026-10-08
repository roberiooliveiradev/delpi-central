// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { PcpOperatorFeedback } from "../types";
import { OperatorFeedbackInbox } from "./OperatorFeedbackInbox";

vi.mock("./PpcConfirmModal", () => ({
  HostContainedDialog: ({
    open,
    title,
    children,
  }: {
    open: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
  }) =>
    open ? (
      <div>
        <h2>{title}</h2>
        {children}
      </div>
    ) : null,
  HostContainedWideDialog: ({
    open,
    title,
    children,
  }: {
    open: boolean;
    title: string;
    children: ReactNode;
    onClose: () => void;
  }) =>
    open ? (
      <div>
        <h2>{title}</h2>
        {children}
      </div>
    ) : null,
}));

function makeFeedback(
  partial: Partial<PcpOperatorFeedback> = {},
): PcpOperatorFeedback {
  return {
    id: "fb-1",
    branch: "01",
    productionOrder: "24640401002",
    operationCode: "03",
    reportedWorkCenter: "CT-63",
    feedbackType: "cannot_produce",
    reasonCode: "missing_material",
    note: "Falta terminal na bancada",
    status: "open",
    operatorCode: "001234",
    operatorName: "Maria Silva",
    productCode: "TR-1",
    productDescription: null,
    paProductCode: "PA-9",
    dueDate: "2026-10-08",
    createdAt: "2026-10-01T08:00:00Z",
    acknowledgedAt: null,
    acknowledgedBy: null,
    ...partial,
  };
}

const WITH_MATERIALS = makeFeedback({
  materials: [
    {
      id: "m-1",
      productCode: "10081234",
      description: "TERMINAL FASTON",
      unit: "PC",
      openQty: 120,
      status: "picked",
      pickedAt: "2026-10-01T09:00:00Z",
      deliveredAt: null,
    },
    {
      id: "m-2",
      productCode: "10085678",
      description: "FIO RIGIDO",
      unit: "MT",
      openQty: 40,
      status: "delivered",
      pickedAt: "2026-10-01T09:00:00Z",
      deliveredAt: "2026-10-01T09:30:00Z",
    },
  ],
});

function renderInbox(items: PcpOperatorFeedback[]) {
  return render(
    <OperatorFeedbackInbox
      open
      items={items}
      summary={{
        total: items.length,
        open: items.filter((i) => i.status === "open").length,
        acknowledged: items.filter((i) => i.status === "acknowledged").length,
      }}
      loading={false}
      error={null}
      notice={null}
      actingId={null}
      findInQueue={() => null}
      onAcknowledge={() => Promise.resolve(true)}
      onResolve={() => Promise.resolve(true)}
      onGoToQueue={() => undefined}
      onClose={() => undefined}
    />,
  );
}

afterEach(() => cleanup());

describe("OperatorFeedbackInbox — materiais (C5)", () => {
  it("exibe os materiais informados com status do Alimentador", () => {
    renderInbox([WITH_MATERIALS]);

    expect(screen.getByText("Materiais informados")).toBeTruthy();
    expect(screen.getByText("10081234")).toBeTruthy();
    expect(screen.getByText(/TERMINAL FASTON/)).toBeTruthy();
    expect(screen.getByText("10085678")).toBeTruthy();
    expect(screen.getByText("Em separação")).toBeTruthy();
    expect(screen.getByText("Entregue")).toBeTruthy();
  });

  it("feedback legado sem materiais não quebra", () => {
    renderInbox([makeFeedback()]);
    expect(screen.queryByText("Materiais informados")).toBeNull();
    expect(screen.getByText("24640401002")).toBeTruthy();
  });

  it("avisa ao resolver com material ainda não entregue", () => {
    renderInbox([WITH_MATERIALS]);
    fireEvent.click(screen.getByRole("button", { name: "Resolver" }));
    expect(
      screen.getByText("Ainda existem materiais não marcados como entregues."),
    ).toBeTruthy();
  });

  it("material entregue não remove o feedback e não mostra warning", () => {
    const allDelivered = makeFeedback({
      status: "acknowledged",
      materials: [
        {
          id: "m-1",
          productCode: "10081234",
          description: "TERMINAL FASTON",
          unit: "PC",
          openQty: 120,
          status: "delivered",
          pickedAt: "2026-10-01T09:00:00Z",
          deliveredAt: "2026-10-01T09:30:00Z",
        },
      ],
    });
    renderInbox([allDelivered]);
    // continua na inbox — delivered não resolve o impedimento
    expect(screen.getByText("24640401002")).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: "Marcar como resolvido" }),
    );
    expect(
      screen.queryByText("Ainda existem materiais não marcados como entregues."),
    ).toBeNull();
  });
});
