import assert from "node:assert/strict";
import { resolveReportsPermissions } from "./reportsPermissions.ts";

function check(
  label: string,
  input: Parameters<typeof resolveReportsPermissions>[0],
  expected: ReturnType<typeof resolveReportsPermissions>,
) {
  const actual = resolveReportsPermissions(input);
  assert.deepEqual(actual, expected, label);
}

check("superadmin vê tudo", { isSuperadmin: true }, {
  canUseAdminNav: true,
  canUseFollowUpNav: true,
});

check(
  "só notes.manage → apenas acompanhamentos",
  { permissions: ["reports.notes.manage", "reports.view.filial-sc"] },
  { canUseAdminNav: false, canUseFollowUpNav: true },
);

check(
  "reports.view → admin + acompanhamentos",
  { permissions: ["reports.view"] },
  { canUseAdminNav: true, canUseFollowUpNav: true },
);

check(
  "reports.manage → admin + acompanhamentos",
  { permissions: ["reports.manage"] },
  { canUseAdminNav: true, canUseFollowUpNav: true },
);

check(
  "só filial sem view/notes → nenhuma aba",
  { permissions: ["reports.view.filial-es"] },
  { canUseAdminNav: false, canUseFollowUpNav: false },
);

check(
  "hasPermission do host",
  {
    hasPermission: (code) => code === "reports.notes.manage",
  },
  { canUseAdminNav: false, canUseFollowUpNav: true },
);

console.log("reportsPermissions: ok");
