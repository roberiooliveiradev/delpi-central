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
    function StateBox({
      children,
      variant,
    }: {
      children: ReactNode;
      variant?: string;
    }) {
      return <div role="alert" data-variant={variant}>{children}</div>;
    },
}));

vi.mock("../../hooks/usePermissions", () => ({
  usePermissions: () => ({
    profile: {
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.guidance.manage",
        "planejamento-orcamentario.admin",
      ],
    },
    loading: false,
    error: null,
  }),
}));

import { AdminGuidancePage } from "./AdminGuidancePage";
import * as budgetApi from "../../api/budgetPlanningApi";

vi.mock("../../api/budgetPlanningApi");

const draft = {
  id: "g-draft",
  status: "draft",
  version_number: null,
  title: "Carta",
  board_message: "Msg",
  objective: "",
  general_guidance: "",
  premises: [],
  schedule: [],
};

beforeEach(() => {
  vi.mocked(budgetApi.listAdminExercises).mockResolvedValue([
    {
      id: "ex1",
      year: 2027,
      name: "PO 2027",
      status: "open",
      is_active: true,
    },
  ]);
  vi.mocked(budgetApi.fetchAdminGuidance).mockResolvedValue({
    draft: draft as never,
    published_versions: [],
  });
  vi.mocked(budgetApi.listAdminGuidanceDocuments).mockResolvedValue([]);
  vi.mocked(budgetApi.uploadAdminGuidanceDocument).mockResolvedValue({
    id: "d1",
    display_name: "Manual",
    original_name: "manual.pdf",
    mime_type: "application/pdf",
    size_bytes: 3,
    document_kind: "pdf",
    status: "active",
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("AdminGuidancePage documentos", () => {
  it("valida extensão inválida e impede upload", async () => {
    render(<AdminGuidancePage />);
    await screen.findByText("Documentos de apoio");
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const bad = new File([new Uint8Array([1])], "x.exe", { type: "application/octet-stream" });
    fireEvent.change(input, { target: { files: [bad] } });
    await screen.findByText(/Extensão/i);
    expect(budgetApi.uploadAdminGuidanceDocument).not.toHaveBeenCalled();
  });

  it("envia multipart válido com progresso e lista o documento", async () => {
    vi.mocked(budgetApi.listAdminGuidanceDocuments)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          id: "d1",
          display_name: "Manual",
          original_name: "manual.pdf",
          mime_type: "application/pdf",
          size_bytes: 3,
          document_kind: "pdf",
          status: "active",
        },
      ]);
    render(<AdminGuidancePage />);
    await screen.findByText("Documentos de apoio");
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File([new Uint8Array([1, 2, 3])], "manual.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText("Nome de exibição"), {
      target: { value: "Manual" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Enviar documento" }));
    await waitFor(() => {
      expect(budgetApi.uploadAdminGuidanceDocument).toHaveBeenCalledWith(
        expect.objectContaining({
          exerciseId: "ex1",
          guidanceId: "g-draft",
          displayName: "Manual",
          file,
        }),
        expect.objectContaining({ onProgress: expect.any(Function) }),
      );
    });
    await screen.findByText("Documento enviado com sucesso.");
    await screen.findByText("Manual");
  });
});
