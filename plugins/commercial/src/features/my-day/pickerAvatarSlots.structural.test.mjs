import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "../../../../..");

describe("picker avatar slots", () => {
  it("UserDirectoryPicker e CustomerSearchPicker expõem slots de avatar", () => {
    const kit = readFileSync(
      join(repo, "plugins/plugin-ui/src/components/directory/UserDirectoryPicker.tsx"),
      "utf8",
    );
    assert.match(kit, /renderOptionLeading\?:/);
    assert.match(kit, /renderSelectedChip\?:/);

    const customer = readFileSync(
      join(here, "../customers/components/CustomerSearchPicker.tsx"),
      "utf8",
    );
    assert.match(customer, /renderOptionLeading\?:/);
    assert.match(customer, /renderSelectedChip\?:/);

    const page = readFileSync(join(here, "MyDayPage.tsx"), "utf8");
    assert.match(page, /renderOptionLeading=\{/);
    assert.match(page, /renderSelectedChip=\{/);
    assert.match(page, /TaskUserChipAvatar/);
    assert.match(page, /CustomerAvatar/);
  });
});
