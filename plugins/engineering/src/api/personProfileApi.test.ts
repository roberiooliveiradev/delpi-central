import { describe, expect, it, vi } from "vitest";

vi.mock("./httpClient", () => ({
  getJson: vi.fn(async (path: string) => ({ path, has_photo: true })),
  getBlob: vi.fn(async (path: string) => new Blob([path])),
}));

import { getBlob, getJson } from "./httpClient";
import {
  getMyPersonProfile,
  getMyPersonProfilePhoto,
} from "./personProfileApi";

describe("personProfileApi", () => {
  it("lê o perfil oficial no contrato Core /me/person-profile", async () => {
    const profile = await getMyPersonProfile();
    expect(getJson).toHaveBeenCalledWith(
      "/core-api/me/person-profile",
      undefined,
    );
    expect(profile.has_photo).toBe(true);
  });

  it("busca a foto no endpoint oficial /me/person-profile/photo", async () => {
    const blob = await getMyPersonProfilePhoto();
    expect(getBlob).toHaveBeenCalledWith(
      "/core-api/me/person-profile/photo",
      undefined,
    );
    expect(blob.size).toBeGreaterThan(0);
  });
});
