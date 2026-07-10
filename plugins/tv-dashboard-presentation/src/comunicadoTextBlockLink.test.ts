import { describe, expect, it } from "vitest";

import {
  appendHrefLineToRuns,
  isLikelyExternalUrl,
  normalizeHrefInput,
  partitionTextBlockRunsAndHref,
} from "./comunicadoTextBlockLink";

describe("comunicadoTextBlockLink", () => {
  it("detecta e normaliza URLs", () => {
    expect(isLikelyExternalUrl("https://delpi.com")).toBe(true);
    expect(normalizeHrefInput("www.exemplo.com")).toBe("https://www.exemplo.com");
  });

  it("anexa href como linha editável", () => {
    const runs = appendHrefLineToRuns([{ text: "Título" }], "https://a.com");
    expect(partitionTextBlockRunsAndHref(runs).href).toBe("https://a.com");
    expect(partitionTextBlockRunsAndHref(runs).runs[0]?.text).toBe("Título");
  });

  it("extrai href de linha URL ao salvar", () => {
    const { runs, href } = partitionTextBlockRunsAndHref([
      { text: "Comunicado\n" },
      { text: "https://minhadelpi.com.br/tv" },
    ]);
    expect(href).toBe("https://minhadelpi.com.br/tv");
    expect(runs.map((run) => run.text).join("")).toBe("Comunicado");
  });
});
