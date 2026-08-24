import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { UserAccessProfile } from "../../../data/userAccessProfileTypes.ts";
import {
  ORPHAN_APP_ID,
  ORPHAN_APP_NAME,
  buildGroupCentricTree,
  buildRoleCentricTree,
  buildUnifiedAccessTree,
  groupPermissionsByApp,
} from "./rbacAccessTree.ts";

const sampleProfile: UserAccessProfile = {
  isSuperadmin: false,
  effectivePermissions: [],
  effectiveApps: [],
  groups: [
    {
      id: "group-1",
      name: "DELPI - SC",
      description: "Matriz SC",
      roles: ["Almoxarife"],
    },
  ],
  roles: [
    {
      id: "role-direct",
      name: "Auditor 5S",
      description: null,
      sources: [{ type: "direct" }],
      permissions: [
        { code: "auditoria.view", name: "Ver auditoria", description: null, module: "auditoria" },
        { code: "legacy.access", name: "Legado", description: null, module: null },
      ],
      apps: [
        {
          id: "auditoria",
          name: "Auditoria 5S",
          basePath: "/apps/auditoria",
          icon: null,
          type: null,
          routes: [{ path: "/", label: "Home", permission: "auditoria.view", showInMenu: true }],
        },
      ],
    },
    {
      id: "role-group",
      name: "Almoxarife",
      description: null,
      sources: [{ type: "group", groupName: "DELPI - SC", groupId: "group-1" }],
      permissions: [
        { code: "supplies.view", name: "Ver suprimentos", description: null, module: "supplies" },
      ],
      apps: [
        {
          id: "supplies",
          name: "Suprimentos",
          basePath: "/apps/supplies",
          icon: null,
          type: null,
          routes: [{ path: "/", label: "Home", permission: "supplies.view", showInMenu: true }],
        },
      ],
    },
  ],
};

describe("groupPermissionsByApp", () => {
  it("agrupa permissões sob apps e isola órfãs", () => {
    const apps = groupPermissionsByApp(sampleProfile.roles[0]);
    assert.equal(apps.length, 2);
    assert.equal(apps[0].appName, "Auditoria 5S");
    assert.equal(apps[0].permissions[0].code, "auditoria.view");
    assert.equal(apps[1].appId, ORPHAN_APP_ID);
    assert.equal(apps[1].appName, ORPHAN_APP_NAME);
    assert.equal(apps[1].permissions[0].code, "legacy.access");
  });
});

describe("buildUnifiedAccessTree", () => {
  it("combina papéis diretos e ramos de grupo", () => {
    const tree = buildUnifiedAccessTree(sampleProfile);
    assert.equal(tree.branches.length, 2);
    assert.equal(tree.branches[0].kind, "directRole");
    assert.equal(tree.branches[1].kind, "groupBranch");
    assert.equal(tree.branches[1].group.roles[0].roleName, "Almoxarife");
  });
});

describe("buildRoleCentricTree", () => {
  it("lista todos os papéis efetivos com badges de origem", () => {
    const tree = buildRoleCentricTree(sampleProfile);
    assert.equal(tree.roles.length, 2);
    assert.deepEqual(tree.roles[0].sourceLabels, ["Direto"]);
    assert.deepEqual(tree.roles[1].sourceLabels, ["Via DELPI - SC"]);
  });
});

describe("buildGroupCentricTree", () => {
  it("mostra só grupos vinculados e papéis herdados", () => {
    const tree = buildGroupCentricTree(sampleProfile);
    assert.equal(tree.groups.length, 1);
    assert.equal(tree.groups[0].groupName, "DELPI - SC");
    assert.equal(tree.groups[0].roles.length, 1);
    assert.equal(tree.groups[0].roles[0].apps[0].appName, "Suprimentos");
  });
});
