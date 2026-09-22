#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("PortalTopBarUserIdentity", () => {
  it("abre o perfil do Portal Transforma+ (/users/:id), não só /profile do host", () => {
    const identity = readFileSync(
      join(src, "components/PortalTopBarUserIdentity.tsx"),
      "utf8",
    );
    assert.match(identity, /buildTransformometroUserPath/);
    assert.match(identity, /navigateTransformometroUserProfile/);
    assert.doesNotMatch(identity, /HOST_SELF_PROFILE_PATH/);
    assert.match(identity, /fetchMeProfile/);
    assert.match(identity, /useMyPersonProfilePhotoUrl/);
    assert.doesNotMatch(identity, /display-only/);
  });

  it("TopBar expõe identity no slot actions", () => {
    const nav = readFileSync(join(src, "components/TransformometroNav.tsx"), "utf8");
    assert.match(nav, /PortalTopBarUserIdentity/);
    assert.match(nav, /actions=\{\s*<PortalTopBarUserIdentity/);
  });
});
