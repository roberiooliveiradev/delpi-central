import { describe, expect, it, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMemo, useState } from "react";

import { usePresentationEngine } from "./usePresentationEngine";
import type { PresentationPayloadLike } from "./types";

const basePayload: PresentationPayloadLike = {
  playlist: {
    id: "p1",
    name: "Test",
    viewportProfile: "1080p",
    transitionStyle: "fade",
    globalRefreshSec: 300,
    defaultDurationSec: 30,
  },
  slides: [
    {
      id: "s1",
      sortOrder: 0,
      slideType: "native",
      durationSec: 30,
      title: "A",
      native: { screenKey: "custom_message", config: {}, data: { headline: "A" } },
    },
  ],
};

describe("usePresentationEngine — estabilidade do initialPayload", () => {
  it("não entra em loop quando o pai re-renderiza sem trocar o payload memoizado", () => {
    let setTick!: (n: number) => void;
    const clone = () => structuredClone(basePayload);

    const { result, rerender } = renderHook(() => {
      const [tick, setTickState] = useState(0);
      setTick = setTickState;
      /* Simula PresentationPreview: rewrite/clone memoizado em [initial]. */
      const initial = useMemo(() => clone(), []);
      void tick;
      return usePresentationEngine({
        initialPayload: initial,
        enableHiddenPause: false,
      });
    });

    const first = result.current.payload;
    act(() => {
      setTick(1);
    });
    rerender();
    act(() => {
      setTick(2);
    });
    rerender();
    expect(result.current.payload).toBe(first);
  });

  it("ainda atualiza quando o initialPayload memoizado muda de verdade", () => {
    const onRefresh = vi.fn();
    const { result, rerender } = renderHook(
      ({ payload }) =>
        usePresentationEngine({
          initialPayload: payload,
          onRefresh,
          enableHiddenPause: false,
        }),
      { initialProps: { payload: basePayload } },
    );

    const next = {
      ...basePayload,
      playlist: { ...basePayload.playlist, name: "Atualizado" },
    };
    rerender({ payload: next });
    expect(result.current.payload.playlist.name).toBe("Atualizado");
  });
});
