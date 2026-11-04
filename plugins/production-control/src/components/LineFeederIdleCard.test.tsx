// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LineFeederIdleCard } from "./LineFeederIdleCard";

afterEach(() => {
  cleanup();
});

describe("LineFeederIdleCard", () => {
  it("mostra orientação amigável e destaca Coletar no centro", () => {
    const onCollect = vi.fn();
    render(<LineFeederIdleCard onCollect={onCollect} />);

    expect(screen.getByRole("status", { name: /Pronto para abastecer/i })).toBeTruthy();
    expect(screen.getByText(/sem reservar material/i)).toBeTruthy();

    const cta = screen.getByRole("button", { name: /^Coletar$/i });
    expect(cta.className).toContain("ppc-feeder-idle__cta");
    fireEvent.click(cta);
    expect(onCollect).toHaveBeenCalledTimes(1);
  });

  it("respeita disabled no CTA", () => {
    const onCollect = vi.fn();
    render(<LineFeederIdleCard onCollect={onCollect} disabled />);
    const cta = screen.getByRole("button", { name: /^Coletar$/i }) as HTMLButtonElement;
    expect(cta.disabled).toBe(true);
    fireEvent.click(cta);
    expect(onCollect).not.toHaveBeenCalled();
  });
});
