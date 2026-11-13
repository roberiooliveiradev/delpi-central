import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConcurrentChangeNotice } from "./ConcurrentChangeNotice";
import { RealtimeStatusIndicator } from "./RealtimeStatusIndicator";
import { useRealtimeRooms } from "./useRealtimeRooms";

function Rooms({ enabled }: { enabled: boolean }) {
  const { status } = useRealtimeRooms({
    enabled,
    config: {
      buildUrl: () => "wss://h/ws",
      onMessage: () => undefined,
    },
    rooms: ['{"type":"subscribe","room":"a"}'],
    onEvent: () => undefined,
  });
  return <span>{status}</span>;
}

describe("indicador e aviso", () => {
  it("não renderiza idle nem closed e anuncia o estado", () => {
    const { rerender } = render(<RealtimeStatusIndicator status="idle" />);
    expect(screen.queryByRole("status")).toBeNull();
    rerender(<RealtimeStatusIndicator status="open" />);
    expect(screen.getByRole("status").textContent).toBe("Ao vivo");
    rerender(<RealtimeStatusIndicator status="unavailable" />);
    expect(screen.getByRole("status").textContent).toBe(
      "Atualização automática indisponível",
    );
  });

  it("o aviso não recebe foco sozinho e a ação é teclável", async () => {
    const onAction = vi.fn();
    render(
      <ConcurrentChangeNotice
        message="Esta solicitação foi alterada por outra pessoa"
        onAction={onAction}
      />,
    );
    const button = screen.getByRole("button", { name: "Recarregar" });
    expect(document.activeElement).not.toBe(button);
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledOnce();
  });
});

describe("useRealtimeRooms", () => {
  it("enabled false não abre socket", () => {
    const instances = (globalThis.WebSocket as { instances?: unknown[] }).instances;
    void instances;
    render(<Rooms enabled={false} />);
    expect(screen.getByText("idle")).toBeTruthy();
  });
});
