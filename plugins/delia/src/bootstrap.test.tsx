import { afterEach, describe, expect, it, vi } from "vitest";

const render = vi.fn();
const unmountRoot = vi.fn();

vi.mock("../../vite/federationShareScope", () => ({
  preparePluginUiRemote: vi.fn().mockResolvedValue(undefined),
  getReactDomClient: vi.fn().mockResolvedValue({
    createRoot: () => ({
      render,
      unmount: unmountRoot,
    }),
  }),
}));

import { mount, unmount, updateRoute } from "./bootstrap";

afterEach(() => {
  render.mockClear();
  unmountRoot.mockClear();
  document.body.innerHTML = "";
});

describe("bootstrap mount/unmount", () => {
  it("exports Portal-compatible lifecycle API", async () => {
    const mod = await import("./bootstrap");
    expect(typeof mod.mount).toBe("function");
    expect(typeof mod.unmount).toBe("function");
    expect(typeof mod.updateRoute).toBe("function");
  });

  it("mounts into the supplied container and unmounts the React root", () => {
    const el = document.createElement("div");
    document.body.appendChild(el);

    mount(el, {
      pathname: "/apps/delia",
      permissions: ["fake.frontend.permission"],
      isSuperadmin: true,
      getAccessToken: () => "must-not-persist",
    });

    expect(render).toHaveBeenCalledTimes(1);
    const element = render.mock.calls[0][0];
    expect(element?.props?.pathname).toBe("/apps/delia");
    expect(element?.props?.permissions).toEqual(["fake.frontend.permission"]);

    unmount(el);
    expect(unmountRoot).toHaveBeenCalledTimes(1);
  });

  it("updateRoute reuses the same root", () => {
    const el = document.createElement("div");
    document.body.appendChild(el);

    mount(el, { pathname: "/apps/delia" });
    updateRoute(el, { pathname: "/apps/delia/workspace", routeLabel: "Workspace" });

    expect(render).toHaveBeenCalledTimes(2);
    expect(render.mock.calls[1][0]?.props?.routeLabel).toBe("Workspace");

    unmount(el);
    expect(unmountRoot).toHaveBeenCalledTimes(1);
  });
});
