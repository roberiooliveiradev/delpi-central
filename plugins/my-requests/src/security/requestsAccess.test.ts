import { describe, expect, it } from "vitest";

import {
  buildAccessFromPermissions,
  canAccessWorkQueue,
  canCreateAnyRequest,
  canCreateRequestType,
  canProcessAnyRequest,
} from "./requestsAccess";

describe("buildAccessFromPermissions", () => {
  it("marca canManage com my-requests.manage", () => {
    const access = buildAccessFromPermissions(["my-requests.access", "my-requests.manage"]);
    expect(access.canManage).toBe(true);
    expect(canProcessAnyRequest(access)).toBe(true);
    expect(canAccessWorkQueue(access)).toBe(true);
  });

  it("sem manage não libera admin nem fila só com create", () => {
    const access = buildAccessFromPermissions([
      "my-requests.access",
      "my-requests.invoice-issuance.create",
    ]);
    expect(access.canManage).toBe(false);
    expect(canProcessAnyRequest(access)).toBe(false);
    expect(canAccessWorkQueue(access)).toBe(false);
    expect(canCreateAnyRequest(access)).toBe(true);
  });
});

describe("canAccessWorkQueue", () => {
  it("nega quem só tem access", () => {
    const access = buildAccessFromPermissions(["my-requests.access"]);
    expect(canAccessWorkQueue(access)).toBe(false);
  });

  it("libera com process de um tipo", () => {
    const access = buildAccessFromPermissions([
      "my-requests.access",
      "my-requests.invoice-issuance.process",
    ]);
    expect(canAccessWorkQueue(access)).toBe(true);
  });

  it("libera com view-all sem process", () => {
    const access = buildAccessFromPermissions([
      "my-requests.access",
      "my-requests.view-all",
    ]);
    expect(canAccessWorkQueue(access)).toBe(true);
  });
});

describe("canCreateRequestType", () => {
  it("filtra tipo sem create correspondente", () => {
    const access = buildAccessFromPermissions([
      "my-requests.access",
      "my-requests.invoice-issuance.create",
    ]);
    expect(
      canCreateRequestType(access, "my-requests.invoice-issuance", "invoice-issuance"),
    ).toBe(true);
    expect(
      canCreateRequestType(
        access,
        "my-requests.raw-material-creation",
        "raw-material-creation",
      ),
    ).toBe(false);
  });

  it("manage cria qualquer tipo", () => {
    const access = buildAccessFromPermissions(["my-requests.access", "my-requests.manage"]);
    expect(canCreateRequestType(access, "my-requests.raw-material-creation")).toBe(true);
  });

  it("usa typeCode quando prefix ausente", () => {
    const access = buildAccessFromPermissions([
      "my-requests.access",
      "my-requests.raw-material-creation.create",
    ]);
    expect(canCreateRequestType(access, null, "raw-material-creation")).toBe(true);
  });
});
