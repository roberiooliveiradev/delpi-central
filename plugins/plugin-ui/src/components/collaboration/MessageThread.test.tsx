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

  it("renders emptyContent slot when provided", () => {
    render(
      <MessageThread
        classNames={classNames}
        messages={[]}
        listAriaLabel="Messages"
        emptyLabel="No messages yet"
        emptyContent={
          <div role="status">
            <p>Pick a conversation</p>
          </div>
        }
      />,
    );
    expect(screen.getByText("Pick a conversation")).toBeTruthy();
    expect(screen.queryByText("No messages yet")).toBeNull();
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

  it("renders mentions inside system lines", () => {
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "sys-1",
            kind: "system",
            bodyText: "Tarefa criada: @Ana",
            createdAtLabel: "10:01",
            mentions: [
              {
                kind: "user",
                label: "@Ana",
                href: "/apps/commercial/users/u1",
                title: "Abrir Ana",
                avatarName: "Ana",
              },
            ],
          },
        ]}
      />,
    );
    const link = screen.getByRole("link", { name: "Abrir Ana" });
    expect(link.getAttribute("href")).toBe("/apps/commercial/users/u1");
    expect(link.className).toContain("with-avatar");
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
          {
            id: "delete",
            label: "Delete",
            danger: true,
            onClick: onDelete,
          },
        ]}
      />,
    );
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-message-thread__cluster")!);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it("renders resolveActionExtras before action buttons", () => {
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
        resolveActionExtras={() => (
          <span data-testid="reaction-extras">👍</span>
        )}
        resolveActions={() => [
          {
            id: "reply",
            label: "Reply",
            onClick: () => undefined,
          },
        ]}
      />,
    );
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-message-thread__cluster")!);
    const actions = document.body.querySelector(".delpi-ui-message-thread__actions");
    expect(actions).not.toBeNull();
    expect(screen.getByTestId("reaction-extras")).toBeTruthy();
    expect(actions?.querySelector(".delpi-ui-message-thread__actions-divider")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Reply" })).toBeTruthy();
  });

  it("swaps body for edit slot when editingId matches", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        editingId="1"
        renderEditSlot={() => <div data-testid="edit-slot">Editor</div>}
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Original",
            authorName: "Bruno",
            createdAtLabel: "10:00",
            mine: true,
          },
        ]}
        resolveActions={() => [
          { id: "edit", label: "Edit", onClick: () => undefined },
        ]}
      />,
    );
    expect(screen.getByTestId("edit-slot").textContent).toBe("Editor");
    expect(screen.queryByText("Original")).toBeNull();
    expect(screen.queryByRole("button", { name: "Edit" })).toBeNull();
    expect(container.querySelector(".delpi-ui-message-thread__item--editing")).not.toBeNull();
    expect(container.querySelector(".delpi-ui-message-thread__edit-slot")).not.toBeNull();
  });

  it("exposes icon actions by accessible name without permanent text", () => {
    const onPin = vi.fn();
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
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-message-thread__cluster")!);
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

  it("repete nome, avatar e horário em cada bloco do mesmo autor", () => {
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
    expect(screen.getAllByText("Bruno Costa")).toHaveLength(2);
    expect(container.querySelectorAll(".delpi-ui-avatar")).toHaveLength(2);
    expect(screen.getByText("07:43")).toBeTruthy();
    expect(screen.getByText("07:44")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-message-thread__item--continue")).toBeNull();
  });

  it("repete horário em cada bloco das próprias mensagens", () => {
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "a",
            authorName: "Eu",
            createdAtLabel: "15:11",
            mine: true,
          },
          {
            id: "2",
            kind: "text",
            bodyText: "b",
            authorName: "Eu",
            createdAtLabel: "15:12",
            mine: true,
          },
        ]}
      />,
    );
    expect(screen.getByText("15:11")).toBeTruthy();
    expect(screen.getByText("15:12")).toBeTruthy();
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

  it("coloca a barra de ações em portal no body (fora do scroll da thread)", () => {
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
    const cluster = container.querySelector(".delpi-ui-message-thread__cluster");
    expect(article).not.toBeNull();
    expect(cluster).not.toBeNull();
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-message-thread__cluster")!);
    const actionsInTree = container.querySelector(".delpi-ui-message-thread__actions");
    expect(actionsInTree).toBeNull();
    const actionsInBody = document.body.querySelector(".delpi-ui-message-thread__actions");
    expect(actionsInBody).not.toBeNull();
    expect(article?.contains(actionsInBody)).toBe(false);
    expect(cluster?.contains(article)).toBe(true);
  });

  it("renders markdown rich body with strong when not plain", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "md",
            kind: "text",
            bodyText: "**hello** and `code`",
            authorName: "Ana",
            createdAtLabel: "10:00",
          },
        ]}
      />,
    );
    const rich = container.querySelector(".delpi-ui-message-thread__body--rich");
    expect(rich).not.toBeNull();
    expect(rich?.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
    expect(rich?.innerHTML.toLowerCase()).toMatch(/<code\b/);
  });

  it("keeps MentionText for plain body with @mention", () => {
    render(
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
            mentions: [{ kind: "user", label: "Ana" }],
          },
        ]}
      />,
    );
    expect(screen.getByText("Ana").className).toMatch(/mention-text__chip/);
  });
});

describe("message-thread.css host scroll", () => {
  it("rola no host: overflow visible; toolbar via portal (sem abspos/padding gambiarra)", () => {
    const source = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "MessageThread.tsx"),
      "utf8",
    );
    expect(source).toMatch(/alignEnd=\{!message\.mine\}/);
    const css = readFileSync(join(stylesDir, "message-thread.css"), "utf8");
    const root = css.match(/\.delpi-ui-message-thread \{[^}]+\}/)?.[0] ?? "";
    const list = css.match(/\.delpi-ui-message-thread__list \{[^}]+\}/)?.[0] ?? "";
    const row = css.match(/\.delpi-ui-message-thread__row \{[^}]+\}/)?.[0] ?? "";
    const bubble = css.match(/\.delpi-ui-message-thread__bubble \{[^}]+\}/)?.[0] ?? "";
    const cluster = css.match(/\.delpi-ui-message-thread__cluster \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/overflow:\s*visible;/);
    expect(root).not.toMatch(/overflow-y:\s*auto;/);
    expect(list).toMatch(/padding:\s*0;/);
    expect(list).not.toMatch(/2\.75rem/);
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
    expect(mine).toMatch(/18%/);
    const actions = css.match(/\.delpi-ui-message-thread__actions \{[^}]+\}/)?.[0] ?? "";
    expect(actions).toMatch(/inline-flex/);
    expect(actions).toMatch(/flex-wrap:\s*nowrap/);
    expect(actions).toMatch(/width:\s*max-content/);
    expect(actions).toMatch(/max-width:\s*calc\(100vw - 1rem\)/);
    expect(actions).not.toMatch(/position:\s*absolute/);
    expect(actions).not.toMatch(/translateY/);
    expect(actions).not.toMatch(/bottom:\s*100%/);
    expect(css).not.toMatch(/opacity 0\.15s ease 0\.45s/);
    expect(css).not.toMatch(/cluster:hover \.delpi-ui-message-thread__actions/);
    expect(css).toMatch(/box-shadow:\s*none;/);
    expect(css).toMatch(/__body--rich/);
    expect(css).not.toMatch(/__body--rich code \{/);
    expect(css).not.toMatch(/__body--rich pre \{/);
    const prose = readFileSync(join(stylesDir, "collaboration-rich-prose.css"), "utf8");
    expect(prose).toMatch(/__body--rich code/);
    expect(prose).toMatch(/__body--rich pre/);
    expect(prose).toMatch(/__body--rich blockquote/);
  });

  it("cita reply clicável chama onParentQuoteClick", () => {
    const onParentQuoteClick = vi.fn();
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        onParentQuoteClick={onParentQuoteClick}
        messages={[
          {
            id: "parent-1",
            kind: "text",
            bodyText: "Original",
            authorName: "Ana",
            createdAtLabel: "10:00",
          },
          {
            id: "reply-1",
            kind: "text",
            bodyText: "Resposta",
            authorName: "Bruno",
            createdAtLabel: "10:01",
            parentId: "parent-1",
            mine: true,
          },
        ]}
      />,
    );
    const quote = screen.getByRole("button", { name: /Ana/i });
    fireEvent.click(quote);
    expect(onParentQuoteClick).toHaveBeenCalledWith("parent-1");
  });
});
