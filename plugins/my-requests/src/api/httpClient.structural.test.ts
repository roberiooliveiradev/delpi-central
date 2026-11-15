import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const src = readFileSync(
  fileURLToPath(new URL("./httpClient.ts", import.meta.url)),
  "utf8",
);

describe("httpClient resilience contract", () => {
  it("define um timeout total padrão para toda chamada HTTP", () => {
    expect(src).toContain("HTTP_REQUEST_TIMEOUT_MS");
    expect(src).toContain("AbortSignal.timeout");
    /* Caller aborts still win via AbortSignal.any. */
    expect(src).toContain("AbortSignal.any");
  });

  it("aplica o timeout nos quatro métodos — nenhum fetch fica sem signal", () => {
    const timed = src.match(/signal: withRequestTimeout\(options\.signal\)/g);
    expect(timed).toHaveLength(4);
    expect(src).not.toContain("signal: options.signal,");
  });
});
