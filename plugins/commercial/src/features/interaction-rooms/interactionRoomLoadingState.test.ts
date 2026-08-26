import { describe, expect, it } from "vitest";

import {
  resolveInboxLoadingState,
  resolveThreadLoadingState,
} from "./interactionRoomLoadingState";

describe("interactionRoomLoadingState", () => {
  it("inbox: initial load sem itens", () => {
    expect(
      resolveInboxLoadingState({ loading: true, itemCount: 0, hasError: false }),
    ).toEqual({ initialLoading: true, refreshing: false });
  });

  it("inbox: refetch mantém lista visível", () => {
    expect(
      resolveInboxLoadingState({ loading: true, itemCount: 3, hasError: false }),
    ).toEqual({ initialLoading: false, refreshing: true });
  });

  it("thread: primeira carga", () => {
    expect(
      resolveThreadLoadingState({ loading: true, hasRoomSnapshot: false }),
    ).toEqual({ initialLoading: true, refreshing: false });
  });

  it("thread: refetch com snapshot", () => {
    expect(
      resolveThreadLoadingState({ loading: true, hasRoomSnapshot: true }),
    ).toEqual({ initialLoading: false, refreshing: true });
  });
});
