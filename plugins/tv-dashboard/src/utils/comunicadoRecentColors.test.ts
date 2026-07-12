import { beforeEach, describe, expect, it } from "vitest";

import { readRecentComunicadoColors, rememberComunicadoColor } from "./comunicadoRecentColors";

describe("comunicadoRecentColors", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it("lembra e deduplica cores", () => {
    rememberComunicadoColor("#AABBCC");
    rememberComunicadoColor("#112233");
    rememberComunicadoColor("#aabbcc");
    expect(readRecentComunicadoColors()).toEqual(["#aabbcc", "#112233"]);
  });

  it("ignora transparent/auto", () => {
    rememberComunicadoColor("transparent");
    rememberComunicadoColor("auto");
    expect(readRecentComunicadoColors()).toEqual([]);
  });
});
