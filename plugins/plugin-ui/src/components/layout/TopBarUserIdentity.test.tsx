import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { initialsAvatarBemClasses } from "./InitialsAvatar";
import {
  TopBarUserIdentity,
  createDashboardTopBarUserIdentity,
  topBarUserIdentityBemClasses,
} from "./TopBarUserIdentity";

afterEach(() => {
  cleanup();
});

const classNames = topBarUserIdentityBemClasses("cm");
const avatarClassNames = initialsAvatarBemClasses("cm");

describe("TopBarUserIdentity", () => {
  it("mostra displayName e dual-class", () => {
    const { container } = render(
      <TopBarUserIdentity
        classNames={classNames}
        avatarClassNames={avatarClassNames}
        displayName="Robério Oliveira"
      />,
    );
    expect(screen.getByText("Robério Oliveira")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-topbar-user")).toBeTruthy();
    expect(container.querySelector(".cm-topbar-user")).toBeTruthy();
  });

  it("usa fallback e iniciais sem avatarUrl", () => {
    render(
      <TopBarUserIdentity
        classNames={classNames}
        avatarClassNames={avatarClassNames}
        displayName={null}
        fallbackLabel="Usuário"
      />,
    );
    expect(screen.getByText("Usuário")).toBeTruthy();
  });

  it("modo link chama onNavigate", () => {
    const onNavigate = vi.fn();
    render(
      <TopBarUserIdentity
        classNames={classNames}
        avatarClassNames={avatarClassNames}
        displayName="Ana"
        href="/apps/supplies/users/me"
        onNavigate={onNavigate}
        title="Perfil"
      />,
    );
    fireEvent.click(screen.getByRole("link", { name: "Ana" }));
    expect(onNavigate).toHaveBeenCalled();
  });

  it("abre menu e seleciona item", () => {
    const onSelect = vi.fn();
    render(
      <TopBarUserIdentity
        classNames={classNames}
        avatarClassNames={avatarClassNames}
        displayName="Ana"
        menuItems={[{ id: "a", label: "Carteira A", onSelect }]}
        menuAriaLabel="Menu"
      />,
    );
    const trigger = screen.getByRole("button", { name: "Ana" });
    fireEvent.click(trigger);
    expect(trigger.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(screen.getByRole("menuitem", { name: "Carteira A" }));
    expect(onSelect).toHaveBeenCalled();
  });

  it("loading não esconde o chip", () => {
    const { container } = render(
      <TopBarUserIdentity
        classNames={classNames}
        avatarClassNames={avatarClassNames}
        displayName={null}
        loading
        fallbackLabel="Usuário"
      />,
    );
    expect(container.querySelector(".delpi-ui-topbar-user--loading")).toBeTruthy();
    expect(screen.getByText("Usuário")).toBeTruthy();
  });

  it("factory injeta classNames", () => {
    const Identity = createDashboardTopBarUserIdentity({ prefix: "ds" });
    const { container } = render(<Identity displayName="Bia" />);
    expect(container.querySelector(".ds-topbar-user")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-topbar-user")).toBeTruthy();
  });
});
