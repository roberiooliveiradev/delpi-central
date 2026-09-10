import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("PersonIdentity / avatar surfaces", () => {
  it("PersonIdentity usa MyRequestsAvatar", () => {
    const src = read("components/PersonIdentity.tsx");
    expect(src).toMatch(/MyRequestsAvatar/);
    expect(src).toMatch(/my-requests-person-identity/);
  });

  it("Solicitante e Timeline usam PersonIdentity + hook de avatar", () => {
    const detail = read("pages/RequestDetailPage.tsx");
    const timeline = read("components/TimelinePanel.tsx");
    expect(detail).toMatch(/PersonIdentity/);
    expect(detail).toMatch(/useParticipantAvatarUrls/);
    expect(detail).toMatch(/created_by_user_id/);
    expect(timeline).toMatch(/PersonIdentity/);
    expect(timeline).toMatch(/useParticipantAvatarUrls/);
    expect(timeline).toMatch(/actor_user_id/);
    expect(timeline).toMatch(/timelineEventTitle/);
    expect(timeline).toMatch(/timelineEventJustification/);
    expect(detail).not.toMatch(/commercial-api/);
    expect(timeline).not.toMatch(/core-api\/person/);
  });
});
