import { describe, expect, it } from "vitest";

import {
  pickEmptyStateGreeting,
  pickEmptyStateHint,
} from "./chatEmptyStateGreeting";

describe("pickEmptyStateGreeting", () => {
  it("fala diretamente com o usuário quando há nome", () => {
    const greeting = pickEmptyStateGreeting("Roberto Silva");

    expect(greeting).toMatch(/^Olá, Roberto\.|^Oi, Roberto\.|^Ei, Roberto\./);
  });

  it("usa saudação genérica quando não há nome", () => {
    expect(pickEmptyStateGreeting(null)).toMatch(/Olá\.|O que vamos resolver|Pode perguntar/);
  });
});

describe("pickEmptyStateHint", () => {
  it("orienta o usuário sem repetir o catálogo de perfis", () => {
    expect(pickEmptyStateHint("Roberto Silva")).toContain("do seu jeito");
    expect(pickEmptyStateHint(null)).toContain("do seu jeito");
  });
});
