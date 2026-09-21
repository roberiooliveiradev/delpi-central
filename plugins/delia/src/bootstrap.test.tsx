import { afterEach, describe, expect, it, vi } from "vitest";

const { render, unmountRoot, createRoot } = vi.hoisted(() => {
  const render = vi.fn();
  const unmountRoot = vi.fn();
  const createRoot = vi.fn(() => ({
    render,
    unmount: unmountRoot,
  }));
  return { render, unmountRoot, createRoot };
});

vi.mock("../../vite/federationShareScope", () => ({
  preparePluginUiRemote: vi.fn().mockResolvedValue(undefined),
  getReactDomClient: vi.fn().mockResolvedValue({
    createRoot,
  }),
}));

import { mount, unmount, updateRoute } from "./bootstrap";

afterEach(() => {
  render.mockClear();
  unmountRoot.mockClear();
  createRoot.mockClear();
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

  it("destroys the root on unmount and creates a fresh root on remount", () => {
    const el = document.createElement("div");
    document.body.appendChild(el);

    mount(el, { pathname: "/apps/delia", routeLabel: "User A" });
    unmount(el);
    mount(el, { pathname: "/apps/delia", routeLabel: "User B" });

    expect(createRoot).toHaveBeenCalledTimes(2);
    expect(unmountRoot).toHaveBeenCalledTimes(1);
    expect(render.mock.calls[1][0]?.props?.routeLabel).toBe("User B");

    unmount(el);
  });

  it("updateRoute refreshes host presentation without a second root", () => {
    const el = document.createElement("div");
    document.body.appendChild(el);

    mount(el, { pathname: "/apps/delia", search: "" });
    updateRoute(el, {
      pathname: "/apps/delia/panel",
      search: "?view=host",
      routeLabel: "Painel",
    });

    expect(createRoot).toHaveBeenCalledTimes(1);
    expect(render).toHaveBeenCalledTimes(2);
    expect(render.mock.calls[1][0]?.props?.pathname).toBe("/apps/delia/panel");
    expect(render.mock.calls[1][0]?.props?.search).toBe("?view=host");
    expect(render.mock.calls[1][0]?.props?.routeLabel).toBe("Painel");

    unmount(el);
  });
});
