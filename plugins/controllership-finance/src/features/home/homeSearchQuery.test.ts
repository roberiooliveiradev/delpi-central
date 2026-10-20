import { describe, expect, it } from "vitest";

import { readHomeSearchQuery, writeHomeSearchQuery } from "./homeSearchQuery";

describe("homeSearchQuery — deep link ?q=", () => {
  it("lê ?q= da URL", () => {
    expect(readHomeSearchQuery("?q=inicio")).toBe("inicio");
    expect(readHomeSearchQuery("?q=")).toBe("");
    expect(readHomeSearchQuery("?other=1")).toBe("");
  });

  it("lê com encoding", () => {
    expect(readHomeSearchQuery("?q=vis%C3%A3o")).toBe("visão");
  });

  it("escreve e remove ?q= preservando path", () => {
    window.history.replaceState(null, "", "/apps/controllership-finance");
    writeHomeSearchQuery("central");
    expect(window.location.search).toBe("?q=central");
    writeHomeSearchQuery("");
    expect(window.location.search).toBe("");
    expect(window.location.pathname).toBe("/apps/controllership-finance");
  });
});
