import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { DELPI_PERSON_PROFILE_CHANGED_EVENT } from "./personProfileEvents";

const dir = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(dir, "../../../../");

describe("person profile Core sync", () => {
  it("uses Core person-profile paths (not supplies-api photo store)", () => {
    const api = readFileSync(join(dir, "../api/personProfileApi.ts"), "utf8");
    expect(api).toContain("/core-api/me/person-profile");
    expect(api).toContain("/core-api/me/person-profile/photo");
    expect(api).not.toMatch(/suppliesApiUrl/);
  });

  it("TopBar and UserProfile consume useMyPersonProfile", () => {
    const slots = readFileSync(join(dir, "ShellTopBarSlots.tsx"), "utf8");
    const page = readFileSync(join(dir, "../features/users/UserProfilePage.tsx"), "utf8");
    const hook = readFileSync(join(dir, "useMyPersonProfile.ts"), "utf8");
    expect(slots).toContain("useMyPersonProfile");
    expect(slots).toContain("src={photoUrl}");
    expect(page).toContain("useMyPersonProfile");
    expect(page).toContain("jobTitleLabel");
    expect(hook).toContain(DELPI_PERSON_PROFILE_CHANGED_EVENT);
  });

  it("keeps the same CustomEvent contract as the host Portal", () => {
    const portalEvents = readFileSync(
      join(repoRoot, "portal/src/ui/profile/personProfilePhotoEvents.ts"),
      "utf8",
    );
    expect(portalEvents).toContain(`"${DELPI_PERSON_PROFILE_CHANGED_EVENT}"`);
    expect(portalEvents).toContain("notifyPersonProfileChanged");
    expect(portalEvents).toContain("notifyPersonProfilePhotoChanged");
  });
});
