import { describe, expect, it } from "vitest";

import { shouldRequestDataRouteSuggestions } from "./shouldRequestDataRouteSuggestions";

describe("shouldRequestDataRouteSuggestions", () => {
  it("ignora vazio e token único curto", () => {
    expect(shouldRequestDataRouteSuggestions("")).toBe(false);
    expect(shouldRequestDataRouteSuggestions("oee")).toBe(false);
    expect(shouldRequestDataRouteSuggestions("estoque")).toBe(false);
  });

  it("aceita domínio+indicador (2+ tokens) ou 12+ chars", () => {
    expect(shouldRequestDataRouteSuggestions("otd comercial")).toBe(true);
    expect(shouldRequestDataRouteSuggestions("dois termos")).toBe(true);
    expect(shouldRequestDataRouteSuggestions("oee da semana")).toBe(true);
    expect(shouldRequestDataRouteSuggestions("eficiencia fabril")).toBe(true);
  });
});
