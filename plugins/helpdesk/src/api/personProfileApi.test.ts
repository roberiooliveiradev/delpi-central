import { describe, expect, it } from "vitest";

import { PERSON_PROFILE_PATH, PERSON_PROFILE_PHOTO_PATH } from "./personProfileApi";

describe("person profile client", () => {
  it("busca a foto no Core, não no helpdesk-api", () => {
    expect(PERSON_PROFILE_PATH).toBe("/core-api/me/person-profile");
    expect(PERSON_PROFILE_PHOTO_PATH).toBe("/core-api/me/person-profile/photo");
    expect(PERSON_PROFILE_PATH.startsWith("/apps/helpdesk-api")).toBe(false);
  });
});
