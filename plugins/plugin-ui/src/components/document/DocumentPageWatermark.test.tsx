// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DocumentPage, DocumentReader } from "./DocumentReader";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  document.body.innerHTML = "";
});

describe("DocumentPageWatermark", () => {
  it("renderiza tiles A4 da marca d'água na prévia", () => {
    render(
      <DocumentReader>
        <DocumentPage watermark={<img src="/wm.png" alt="" />}>
          <p>Corpo</p>
        </DocumentPage>
      </DocumentReader>,
    );

    const root = document.querySelector("[data-delpi-document-watermark]");
    expect(root).toBeTruthy();
    expect(root!.querySelectorAll("[data-delpi-document-watermark-tile]").length).toBeGreaterThanOrEqual(
      1,
    );
    expect(screen.getByText("Corpo")).toBeTruthy();
  });
});
