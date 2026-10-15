import { cleanup, render, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationTimeline } from "../ui/ConversationTimeline";
import { useCurrentUserIdentity } from "./currentUser";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  // Remove jsdom-injected URL statics from tests that define them.
  const urlStatic = URL as unknown as Record<string, unknown>;
  delete urlStatic.createObjectURL;
  delete urlStatic.revokeObjectURL;
});

function stubIdentityFetch(options: {
  name?: string;
  hasPhoto?: boolean;
  fail?: boolean;
}) {
  return vi.fn().mockImplementation((input: RequestInfo | URL) => {
    const url = String(input);
    if (options.fail) {
      return Promise.resolve(new Response("{}", { status: 500 }));
    }
    if (url.endsWith("/core-api/me")) {
      return Promise.resolve(
        new Response(JSON.stringify({ name: options.name ?? null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
    if (url.endsWith("/core-api/me/person-profile")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({ has_photo: options.hasPhoto ?? false }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    }
    if (url.endsWith("/core-api/me/person-profile/photo")) {
      return Promise.resolve(
        new Response(new Uint8Array([9, 9]), {
          status: 200,
        }),
      );
    }
    return Promise.reject(new Error(`unexpected call ${url}`));
  });
}

describe("useCurrentUserIdentity", () => {
  it("does not fetch without an access token", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useCurrentUserIdentity());
    await Promise.resolve();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.displayName).toBeNull();
    expect(result.current.imageUrl).toBeNull();
  });

  it("loads display name and photo object URL", async () => {
    vi.stubGlobal("fetch", stubIdentityFetch({ name: "Ana Lima", hasPhoto: true }));
    // jsdom lacks URL.createObjectURL — define it; afterEach removes.
    const urlStatic = URL as unknown as Record<string, unknown>;
    urlStatic.createObjectURL = vi.fn(() => "blob:photo");
    urlStatic.revokeObjectURL = vi.fn();
    const { result } = renderHook(() =>
      useCurrentUserIdentity(() => "t"),
    );
    await waitFor(() =>
      expect(result.current.displayName).toBe("Ana Lima"),
    );
    expect(result.current.imageUrl).toBe("blob:photo");
  });

  it("keeps imageUrl null when the profile has no photo", async () => {
    const fetchMock = stubIdentityFetch({ name: "Ana Lima", hasPhoto: false });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() =>
      useCurrentUserIdentity(() => "t"),
    );
    await waitFor(() =>
      expect(result.current.displayName).toBe("Ana Lima"),
    );
    expect(result.current.imageUrl).toBeNull();
    // Only /me + /person-profile — never the photo blob.
    expect(
      fetchMock.mock.calls.filter(([u]) =>
        String(u).endsWith("/photo"),
      ),
    ).toHaveLength(0);
  });

  it("degrades silently on failure", async () => {
    vi.stubGlobal("fetch", stubIdentityFetch({ fail: true }));
    const { result } = renderHook(() =>
      useCurrentUserIdentity(() => "t"),
    );
    await Promise.resolve();
    expect(result.current.displayName).toBeNull();
    expect(result.current.imageUrl).toBeNull();
  });
});

describe("ConversationTimeline — user avatar identity", () => {
  const turns = [
    { id: "u1", role: "user" as const, content: "olá" },
  ];
  const noop = () => {};

  it("renders initials from the real display name", () => {
    const { container } = render(
      <ConversationTimeline
        turns={turns}
        loading={false}
        onConfirmation={noop}
        userIdentity={{ displayName: "Ana Lima", imageUrl: null }}
      />,
    );
    const avatar = container.querySelector(
      ".delpi-ui-unified-avatar--person",
    );
    expect(avatar).toBeTruthy();
    expect(avatar?.textContent).toContain("AL");
  });

  it("renders the published photo when provided", () => {
    const { container } = render(
      <ConversationTimeline
        turns={turns}
        loading={false}
        onConfirmation={noop}
        userIdentity={{
          displayName: "Ana Lima",
          imageUrl: "blob:https://x/1",
        }}
      />,
    );
    const img = container.querySelector(
      ".delpi-ui-unified-avatar--person img",
    );
    expect(img?.getAttribute("src")).toBe("blob:https://x/1");
  });

  it("falls back to the neutral person avatar without identity", () => {
    const { container } = render(
      <ConversationTimeline
        turns={turns}
        loading={false}
        onConfirmation={noop}
      />,
    );
    const avatar = container.querySelector(
      ".delpi-ui-unified-avatar--person",
    );
    expect(avatar).toBeTruthy();
    expect(avatar?.querySelector("img")).toBeNull();
  });
});
