import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { AvatarStack, avatarStackBemClasses } from "./AvatarStack";

const classNames = avatarStackBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("AvatarStack", () => {
  it("mostra até max avatares e +N no overflow", () => {
    const { container } = render(
      <AvatarStack
        classNames={classNames}
        max={2}
        items={[
          { id: "1", name: "Ana Silva" },
          { id: "2", name: "Bruno Costa" },
          { id: "3", name: "Carla Dias" },
        ]}
      />,
    );
    const list = within(container).getByLabelText("Membros");
    expect(list.querySelectorAll("li")).toHaveLength(3);
    expect(within(list).getByLabelText("Mais 1").textContent?.replace(/\s+/g, "")).toBe("+1");
  });

  it("sem overflow não renderiza +N", () => {
    const { container } = render(
      <AvatarStack
        classNames={classNames}
        max={5}
        items={[{ id: "1", name: "Ana" }]}
      />,
    );
    expect(within(container).queryByLabelText(/Mais/)).toBeNull();
  });

  it("com href+title cada face é link", () => {
    render(
      <AvatarStack
        classNames={classNames}
        items={[
          {
            id: "1",
            name: "Ana",
            href: "/apps/commercial/users/u1",
            title: "Abrir perfil de Ana",
          },
        ]}
      />,
    );
    const link = screen.getByRole("link", { name: "Abrir perfil de Ana" });
    expect(link.getAttribute("href")).toBe("/apps/commercial/users/u1");
  });
});
