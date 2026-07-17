import { act, cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  FloatingNoticeStack,
  floatingNoticeStackBemClasses,
  useFloatingNotices,
} from "./FloatingNoticeStack";

const classNames = floatingNoticeStackBemClasses("kz");

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("FloatingNoticeStack", () => {
  it("renderiza cards no portal com variante e classes canônicas", () => {
    render(
      <FloatingNoticeStack
        items={[
          { id: "e1", message: "Falhou ao salvar", variant: "error", title: "Erro" },
          { id: "w1", message: "Assinatura pendente", variant: "warning" },
        ]}
        onDismiss={() => {}}
        classNames={classNames}
        portalScopeClassName="dashboard-kz"
      />,
    );

    const alerts = screen.getAllByRole("alert");
    expect(alerts).toHaveLength(2);
    expect(alerts[0].className).toContain("delpi-ui-floating-notice--error");
    expect(alerts[0].className).toContain("kz-floating-notice--error");
    expect(alerts[1].className).toContain("delpi-ui-floating-notice--warning");
    expect(screen.getByText("Erro")).toBeTruthy();
    expect(
      document.querySelector(".dashboard-kz .delpi-ui-floating-notices"),
    ).toBeTruthy();
  });

  it("fecha pelo botão e não renderiza nada sem itens", () => {
    const onDismiss = vi.fn();
    const { rerender } = render(
      <FloatingNoticeStack
        items={[{ id: "e1", message: "Falhou" }]}
        onDismiss={onDismiss}
        classNames={classNames}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Fechar aviso" }));
    expect(onDismiss).toHaveBeenCalledWith("e1");

    rerender(
      <FloatingNoticeStack items={[]} onDismiss={onDismiss} classNames={classNames} />,
    );
    expect(document.querySelector(".delpi-ui-floating-notices")).toBeNull();
  });

  it("auto-dismiss para sucesso; erro permanece", () => {
    vi.useFakeTimers();
    const onDismiss = vi.fn();
    render(
      <FloatingNoticeStack
        items={[
          { id: "ok", message: "Salvo", variant: "success" },
          { id: "err", message: "Falhou", variant: "error" },
        ]}
        onDismiss={onDismiss}
        classNames={classNames}
      />,
    );

    act(() => {
      vi.advanceTimersByTime(6001);
    });
    expect(onDismiss).toHaveBeenCalledTimes(1);
    expect(onDismiss).toHaveBeenCalledWith("ok");
  });
});

describe("useFloatingNotices", () => {
  it("push/dismiss/clear controlam a pilha e reaproveitam id", () => {
    const { result } = renderHook(() => useFloatingNotices());

    let firstId = "";
    act(() => {
      firstId = result.current.push("Erro simples");
      result.current.push({ id: "fixed", message: "Um", variant: "warning" });
    });
    expect(result.current.items).toHaveLength(2);

    act(() => {
      result.current.push({ id: "fixed", message: "Dois", variant: "warning" });
    });
    expect(result.current.items).toHaveLength(2);
    expect(
      result.current.items.find((item) => item.id === "fixed")?.message,
    ).toBe("Dois");

    act(() => {
      result.current.dismiss(firstId);
    });
    expect(result.current.items).toHaveLength(1);

    act(() => {
      result.current.clear();
    });
    expect(result.current.items).toHaveLength(0);
  });
});
