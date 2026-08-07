#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildCommercialOpenOrderPath,
  findOpenOrderLine,
  parseOpenOrdersAttentionDeepLink,
  parseOpenOrdersLineDeepLink,
} from "./openOrdersDeepLink.ts";

describe("openOrdersDeepLink", () => {
  it("monta path com pedido linha e filial", () => {
    assert.equal(
      buildCommercialOpenOrderPath({
        pedido: "123",
        linha: "01",
        filial: "02",
      }),
      "/apps/commercial/open-orders?pedido=123&linha=01&filial=02",
    );
  });

  it("monta path só com pedido", () => {
    assert.equal(
      buildCommercialOpenOrderPath({ pedido: "123", filial: "01" }),
      "/apps/commercial/open-orders?pedido=123&filial=01",
    );
  });

  it("parseia atenção e linha", () => {
    assert.deepEqual(
      parseOpenOrdersAttentionDeepLink("?stock=parcial&focus=late"),
      { stockStatus: "parcial", lateOnly: true },
    );
    assert.deepEqual(parseOpenOrdersLineDeepLink("?pedido=9&linha=02&filial=01"), {
      pedido: "9",
      linha: "02",
      filial: "01",
    });
    assert.deepEqual(parseOpenOrdersLineDeepLink("?pedido=9"), {
      pedido: "9",
      linha: undefined,
      filial: undefined,
    });
    assert.equal(parseOpenOrdersLineDeepLink("?linha=01"), null);
  });

  it("encontra linha na lista", () => {
    const hit = findOpenOrderLine(
      [
        { filial: "01", pedido: "A", linha: "01" },
        { filial: "02", pedido: "B", linha: "02" },
      ],
      { pedido: "B", linha: "02", filial: "02" },
    );
    assert.equal(hit?.pedido, "B");
  });

  it("encontra primeira linha quando só pedido", () => {
    const hit = findOpenOrderLine(
      [
        { filial: "01", pedido: "A", linha: "01" },
        { filial: "01", pedido: "A", linha: "02" },
      ],
      { pedido: "A" },
    );
    assert.equal(hit?.linha, "01");
  });
});
