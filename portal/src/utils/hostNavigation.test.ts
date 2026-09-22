import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  HOST_SELF_PROFILE_PATH,
  isHostShellPath,
} from "./hostNavigation.ts";
import { resolveSameAppSpaNavigation } from "./sameAppAnchorNavigation.ts";

describe("host shell navigation", () => {
  it("reconhece /profile como path do shell", () => {
    assert.equal(HOST_SELF_PROFILE_PATH, "/profile");
    assert.equal(isHostShellPath("/profile"), true);
    assert.equal(isHostShellPath("/apps/commercial/users/u1"), false);
  });

  it("interceptor SPA navega /profile a partir de um MFE", () => {
    const destination = resolveSameAppSpaNavigation(
      {
        defaultPrevented: false,
        button: 0,
        metaKey: false,
        ctrlKey: false,
        shiftKey: false,
        altKey: false,
      },
      {
        href: "https://minhadelpi.com.br/profile",
        target: "",
        hasAttribute: () => false,
        getAttribute: () => null,
      },
      {
        appBasePath: "/apps/transformometro",
        currentOrigin: "https://minhadelpi.com.br",
        currentPathname: "/apps/transformometro/interaction-rooms/r1",
        currentSearch: "",
        currentHash: "",
      },
    );
    assert.equal(destination, "/profile");
  });
});
