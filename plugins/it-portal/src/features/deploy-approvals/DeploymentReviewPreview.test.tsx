import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DeploymentReviewPreview,
  type DeploymentReviewSummary,
} from "./DeploymentReviewPreview";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const valid: DeploymentReviewSummary = {
  proposalId: "01234567-89ab-4def-8abc-0123456789ab",
  requesterLabel: "Solicitante de teste",
  environment: "prod",
  serviceId: "public-hub",
  status: "pending_approval",
  targetCommitSha: "f81ddd0075de1e4ef8bb68ca58791e9c43e70759",
  manifestDigest: "sha256:" + "a".repeat(64),
  previousImageId: "sha256:" + "b".repeat(64),
  targetImageId: "sha256:" + "c".repeat(64),
  bindingSha256: "d".repeat(64),
  expiresAt: "2026-11-16T17:00:00Z",
};

describe("ATLAS deployment approval preview is deliberately inert", () => {
  it("shows full immutable OCI identifiers and manual deploy independence", () => {
    render(<DeploymentReviewPreview proposal={valid} />);
    expect(screen.getByRole("heading", { name: "Revisão de implantação" })).toBeTruthy();
    expect(screen.getByText(valid.targetCommitSha)).toBeTruthy();
    expect(screen.getByText(valid.manifestDigest)).toBeTruthy();
    expect(screen.getByText(valid.previousImageId)).toBeTruthy();
    expect(screen.getByText(valid.targetImageId)).toBeTruthy();
    expect(screen.getByText(valid.bindingSha256)).toBeTruthy();
    expect(screen.getByText(/deploys manuais pelo terminal continuam independentes/i)).toBeTruthy();
    const reject = screen.getByRole("button", { name: "Rejeitar" }) as HTMLButtonElement;
    const approve = screen.getByRole("button", { name: "Aprovar atualização" }) as HTMLButtonElement;
    expect(reject.disabled).toBe(true);
    expect(approve.disabled).toBe(true);
  });

  it("renders a safe empty state without data", () => {
    render(<DeploymentReviewPreview proposal={null} />);
    expect(screen.getByText(/nenhuma solicitação pronta/i)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Aprovar atualização" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("does not display malformed or mismatched OCI image identities", () => {
    const invalid = { ...valid, targetImageId: valid.previousImageId };
    render(<DeploymentReviewPreview proposal={invalid} />);
    expect(screen.getByText(/nenhuma solicitação pronta/i)).toBeTruthy();
    expect(screen.queryByText(valid.manifestDigest)).toBeNull();
  });

  it("never calls the network or attempts approval", () => {
    const mockFetch = vi.fn();
    vi.stubGlobal("fetch", mockFetch);
    render(<DeploymentReviewPreview proposal={valid} />);
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("distinguishes homologation from production without granting actions", () => {
    render(<DeploymentReviewPreview proposal={{ ...valid, environment: "hml" }} />);
    expect(screen.getByText("Homologação")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Aprovar atualização" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
