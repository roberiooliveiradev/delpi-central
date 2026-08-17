import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { HTTP_ERROR_CONTENT } from "../content/httpErrorContent.ts";
import {
  looksLikeGatewayOrHtmlNoise,
  resolveHttpErrorMessage,
} from "./httpErrorMessage.ts";

describe("httpErrorMessage", () => {
  it("detects Cloudflare / HTML noise", () => {
    assert.equal(
      looksLikeGatewayOrHtmlNoise(
        "The origin web server returned an invalid or incomplete response to Cloudflare.",
      ),
      true,
    );
    assert.equal(looksLikeGatewayOrHtmlNoise("<!DOCTYPE html><html>"), true);
    assert.equal(looksLikeGatewayOrHtmlNoise("Permissão negada"), false);
  });

  it("maps 502-504 to friendly gateway message", () => {
    assert.equal(
      resolveHttpErrorMessage(502, "Cloudflare Bad Gateway"),
      HTTP_ERROR_CONTENT.gatewayUnavailable,
    );
    assert.equal(
      resolveHttpErrorMessage(503, null),
      HTTP_ERROR_CONTENT.gatewayUnavailable,
    );
  });

  it("keeps business JSON messages on 4xx", () => {
    assert.equal(
      resolveHttpErrorMessage(403, "Sem permissão commercial.access"),
      "Sem permissão commercial.access",
    );
  });

  it("sanitizes HTML noise even on non-gateway status", () => {
    assert.equal(
      resolveHttpErrorMessage(500, "<html>error</html>"),
      HTTP_ERROR_CONTENT.gatewayUnavailable,
    );
  });
});
