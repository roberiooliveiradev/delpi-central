/**
 * Contratos de fluxo admin cobertos por asserts de parse/permissão
 * (sem RTL — infraestrutura de componentes não configurada neste plugin).
 */
import assert from "node:assert/strict";
import test from "node:test";

import { hasManagePermission } from "../src/utils/permissions.ts";
import {
  GUIAS_PROCEDIMENTOS_ROUTES,
  parseGuiasProcedimentosPath,
} from "../src/utils/route.ts";

test("usuário sem manage não seria autorizado (gate)", () => {
  const canManage = hasManagePermission({
    id: "1",
    name: "ops",
    email: "ops@x",
    permissions: ["guias-procedimentos.access"],
  });
  assert.equal(canManage, false);
});

test("usuário com manage autoriza admin", () => {
  assert.equal(
    hasManagePermission({
      id: "1",
      name: "admin",
      email: "a@x",
      permissions: ["guias-procedimentos.manage"],
    }),
    true,
  );
});

test("rota admin declarada e parseável", () => {
  assert.equal(
    GUIAS_PROCEDIMENTOS_ROUTES.admin,
    "/apps/guias-procedimentos/admin",
  );
  assert.equal(
    parseGuiasProcedimentosPath(GUIAS_PROCEDIMENTOS_ROUTES.admin).view,
    "admin-home",
  );
  assert.equal(
    parseGuiasProcedimentosPath(
      GUIAS_PROCEDIMENTOS_ROUTES.adminDepartmentEdit("abc"),
    ).view,
    "admin-department-edit",
  );
  assert.equal(
    parseGuiasProcedimentosPath(
      GUIAS_PROCEDIMENTOS_ROUTES.adminProcedureEdit("xyz"),
    ).id,
    "xyz",
  );
});
