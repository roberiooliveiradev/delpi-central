import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ImageLightboxModal } from "./ImageLightboxModal";

afterEach(() => {
  cleanup();
});

describe("ImageLightboxModal", () => {
  it("mostra a imagem ampliada no dialog host-contained", () => {
    const host = document.createElement("main");
    host.className = "dashboard-commercial";
    document.body.appendChild(host);
    const mount = document.createElement("div");
    host.appendChild(mount);

    render(
      <ImageLightboxModal
        open
        src="blob:photo"
        title="Maria Silva"
        onClose={vi.fn()}
        portalScopeClassName="dashboard-commercial"
      />,
      { container: mount },
    );

    const dialog = screen.getByRole("dialog", { name: "Maria Silva" });
    expect(host.contains(dialog)).toBe(true);
    expect(screen.getByRole("img", { name: "Maria Silva" }).getAttribute("src")).toBe(
      "blob:photo",
    );

    host.remove();
  });
});
