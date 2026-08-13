import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildHrefWithReturn,
  parseReturnNavFromSearch,
  resolvePagePathBack,
  sanitizeReturnLabel,
  sanitizeReturnTo,
} from "./commercialNavigationReturn.ts";


const BASE = "/apps/commercial";

describe("commercialNavigationReturn", () => {
  it("sanitizeReturnTo aceita path sob o plugin", () => {
    assert.equal(
      sanitizeReturnTo("/apps/commercial/customers/1/01?secao=pedidos", BASE),
      "/apps/commercial/customers/1/01?secao=pedidos",
    );
    assert.equal(
      sanitizeReturnTo("customers/1/01?secao=pedidos", BASE),
      "/apps/commercial/customers/1/01?secao=pedidos",
    );
  });

  it("sanitizeReturnTo rejeita open-redirect e fora do prefixo", () => {
    assert.equal(sanitizeReturnTo("https://evil.example/", BASE), null);
    assert.equal(sanitizeReturnTo("//evil.example/", BASE), null);
    assert.equal(sanitizeReturnTo("/apps/other/x", BASE), null);
    assert.equal(sanitizeReturnTo("javascript:alert(1)", BASE), null);
    assert.equal(sanitizeReturnTo("", BASE), null);
  });

  it("sanitizeReturnLabel limita e limpa", () => {
    assert.equal(sanitizeReturnLabel("  Conta · Pedidos  "), "Conta · Pedidos");
    assert.equal(sanitizeReturnLabel(""), null);
    assert.equal(sanitizeReturnLabel("x".repeat(100))?.length, 80);
  });

  it("resolvePagePathBack usa returnTo ou fallback", () => {
    const fallback = { href: "/apps/commercial/proposals", label: "Propostas" };
    assert.deepEqual(
      resolvePagePathBack(
        "?returnTo=%2Fapps%2Fcommercial%2Fanalytics%2Fopportunities%2F003578&returnLabel=OV%20003578",
        fallback,
        BASE,
      ),
      {
        href: "/apps/commercial/analytics/opportunities/003578",
        label: "OV 003578",
      },
    );
    assert.deepEqual(resolvePagePathBack("", fallback, BASE), fallback);
  });

  it("buildHrefWithReturn anexa params sem quebrar query", () => {
    const href = buildHrefWithReturn(
      "/apps/commercial/proposals/005015?tab=pdf",
      {
        returnTo: "/apps/commercial/analytics/opportunities/003558",
        returnLabel: "OV 003558",
      },
      BASE,
    );
    const url = new URL(href, "https://example.test");
    assert.equal(url.pathname, "/apps/commercial/proposals/005015");
    assert.equal(url.searchParams.get("tab"), "pdf");
    assert.equal(
      url.searchParams.get("returnTo"),
      "/apps/commercial/analytics/opportunities/003558",
    );
    assert.equal(url.searchParams.get("returnLabel"), "OV 003558");
  });

  it("parseReturnNavFromSearch lê params", () => {
    const parsed = parseReturnNavFromSearch(
      "returnTo=/apps/commercial/my-tasks&returnLabel=Minhas%20tarefas",
      BASE,
    );
    assert.equal(parsed.returnTo, "/apps/commercial/my-tasks");
    assert.equal(parsed.returnLabel, "Minhas tarefas");
  });
});
