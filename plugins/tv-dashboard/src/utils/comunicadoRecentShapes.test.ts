import { describe, expect, it } from "vitest";

import { rememberComunicadoShape, readRecentComunicadoShapes } from "./comunicadoRecentShapes";

describe("comunicadoRecentShapes", () => {
  it("mantém no máximo 8 formas recentes sem duplicar", () => {
    const first = rememberComunicadoShape("rectangle");
    const second = rememberComunicadoShape("ellipse");
    const third = rememberComunicadoShape("rectangle");

    expect(first).toEqual(["rectangle"]);
    expect(second[0]).toBe("ellipse");
    expect(third[0]).toBe("rectangle");
    expect(third[1]).toBe("ellipse");
    expect(readRecentComunicadoShapes()[0]).toBe("rectangle");
  });
});
