import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  createFederatedMountSession,
  updateFederatedRemote,
  type FederatedHostProps,
  type FederatedRemoteModule,
} from "./federatedRemoteHost.ts";
import { DELIA_EXPOSED_MODULE } from "./globalDeliaSurface.ts";

const DELIA_ENTRY = "/apps/delia/assets/remoteEntry.js";

function hostProps(pathname = "/apps/helpdesk"): FederatedHostProps {
  return {
    getAccessToken: () => undefined,
    basePath: "/apps/delia",
    pathname,
    search: "",
    appRoutes: [{ path: "/apps/delia", entry: null, openInNewTab: false }],
  };
}

describe("federated mount lifecycle", () => {
  it("abre o mesmo remote ./App e desmonta ao fechar", async () => {
    const calls: string[] = [];
    const fakeModule: FederatedRemoteModule = {
      mount(el, props) {
        calls.push(`mount:${props.pathname}`);
        el.dataset.mounted = "1";
      },
      updateRoute(_el, props) {
        calls.push(`update:${props.pathname}`);
      },
      unmount() {
        calls.push("unmount");
      },
    };

    const session = createFederatedMountSession({
      loadModule: async (entryUrl, exposed) => {
        assert.equal(entryUrl, DELIA_ENTRY);
        assert.equal(exposed, DELIA_EXPOSED_MODULE);
        return fakeModule;
      },
    });

    const el = { innerHTML: "", dataset: {} } as unknown as HTMLElement;
    await session.mount(el, DELIA_ENTRY, hostProps(), DELIA_EXPOSED_MODULE);
    assert.equal(session.isMounted(), true);
    assert.equal(session.entryUrl(), DELIA_ENTRY);
    assert.equal(session.exposedModule(), DELIA_EXPOSED_MODULE);

    session.unmount();
    assert.equal(session.isMounted(), false);
    assert.deepEqual(calls, ["mount:/apps/helpdesk", "unmount"]);
  });

  it("reabre com mount limpo e propaga updateRoute", async () => {
    const calls: string[] = [];
    let mounts = 0;
    const fakeModule: FederatedRemoteModule = {
      mount(_el, props) {
        mounts += 1;
        calls.push(`mount:${props.pathname}:${mounts}`);
      },
      updateRoute(_el, props) {
        calls.push(`update:${props.pathname}`);
      },
      unmount() {
        calls.push("unmount");
      },
    };

    const session = createFederatedMountSession({
      async loadModule() {
        return fakeModule;
      },
    });

    const el = { innerHTML: "stale", dataset: {} } as unknown as HTMLElement;
    await session.mount(el, DELIA_ENTRY, hostProps("/"), DELIA_EXPOSED_MODULE);
    session.updateRoute(hostProps("/apps/helpdesk"));
    session.unmount();
    await session.mount(el, DELIA_ENTRY, hostProps("/"), DELIA_EXPOSED_MODULE);

    assert.equal(mounts, 2);
    assert.deepEqual(calls, [
      "mount:/:1",
      "update:/apps/helpdesk",
      "unmount",
      "mount:/:2",
    ]);
  });

  it("faz fallback para mount quando updateRoute não existe", () => {
    const calls: string[] = [];
    const mod: FederatedRemoteModule = {
      mount(_el, props) {
        calls.push(`mount:${props.pathname}`);
      },
    };
    updateFederatedRemote(mod, {} as HTMLElement, hostProps("/profile"));
    assert.deepEqual(calls, ["mount:/profile"]);
  });
});
