import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MessageThread, messageThreadBemClasses } from "./MessageThread";

const classNames = messageThreadBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

afterEach(() => {
  cleanup();
});

describe("MessageThread", () => {
  it("shows empty state", () => {
    render(
      <MessageThread
        classNames={classNames}
        messages={[]}
        listAriaLabel="Messages"
        emptyLabel="No messages yet"
      />,
    );
    expect(screen.getByRole("status").textContent).toBe("No messages yet");
  });

  it("renders text bubbles and system lines with reply indent", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hello @Ana",
            authorName: "Bruno",
            createdAtLabel: "10:00",
            mentions: [{ kind: "user", label: "@Ana" }],
          },
          {
            id: "2",
            kind: "system",
            bodyText: "Room created",
            createdAtLabel: "10:01",
          },
          {
            id: "3",
            kind: "text",
            bodyText: "Reply",
            authorName: "Ana",
            createdAtLabel: "10:02",
            parentId: "1",
          },
        ]}
      />,
    );
    expect(screen.getAllByText(/Hello/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Bruno").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Room created")).toBeTruthy();
    expect(container.querySelector('[data-message-id="1"]')).not.toBeNull();
    expect(container.querySelector('[data-message-id="2"]')).not.toBeNull();
    expect(container.querySelector(".delpi-ui-message-thread__item--reply")).not.toBeNull();
    expect(container.querySelector(".delpi-ui-mention-text__chip")).not.toBeNull();
  });

  it("aligns mine bubbles to the right without system avatar", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Mine",
            authorName: "Eu",
            createdAtLabel: "10:00",
            mine: true,
          },
          {
            id: "2",
            kind: "system",
            bodyText: "Pinned",
            createdAtLabel: "10:01",
            mine: true,
          },
        ]}
      />,
    );
    expect(container.querySelector(".delpi-ui-message-thread__item--mine")).not.toBeNull();
    expect(container.querySelector(".delpi-ui-message-thread__bubble--mine")).not.toBeNull();
    expect(
      container.querySelector('[data-message-kind="text"] .delpi-ui-avatar'),
    ).toBeNull();
    expect(
      container.querySelector('[data-message-kind="system"] .delpi-ui-avatar'),
    ).toBeNull();
  });

  it("exposes host actions on bubbles", () => {
    const onDelete = vi.fn();
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hi",
            authorName: "Bruno",
            createdAtLabel: "10:00",
          },
        ]}
        resolveActions={() => [
          { id: "delete", label: "Delete", onClick: onDelete, danger: true },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it("exposes icon actions by accessible name without permanent text", () => {
    const onPin = vi.fn();
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hi",
            authorName: "Bruno",
            createdAtLabel: "10:00",
          },
        ]}
        resolveActions={() => [
          {
            id: "pin",
            label: "Pin message",
            title: "Pin message",
            icon: <span>📌</span>,
            onClick: onPin,
          },
        ]}
      />,
    );
    expect(screen.queryByText("Pin message")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Pin message" }));
    expect(onPin).toHaveBeenCalledTimes(1);
  });

  it("coloca nome e hora acima da bolha e o contexto citado dentro dela", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Pergunta original",
            authorName: "Bruno Costa",
            authorUserId: "u1",
            createdAtLabel: "19/08, 14:27",
          },
          {
            id: "2",
            kind: "text",
            bodyText: "blz então",
            authorName: "Eu",
            authorUserId: "u2",
            createdAtLabel: "19/08, 14:28",
            mine: true,
            parentId: "1",
          },
        ]}
      />,
    );
    expect(screen.getAllByText("Bruno Costa").length).toBeGreaterThanOrEqual(1);
    const headingTime = container.querySelector(
      ".delpi-ui-message-thread__item--mine .delpi-ui-message-thread__meta time",
    );
    expect(headingTime?.textContent).toBe("19/08, 14:28");
    expect(container.querySelector("article footer time")).toBeNull();
    expect(container.querySelector("blockquote")?.textContent).toMatch(/Pergunta original/);
    expect(container.querySelector(".delpi-ui-message-thread__quote-author")?.textContent).toBe(
      "Bruno Costa",
    );
  });

  it("agrupa mensagens seguidas do mesmo autor sem repetir nome e avatar", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "bom dia.",
            authorName: "Bruno Costa",
            authorUserId: "u1",
            createdAtLabel: "07:43",
          },
          {
            id: "2",
            kind: "text",
            bodyText: "segunda linha",
            authorName: "Bruno Costa",
            authorUserId: "u1",
            createdAtLabel: "07:44",
          },
        ]}
      />,
    );
    expect(screen.getAllByText("Bruno Costa")).toHaveLength(1);
    expect(container.querySelectorAll(".delpi-ui-avatar")).toHaveLength(1);
    expect(container.querySelector(".delpi-ui-message-thread__item--continue")).not.toBeNull();
  });

  it("avatar do autor vira link quando há href e title", () => {
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hi",
            authorName: "Bruno Costa",
            authorUserId: "u1",
            createdAtLabel: "10:00",
            authorHref: "/apps/commercial/users/u1",
            authorLinkTitle: "Abrir perfil de Bruno Costa",
          },
        ]}
      />,
    );
    expect(
      screen.getByRole("link", { name: "Abrir perfil de Bruno Costa" }).getAttribute("href"),
    ).toBe("/apps/commercial/users/u1");
  });

  it("usa a foto do autor quando authorSrc está definido", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hi",
            authorName: "Bruno Costa",
            authorUserId: "u1",
            createdAtLabel: "10:00",
            authorSrc: "blob:photo-bruno",
          },
        ]}
      />,
    );
    expect(container.querySelector("img")?.getAttribute("src")).toBe("blob:photo-bruno");
  });

  it("coloca a barra de ações fora do article da bolha", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hi",
            authorName: "Bruno",
            createdAtLabel: "10:00",
          },
        ]}
        resolveActions={() => [
          { id: "delete", label: "Delete", onClick: vi.fn(), danger: true },
        ]}
      />,
    );
    const article = container.querySelector("article");
    const actions = container.querySelector(".delpi-ui-message-thread__actions");
    const cluster = container.querySelector(".delpi-ui-message-thread__cluster");
    expect(article).not.toBeNull();
    expect(actions).not.toBeNull();
    expect(cluster).not.toBeNull();
    const stack = container.querySelector(".delpi-ui-message-thread__stack");
    expect(article?.contains(actions)).toBe(false);
    expect(cluster?.contains(actions)).toBe(true);
    expect(stack?.contains(actions)).toBe(true);
    expect(cluster?.contains(article)).toBe(true);
  });
});

describe("message-thread.css host scroll", () => {
  it("rola no host: lista overflow visible e teto na bolha", () => {
    const css = readFileSync(join(stylesDir, "message-thread.css"), "utf8");
    const root = css.match(/\.delpi-ui-message-thread \{[^}]+\}/)?.[0] ?? "";
    const row = css.match(/\.delpi-ui-message-thread__row \{[^}]+\}/)?.[0] ?? "";
    const bubble = css.match(/\.delpi-ui-message-thread__bubble \{[^}]+\}/)?.[0] ?? "";
    const cluster = css.match(/\.delpi-ui-message-thread__cluster \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/overflow:\s*visible;/);
    expect(root).not.toMatch(/overflow-y:\s*auto;/);
    expect(row).toMatch(/width:\s*max-content;/);
    expect(row).toMatch(/max-width:\s*min\(92%,\s*56rem\)/);
    expect(row).toMatch(/align-items:\s*flex-start;/);
    expect(row).toMatch(/gap:\s*0\.5rem;/);
    expect(cluster).toMatch(/max-width:\s*none;/);
    expect(cluster).not.toMatch(/width:\s*fit-content;/);
    expect(cluster).not.toMatch(/padding-top:\s*2\.75rem;/);
    expect(bubble).toMatch(/width:\s*100%;/);
    expect(bubble).toMatch(/max-width:\s*none;/);
    expect(bubble).not.toMatch(/min\(75%/);
    expect(bubble).toMatch(/border:\s*none;/);
    expect(bubble).not.toMatch(/border:\s*1px/);
    const mine = css.match(/\.delpi-ui-message-thread__bubble--mine \{[^}]+\}/)?.[0] ?? "";
    expect(mine).toMatch(/22%/);
    const actions = css.match(/\.delpi-ui-message-thread__actions \{[^}]+\}/)?.[0] ?? "";
    expect(actions).toMatch(/position:\s*absolute;/);
    expect(actions).toMatch(/translateY\(-50%\)/);
    expect(css).not.toMatch(/opacity 0\.15s ease 0\.45s/);
    expect(css).toMatch(/transition:\s*opacity 0\.1s ease;/);
    expect(css).toMatch(/box-shadow:\s*none;/);
  });
});
