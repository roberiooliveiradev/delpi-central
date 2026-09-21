import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  createFederatedMountSession,
  updateFederatedRemote,
  type FederatedHostProps,
  type FederatedRemoteModule,
} from "./federatedRemoteHost.ts";
import { DELIA_EXPOSED_MODULE } from "./globalDeliaDock.ts";

const DELIA_ENTRY = "/apps/delia/assets/remoteEntry.js";

function hostProps(pathname = "/apps/helpdesk", search = ""): FederatedHostProps {
  return {
    getAccessToken: () => undefined,
    basePath: "/apps/delia",
    pathname,
    search,
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

  it("atualiza pathname/search sem segundo mount", async () => {
    let mounts = 0;
    const updates: string[] = [];
    const session = createFederatedMountSession({
      async loadModule() {
        return {
          mount() {
            mounts += 1;
          },
          updateRoute(_el, props) {
            updates.push(`${props.pathname}${props.search}`);
          },
          unmount() {},
        };
      },
    });
    const el = { innerHTML: "", dataset: {} } as unknown as HTMLElement;
    await session.mount(
      el,
      DELIA_ENTRY,
      hostProps("/apps/my-requests", "?tab=open"),
      DELIA_EXPOSED_MODULE,
    );
    session.updateRoute(hostProps("/apps/commercial", "?view=board"));
    assert.equal(mounts, 1);
    assert.equal(session.isMounted(), true);
    assert.deepEqual(updates, ["/apps/commercial?view=board"]);
  });
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe("async stale mount", () => {
  it("descarta o load que resolve depois do unmount", async () => {
    const gate = deferred<FederatedRemoteModule>();
    let mountCalls = 0;
    let unmountCalls = 0;
    const mod: FederatedRemoteModule = {
      mount() {
        mountCalls += 1;
      },
      unmount() {
        unmountCalls += 1;
      },
    };
    const session = createFederatedMountSession({
      loadModule: () => gate.promise,
    });
    const el = { innerHTML: "", dataset: {} } as unknown as HTMLElement;
    const pending = session.mount(el, DELIA_ENTRY, hostProps(), DELIA_EXPOSED_MODULE);

    session.unmount();
    gate.resolve(mod);
    await pending;

    assert.equal(mountCalls, 0);
    assert.equal(unmountCalls, 0);
    assert.equal(session.isMounted(), false);
    assert.equal(session.entryUrl(), null);
    assert.equal(session.exposedModule(), null);
  });

  it("mantém o mount mais novo quando o load antigo resolve depois", async () => {
    const gateA = deferred<FederatedRemoteModule>();
    const gateB = deferred<FederatedRemoteModule>();
    const gates = [gateA, gateB];
    let index = 0;
    const calls: string[] = [];
    const modA: FederatedRemoteModule = {
      mount() {
        calls.push("A");
      },
      unmount() {
        calls.push("unmountA");
      },
    };
    const modB: FederatedRemoteModule = {
      mount() {
        calls.push("B");
      },
      unmount() {
        calls.push("unmountB");
      },
    };
    const session = createFederatedMountSession({
      loadModule: () => gates[index++].promise,
    });
    const el = { innerHTML: "", dataset: {} } as unknown as HTMLElement;
    const pendingA = session.mount(el, "/apps/delia/assets/remoteEntry.js", hostProps("/a"), DELIA_EXPOSED_MODULE);
    const pendingB = session.mount(el, "/apps/delia/assets/remoteEntry.js", hostProps("/b"), DELIA_EXPOSED_MODULE);

    gateB.resolve(modB);
    await pendingB;
    gateA.resolve(modA);
    await pendingA;

    assert.deepEqual(calls, ["B"]);
    assert.equal(session.isMounted(), true);
    assert.equal(session.entryUrl(), "/apps/delia/assets/remoteEntry.js");
    assert.equal(session.exposedModule(), DELIA_EXPOSED_MODULE);
  });
});
