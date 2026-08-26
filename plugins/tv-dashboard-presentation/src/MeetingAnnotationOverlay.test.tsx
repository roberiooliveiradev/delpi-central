import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, fireEvent, render } from "@testing-library/react";
import { createRef } from "react";

import {
  MeetingAnnotationOverlay,
  type MeetingAnnotationOverlayHandle,
} from "./MeetingAnnotationOverlay";

describe("MeetingAnnotationOverlay", () => {
  let rafQueue: FrameRequestCallback[] = [];

  beforeEach(() => {
    rafQueue = [];
    vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => {
      rafQueue.push(cb);
      return rafQueue.length;
    });
    vi.stubGlobal("cancelAnimationFrame", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function flushRaf() {
    const pending = rafQueue.splice(0);
    for (const cb of pending) {
      act(() => cb(0));
    }
  }

  it("pinta laser local via DOM sem flood de rede a cada frame", () => {
    const onLocalLaserNetwork = vi.fn();
    const { container } = render(
      <MeetingAnnotationOverlay
        enabled
        slideId="s1"
        clientId="self"
        tool="laser"
        strokes={[]}
        onLocalStroke={vi.fn()}
        onLocalLaserNetwork={onLocalLaserNetwork}
      />,
    );

    const overlay = container.querySelector(".tdp-meeting-annotation") as HTMLDivElement;
    expect(overlay).toBeTruthy();

    Object.defineProperty(overlay, "clientWidth", { value: 800, configurable: true });
    Object.defineProperty(overlay, "clientHeight", { value: 450, configurable: true });
    overlay.getBoundingClientRect = () =>
      ({
        width: 800,
        height: 450,
        left: 0,
        top: 0,
        right: 800,
        bottom: 450,
        x: 0,
        y: 0,
        toJSON: () => ({}),
      }) as DOMRect;

    act(() => {
      fireEvent.pointerMove(overlay, { clientX: 400, clientY: 225, pointerId: 1 });
      fireEvent.pointerMove(overlay, { clientX: 410, clientY: 230, pointerId: 1 });
      fireEvent.pointerMove(overlay, { clientX: 420, clientY: 235, pointerId: 1 });
    });
    flushRaf();

    const localLaser = container.querySelector(
      ".tdp-meeting-annotation__laser--local",
    ) as HTMLSpanElement;
    expect(localLaser.style.opacity).toBe("1");
    expect(localLaser.style.transform).toContain("translate3d");

    expect(onLocalLaserNetwork.mock.calls.length).toBeLessThanOrEqual(3);
  });

  it("paintRemoteLaser via ref atualiza laser remoto sem props lasers", () => {
    const overlayRef = createRef<MeetingAnnotationOverlayHandle>();
    const { container } = render(
      <MeetingAnnotationOverlay
        ref={overlayRef}
        enabled
        slideId="s1"
        clientId="self"
        tool="none"
        strokes={[]}
        onLocalStroke={vi.fn()}
        onLocalLaserNetwork={vi.fn()}
      />,
    );

    const overlay = container.querySelector(".tdp-meeting-annotation") as HTMLDivElement;
    Object.defineProperty(overlay, "clientWidth", { value: 1000, configurable: true });
    Object.defineProperty(overlay, "clientHeight", { value: 600, configurable: true });

    act(() => {
      overlayRef.current?.paintRemoteLaser({
        clientId: "peer",
        slideId: "s1",
        x: 0.25,
        y: 0.75,
        visible: true,
      });
    });
    flushRaf();

    const remoteLaser = container.querySelector(
      '.tdp-meeting-annotation__remote-lasers [data-client-id="peer"]',
    ) as HTMLSpanElement;
    expect(remoteLaser).toBeTruthy();
    expect(remoteLaser.style.opacity).toBe("1");
  });

  it("filtra strokes pelo slideId atual", () => {
    const { container } = render(
      <MeetingAnnotationOverlay
        enabled
        slideId="s2"
        clientId="self"
        tool="none"
        strokes={[
          {
            strokeId: "a",
            clientId: "self",
            slideId: "s1",
            points: [
              { x: 0, y: 0 },
              { x: 1, y: 1 },
            ],
          },
          {
            strokeId: "b",
            clientId: "self",
            slideId: "s2",
            points: [
              { x: 0.2, y: 0.2 },
              { x: 0.8, y: 0.8 },
            ],
          },
        ]}
        onLocalStroke={vi.fn()}
        onLocalLaserNetwork={vi.fn()}
      />,
    );

    const paths = container.querySelectorAll(".tdp-meeting-annotation__stroke");
    expect(paths).toHaveLength(1);
  });
});
