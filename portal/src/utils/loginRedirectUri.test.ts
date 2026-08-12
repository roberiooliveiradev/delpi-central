import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { resolveLoginRedirectUri } from "./loginRedirectUri.ts";

describe("resolveLoginRedirectUri", () => {
  it("preserva deep link de app no refresh/reauth", () => {
    assert.equal(
      resolveLoginRedirectUri({
        origin: "https://minhadelpi.com.br",
        pathname: "/apps/commercial/open-orders",
        search: "?q=1",
        configuredFallback: "https://minhadelpi.com.br/",
      }),
      "https://minhadelpi.com.br/apps/commercial/open-orders?q=1",
    );
  });

  it("preserva a home atual", () => {
    assert.equal(
      resolveLoginRedirectUri({
        origin: "https://minhadelpi.com.br",
        pathname: "/",
        configuredFallback: "https://minhadelpi.com.br/",
      }),
      "https://minhadelpi.com.br/",
    );
  });

  it("usa fallback configurado apenas a partir de /login", () => {
    assert.equal(
      resolveLoginRedirectUri({
        origin: "https://minhadelpi.com.br",
        pathname: "/login",
        configuredFallback: "https://minhadelpi.com.br/",
      }),
      "https://minhadelpi.com.br/",
    );
  });
});
