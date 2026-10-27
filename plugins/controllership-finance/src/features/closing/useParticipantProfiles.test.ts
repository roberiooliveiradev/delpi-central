/** UX-009-RW01 — isolamento de perfis por (competência, documento):
 * perfis resolvidos num contexto nunca são exibidos em outro, trocas de
 * documento abortam a resolução anterior e URLs de objeto são revogadas.
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useParticipantProfiles } from "./useParticipantProfiles";

const lookupMock = vi.fn();
const avatarMock = vi.fn();

vi.mock("../../api/participantsApi", () => ({
  lookupParticipants: (...args: unknown[]) => lookupMock(...args),
  downloadParticipantAvatar: (...args: unknown[]) => avatarMock(...args),
}));

const CTX_A = { period: "2026-05", documentId: "doc-a" };
const CTX_B = { period: "2026-05", documentId: "doc-b" };
const USER = "11111111-2222-3333-4444-555555555555";

beforeEach(() => {
  vi.clearAllMocks();
  lookupMock.mockResolvedValue({
    items: [{ user_id: USER, display_name: "Ana Souza", has_photo: false }],
  });
  avatarMock.mockResolvedValue(new Blob(["jpg"]));
});

describe("useParticipantProfiles", () => {
  it("resolve perfis no contexto do documento", async () => {
    const { result } = renderHook(() =>
      useParticipantProfiles(CTX_A, [USER]),
    );

    await waitFor(() =>
      expect(result.current.get(USER)?.displayName).toBe("Ana Souza"),
    );
    expect(lookupMock).toHaveBeenCalledWith(CTX_A, [USER], expect.anything());
  });

  it("trocar de documento não exibe perfis do contexto anterior", async () => {
    const { result, rerender } = renderHook(
      ({ context }) => useParticipantProfiles(context, [USER]),
      { initialProps: { context: CTX_A } },
    );
    await waitFor(() =>
      expect(result.current.get(USER)?.displayName).toBe("Ana Souza"),
    );

    // Antes de a nova consulta resolver, nenhum perfil stale aparece.
    rerender({ context: CTX_B });
    expect(result.current.size).toBe(0);

    await waitFor(() =>
      expect(lookupMock).toHaveBeenLastCalledWith(
        CTX_B,
        [USER],
        expect.anything(),
      ),
    );
    await waitFor(() =>
      expect(result.current.get(USER)?.displayName).toBe("Ana Souza"),
    );
  });

  it("trocar de competência também isola os perfis", async () => {
    const { result, rerender } = renderHook(
      ({ context }) => useParticipantProfiles(context, [USER]),
      { initialProps: { context: CTX_A } },
    );
    await waitFor(() => expect(result.current.size).toBe(1));

    rerender({ context: { period: "2026-06", documentId: "doc-a" } });
    expect(result.current.size).toBe(0);
    await waitFor(() =>
      expect(lookupMock).toHaveBeenLastCalledWith(
        { period: "2026-06", documentId: "doc-a" },
        [USER],
        expect.anything(),
      ),
    );
  });

  it("aborte a requisição anterior e revogue URLs ao trocar contexto", async () => {
    const signals: (AbortSignal | undefined)[] = [];
    lookupMock.mockImplementation((_ctx, _ids, opts) => {
      signals.push(opts?.signal);
      return new Promise((_r) => setTimeout(() => _r({ items: [] }), 50));
    });
    const { rerender, unmount } = renderHook(
      ({ context }) => useParticipantProfiles(context, [USER]),
      { initialProps: { context: CTX_A } },
    );
    await act(async () => {
      rerender({ context: CTX_B });
    });
    expect(signals[0]?.aborted).toBe(true);
    unmount();
  });

  it("perfil sem foto mantém photoUrl nulo (fallback de iniciais)", async () => {
    lookupMock.mockResolvedValue({
      items: [
        { user_id: USER, display_name: "Ana Souza", has_photo: false },
      ],
    });
    const { result } = renderHook(() =>
      useParticipantProfiles(CTX_A, [USER]),
    );
    await waitFor(() => expect(result.current.size).toBe(1));
    expect(result.current.get(USER)?.photoUrl).toBeNull();
    expect(avatarMock).not.toHaveBeenCalled();
  });

  it("falha do lookup devolve mapa vazio no contexto (sem stale)", async () => {
    lookupMock.mockRejectedValue(new Error("403"));
    const { result } = renderHook(() =>
      useParticipantProfiles(CTX_A, [USER]),
    );
    await waitFor(() => expect(result.current.size).toBe(0));
  });
});
