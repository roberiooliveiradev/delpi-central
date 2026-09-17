import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  buildPublicDrawingPdfUrl,
  buildPublicOperationMaterialsUrl,
  buildPublicProductModelGlbUrl,
} from "./api.ts";

describe("public cockpit asset URLs", () => {
  it("builds the PA drawing PDF URL", () => {
    assert.equal(
      buildPublicDrawingPdfUrl("aberto", "01", "90262957"),
      "/apps/production-control-api/public/machine-load/aberto/drawings/90262957/pdf?branch=01",
    );
  });

  it("builds the OP product GLB URL, not the PA drawing path", () => {
    assert.equal(
      buildPublicProductModelGlbUrl("aberto", "01", "50320064"),
      "/apps/production-control-api/public/machine-load/aberto/models/50320064/glb?branch=01",
    );
  });

  it("encodes reserved characters in the product code", () => {
    assert.equal(
      buildPublicProductModelGlbUrl("aberto", "02", "PI/01"),
      "/apps/production-control-api/public/machine-load/aberto/models/PI%2F01/glb?branch=02",
    );
  });

  it("builds the operation materials URL with OP and operation filters", () => {
    assert.equal(
      buildPublicOperationMaterialsUrl("aberto", "01", "10964501004", "01"),
      "/apps/production-control-api/public/machine-load/aberto/operations/materials?branch=01&productionOrder=10964501004&operationCode=01",
    );
  });
});
