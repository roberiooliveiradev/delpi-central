#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { buildCommercialOpenOrderPath } from "./commercialOpenOrderLink.ts";

describe("buildCommercialOpenOrderPath", () => {
  it("retorna null sem pedido", () => {
    assert.equal(buildCommercialOpenOrderPath({ pedido: "  " }), null);
  });

  it("monta URL com pedido linha e filial", () => {
    assert.equal(
      buildCommercialOpenOrderPath({
        pedido: "100",
        linha: "02",
        filial: "01",
      }),
      "/apps/commercial/open-orders?pedido=100&linha=02&filial=01",
    );
  });

  it("omite linha ausente", () => {
    assert.equal(
      buildCommercialOpenOrderPath({ pedido: "100", filial: "01" }),
      "/apps/commercial/open-orders?pedido=100&filial=01",
    );
  });
});
