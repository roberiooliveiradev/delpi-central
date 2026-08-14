import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));

describe("OrgMembershipFlow fitView", () => {
  it("aguarda nodesInitialized antes do fitView", () => {
    const source = readFileSync(join(root, "OrgMembershipFlow.tsx"), "utf8");
    expect(source).toMatch(/useNodesInitialized/);
    expect(source).toMatch(/if \(!nodesInitialized\) return/);
    expect(source).toMatch(/FitViewOnChange/);
  });

  it("nós de pessoa usam InitialsAvatar com avatarSrc", () => {
    const source = readFileSync(join(root, "OrgMembershipFlow.tsx"), "utf8");
    expect(source).toMatch(/InitialsAvatar/);
    expect(source).toMatch(/src=\{data\.avatarSrc\}/);
    expect(source).toMatch(/node-icon--avatar/);
  });
});
