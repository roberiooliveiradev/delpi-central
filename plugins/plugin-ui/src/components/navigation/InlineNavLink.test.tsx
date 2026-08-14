import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { MouseEvent } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  InlineNavLink,
  createDashboardInlineNavLink,
  inlineNavLinkBemClasses,
  shouldHandleInlineNavClick,
} from "./InlineNavLink";

afterEach(cleanup);

const classNames = inlineNavLinkBemClasses("cm");

describe("shouldHandleInlineNavClick", () => {
  it("aceita left-click limpo e rejeita modificadores", () => {
    const base = {
      defaultPrevented: false,
      button: 0,
      metaKey: false,
      ctrlKey: false,
      shiftKey: false,
      altKey: false,
    } as MouseEvent<HTMLAnchorElement>;
    expect(shouldHandleInlineNavClick(base)).toBe(true);
    expect(shouldHandleInlineNavClick({ ...base, ctrlKey: true })).toBe(false);
    expect(shouldHandleInlineNavClick({ ...base, button: 1 })).toBe(false);
  });
});

describe("InlineNavLink", () => {
  it("renderiza anchor com href, title e dual-class", () => {
    render(
      <InlineNavLink
        classNames={classNames}
        href="/apps/commercial/customers/1/01"
        title="Abrir conta de Exemplo"
      >
        Exemplo
      </InlineNavLink>,
    );
    const link = screen.getByRole("link", { name: "Abrir conta de Exemplo" });
    expect(link.getAttribute("href")).toBe("/apps/commercial/customers/1/01");
    expect(link.getAttribute("title")).toBe("Abrir conta de Exemplo");
    expect(link.className).toContain("cm-inline-nav-link");
    expect(link.className).toContain("delpi-ui-inline-nav-link");
  });

  it("left-click chama onNavigate; Ctrl+click não", () => {
    const onNavigate = vi.fn((event: MouseEvent<HTMLAnchorElement>) => {
      event.preventDefault();
    });
    render(
      <InlineNavLink
        classNames={classNames}
        href="/apps/commercial/users/u1"
        title="Abrir perfil de Ana"
        onNavigate={onNavigate}
      >
        Ana
      </InlineNavLink>,
    );
    const link = screen.getByRole("link", { name: "Abrir perfil de Ana" });
    fireEvent.click(link);
    expect(onNavigate).toHaveBeenCalledTimes(1);

    onNavigate.mockClear();
    fireEvent.click(link, { ctrlKey: true });
    expect(onNavigate).not.toHaveBeenCalled();
  });

  it("createDashboardInlineNavLink aplica prefixo", () => {
    const Link = createDashboardInlineNavLink("cm");
    render(
      <Link href="/apps/commercial/customers" title="Abrir Minha Carteira">
        Carteira
      </Link>,
    );
    expect(screen.getByRole("link").className).toContain("cm-inline-nav-link");
  });

  it("rejeita href externo", () => {
    expect(() =>
      render(
        <InlineNavLink
          classNames={classNames}
          href="https://evil.example"
          title="x"
        >
          x
        </InlineNavLink>,
      ),
    ).toThrow(/href/);
  });
});
