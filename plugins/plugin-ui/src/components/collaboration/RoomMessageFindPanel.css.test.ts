import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

describe("RoomMessageFindPanel CSS", () => {
  it("remove outline interno do input de busca no focus", () => {
    const css = readFileSync(join(stylesDir, "room-message-find.css"), "utf8");
    expect(css).toMatch(/appearance:\s*none/);
    expect(css).toMatch(/::-webkit-search-decoration/);
    expect(css).toMatch(
      /\.delpi-ui-room-message-find \.delpi-ui-room-message-find__input:focus-visible/,
    );
    expect(css).toMatch(
      /\.delpi-ui-room-message-find__search:focus-within/,
    );
  });
});
