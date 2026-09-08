import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  buildListSearchParams,
  buildRequestKey,
  createDefaultQuery,
  parseQueryFromSearch,
  parseRequestKey,
} from "./query";

const dir = dirname(fileURLToPath(import.meta.url));

describe("PurchaseRequests feature", () => {
  it("App liga a página real em vez do placeholder", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    expect(app).toMatch(/PurchaseRequestsPage/);
    expect(app).not.toMatch(/Lista e detalhe de SC entram na jornada C1/);
  });

  it("cliente fala só com supplies-api", () => {
    const api = readFileSync(join(dir, "api.ts"), "utf8");
    expect(api).toMatch(/suppliesApiUrl\(`\/purchase-requests/);
    expect(api).not.toMatch(/purchase-requests-api/);
  });

  it("query positive + sibling + negative", () => {
    const query = createDefaultQuery("01");
    query.request_number = "100";
    query.overall_stages = ["awaiting_order"];
    const params = buildListSearchParams(query);
    expect(params.get("branch")).toBe("01");
    expect(params.get("request_number")).toBe("100");
    expect(params.getAll("overall_stage")).toEqual(["awaiting_order"]);

    const sibling = parseQueryFromSearch("?branch=02&request=02:200", "01");
    expect(sibling.branch).toBe("02");
    expect(parseRequestKey(sibling.request)).toEqual({
      branch: "02",
      requestNumber: "200",
    });

    expect(parseRequestKey("invalid")).toBeNull();
    expect(buildRequestKey("01", "100")).toBe("01:100");
  });
});
