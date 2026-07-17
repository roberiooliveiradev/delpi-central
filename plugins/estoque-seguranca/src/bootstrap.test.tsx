import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("../../vite/federationShareScope", () => ({
  preparePluginUiRemote: vi.fn().mockResolvedValue(undefined),
  getReactDomClient: vi.fn().mockResolvedValue({
    createRoot: () => ({
      render: vi.fn(),
      unmount: vi.fn(),
    }),
  }),
}));

import { mount, unmount } from "./bootstrap";

afterEach(() => {
  const root = document.getElementById("test-root");
  if (root) {
    unmount(root);
    root.remove();
  }
});

describe("bootstrap", () => {
  it("monta e desmonta sem lançar erro", async () => {
    const el = document.createElement("div");
    el.id = "test-root";
    document.body.appendChild(el);

    mount(el, { getAccessToken: () => "token" });
    unmount(el);

    expect(el.childNodes.length).toBe(0);
  });
});
