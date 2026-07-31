import { describe, expect, it } from "vitest";

import { shouldRequestDataRouteSuggestions } from "./shouldRequestDataRouteSuggestions";

describe("shouldRequestDataRouteSuggestions", () => {
  it("ignora vazio e texto curto", () => {
    expect(shouldRequestDataRouteSuggestions("")).toBe(false);
    expect(shouldRequestDataRouteSuggestions("oee")).toBe(false);
    expect(shouldRequestDataRouteSuggestions("estoque")).toBe(false);
    expect(shouldRequestDataRouteSuggestions("dois termos")).toBe(false);
  });

  it("aceita frase com 3+ tokens ou 16+ chars", () => {
    expect(shouldRequestDataRouteSuggestions("oee da semana")).toBe(true);
    expect(shouldRequestDataRouteSuggestions("eficiencia fabril")).toBe(true);
  });
});
