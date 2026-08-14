import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  InitialsAvatar,
  hueFromKey,
  initialsAvatarBemClasses,
  initialsFromName,
} from "./InitialsAvatar";

afterEach(() => {
  cleanup();
});

describe("initialsFromName / hueFromKey", () => {
  it("deriva iniciais de um ou dois nomes", () => {
    expect(initialsFromName("Acme")).toBe("AC");
    expect(initialsFromName("Acme Indústria")).toBe("AI");
    expect(initialsFromName("  ")).toBe("?");
  });

  it("hue determinístico pela chave", () => {
    expect(hueFromKey("01|01")).toBe(hueFromKey("01|01"));
    expect(hueFromKey("01|01")).not.toBe(hueFromKey("02|01"));
  });
});

describe("InitialsAvatar", () => {
  const classNames = initialsAvatarBemClasses("pva");

  it("emite dual-class e iniciais sem src", () => {
    render(<InitialsAvatar name="Acme Indústria" classNames={classNames} size="md" />);
    const el = document.querySelector(".delpi-ui-avatar");
    expect(el?.className).toContain("pva-avatar");
    expect(el?.className).toContain("delpi-ui-avatar--md");
    expect(el?.textContent).toBe("AI");
  });

  it("com src previewable abre lightbox ao clicar", () => {
    const host = document.createElement("main");
    host.className = "dashboard-commercial";
    document.body.appendChild(host);
    const mount = document.createElement("div");
    host.appendChild(mount);

    render(
      <InitialsAvatar
        name="Acme"
        src="blob:test"
        alt="Foto"
        classNames={classNames}
        size="lg"
        portalScopeClassName="dashboard-commercial"
      />,
      { container: mount },
    );

    const trigger = screen.getByRole("button", { name: "Ampliar foto de Acme" });
    expect(trigger.className).toContain("delpi-ui-avatar--previewable");
    fireEvent.click(trigger);
    expect(screen.getByRole("dialog", { name: "Acme" })).toBeTruthy();
    expect(screen.getByRole("img", { name: "Acme" }).getAttribute("src")).toBe("blob:test");

    host.remove();
  });

  it("previewable=false mantém img sem lightbox", () => {
    render(
      <InitialsAvatar
        name="Acme"
        src="blob:test"
        alt="Foto"
        classNames={classNames}
        previewable={false}
      />,
    );
    const img = screen.getByRole("img", { name: "Foto" });
    expect(img.getAttribute("src")).toBe("blob:test");
    expect(screen.queryByRole("button", { name: /Ampliar foto/i })).toBeNull();
  });

  it("stopPropagation no clique previewável", () => {
    const parentClick = vi.fn();
    render(
      <div onClick={parentClick}>
        <InitialsAvatar name="Acme" src="blob:test" classNames={classNames} />
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Ampliar foto/i }));
    expect(parentClick).not.toHaveBeenCalled();
  });

  it("com href renderiza link sem lightbox e chama onNavigate", () => {
    const onNavigate = vi.fn((event: { preventDefault: () => void }) => {
      event.preventDefault();
    });
    const parentClick = vi.fn();
    render(
      <div onClick={parentClick}>
        <InitialsAvatar
          name="Acme"
          classNames={classNames}
          href="/apps/commercial/customers/1/01"
          title="Abrir conta de Acme"
          onNavigate={onNavigate}
        />
      </div>,
    );
    const link = screen.getByRole("link", { name: "Abrir conta de Acme" });
    expect(link.getAttribute("href")).toBe("/apps/commercial/customers/1/01");
    expect(link.getAttribute("title")).toBe("Abrir conta de Acme");
    expect(screen.queryByRole("button", { name: /Ampliar/i })).toBeNull();
    fireEvent.click(link);
    expect(onNavigate).toHaveBeenCalledTimes(1);
    expect(parentClick).not.toHaveBeenCalled();
  });

  it("href com foto não abre lightbox", () => {
    render(
      <InitialsAvatar
        name="Acme"
        src="blob:test"
        classNames={classNames}
        href="/apps/commercial/customers/1/01"
        title="Abrir conta de Acme"
      />,
    );
    expect(screen.getByRole("link", { name: "Abrir conta de Acme" })).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
