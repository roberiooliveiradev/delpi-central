#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildWhatsAppGreeting, buildWhatsAppUrl } from "./whatsapp.ts";

describe("whatsapp helpers", () => {
  it("substitui {full_name} na saudação", () => {
    const text = buildWhatsAppGreeting("Ana Silva");
    assert.match(text, /Ana Silva/);
    assert.doesNotMatch(text, /\{full_name\}/);
  });

  it("monta wa.me com dígitos e texto encoded", () => {
    const url = buildWhatsAppUrl("+55 47 99999-1234", "Olá, Ana!");
    assert.equal(
      url,
      `https://wa.me/5547999991234?text=${encodeURIComponent("Olá, Ana!")}`,
    );
  });
});
