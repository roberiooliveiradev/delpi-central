import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

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

  it("renderiza img quando há src", () => {
    render(
      <InitialsAvatar
        name="Acme"
        src="blob:test"
        alt="Foto"
        classNames={classNames}
        size="lg"
      />,
    );
    const img = screen.getByRole("img", { name: "Foto" });
    expect(img.getAttribute("src")).toBe("blob:test");
    expect(img.className).toContain("delpi-ui-avatar--lg");
  });
});
