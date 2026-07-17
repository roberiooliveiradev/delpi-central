// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { MinuteDetail } from "../api/cipaApi";
import { MinuteDocumentView } from "./MinuteDocumentView";

vi.mock("../api/cipaApi", async (importOriginal) => {
  const original = await importOriginal<typeof import("../api/cipaApi")>();
  return { ...original, getSignatureImage: vi.fn() };
});

afterEach(cleanup);

const detail: MinuteDetail = {
  minute: {
    id: "m1",
    unit_code: "01",
    minute_number: "2026/001",
    meeting_type: "ordinary",
    meeting_date: "2026-07-16",
    start_time: "09:00",
    end_time: "10:00",
    location: "Sala CIPA",
    status: "draft",
  },
  version: {
    version_number: 1,
    body_html: "<p>Conteúdo formal da reunião.</p>",
    content_hash: "hash-1",
  },
  participants: [
    {
      user_id: "u1",
      display_name: "Ana CIPA",
      role_in_meeting: "president",
    },
  ],
  signers: [
    {
      id: "s1",
      user_id: "u1",
      display_name: "Ana CIPA",
      status: "pending",
    },
  ],
  signatures: [],
  action_items: [],
  versions: [],
};

describe("MinuteDocumentView", () => {
  it("renderiza leitura formal com participantes, conteúdo e assinaturas", () => {
    const { container } = render(
      <MinuteDocumentView detail={detail} toolbar={<button>Baixar PDF</button>} />,
    );

    expect(screen.getByLabelText("Modo de leitura da ata")).toBeTruthy();
    expect(screen.getByText("Ata de reunião da CIPA")).toBeTruthy();
    expect(screen.getAllByText(/Ana CIPA/).length).toBeGreaterThan(0);
    expect(screen.getByText("Conteúdo formal da reunião.")).toBeTruthy();
    expect(screen.getByText("Presidente da CIPA")).toBeTruthy();
    expect(screen.getByText("Baixar PDF")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-document-rich-content")).toBeTruthy();
    expect(screen.queryByText(/realizou-se reunião/)).toBeNull();
    expect(screen.queryByText(/DELPI Conexões Elétricas, 16 de julho/)).toBeNull();
  });
});
