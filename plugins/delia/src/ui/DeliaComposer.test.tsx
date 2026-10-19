import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeliaComposer } from "./DeliaComposer";

afterEach(cleanup);

describe("DeliaComposer — audio capture gate", () => {
  it("does not expose mic when audioCaptureEnabled is false (default)", () => {
    render(
      <DeliaComposer
        inputId="delia-input"
        value=""
        onChange={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Gravar áudio" })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Gravação de áudio indisponível" }),
    ).toBeNull();
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toBeTruthy();
  });

  it("shows unavailable mic when enabled without approved limits", () => {
    render(
      <DeliaComposer
        inputId="delia-input"
        value="draft"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        audioCaptureEnabled
      />,
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Gravação de áudio indisponível",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toHaveProperty(
      "value",
      "draft",
    );
  });

  it("shows mic trigger when enabled with explicit QA fixture limits", () => {
    Object.defineProperty(window, "isSecureContext", {
      configurable: true,
      get: () => true,
    });
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn() },
    });
    (
      globalThis as unknown as {
        MediaRecorder: {
          isTypeSupported: (m: string) => boolean;
        };
      }
    ).MediaRecorder = {
      isTypeSupported: (m: string) => m.includes("webm"),
    };

    render(
      <DeliaComposer
        inputId="delia-input"
        value=""
        onChange={() => undefined}
        onSubmit={() => undefined}
        audioCaptureEnabled
        audioCaptureMaxDurationMs={60_000}
        audioCaptureMaxBytes={256_000}
      />,
    );
    expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
  });
});
