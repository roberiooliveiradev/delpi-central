import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("InteractionRoomMentionUnfurls", () => {
  it("usa EntityUnfurlCard e preview da commercial-api", () => {
    const source = readFileSync(
      join(dir, "InteractionRoomMentionUnfurls.tsx"),
      "utf8",
    );
    expect(source).toMatch(/CommercialEntityUnfurlCard/);
    expect(source).toMatch(/previewInteractionEntity/);
    expect(source).toMatch(/mapPreviewToUnfurlCardModel/);
    expect(source).toMatch(/resolveInteractionEntityHref/);
    expect(source).not.toMatch(/api-delpi/);
  });
});
