import { cleanup, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";

import { TaskWorkspacePage } from "./TaskWorkspacePage";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "TaskWorkspacePage.tsx"), "utf8");

afterEach(() => {
  cleanup();
});

describe("TaskWorkspacePage", () => {
  it("é chrome de composição sem fetch nem domínio", () => {
    expect(source).toMatch(/TaskWorklistSection/);
    expect(source).not.toMatch(/\bfetch\(/);
    expect(source).not.toMatch(/commercial|transformometro|supplies/i);
    expect(source).not.toMatch(/localStorage|axios/);
  });

  it("monta hero, worklist, empty/items e editor opcional", () => {
    render(
      <TaskWorkspacePage
        hero={<header>Hero Minhas tarefas</header>}
        worklist={{
          title: "Fila",
          subtitle: "Recorte",
          actions: <button type="button">Nova tarefa</button>,
          search: <input aria-label="Buscar tarefas" />,
        }}
        editor={<section>Editor</section>}
      >
        <p>itens</p>
      </TaskWorkspacePage>,
    );
    expect(screen.getByText("Hero Minhas tarefas")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Fila" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Nova tarefa" })).toBeTruthy();
    expect(screen.getByLabelText("Buscar tarefas")).toBeTruthy();
    expect(screen.getByText("itens")).toBeTruthy();
    expect(screen.getByText("Editor")).toBeTruthy();
  });

  it("suporta página sem scope/create/editor/filters", () => {
    render(
      <TaskWorkspacePage
        hero={<header>Só hero</header>}
        worklist={{ title: "Fila" }}
      >
        <p>conteúdo mínimo</p>
      </TaskWorkspacePage>,
    );
    expect(screen.getByText("Só hero")).toBeTruthy();
    expect(screen.getByText("conteúdo mínimo")).toBeTruthy();
    expect(screen.queryByText("Editor")).toBeNull();
  });

  it("initialLoading substitui fila e editor", () => {
    render(
      <TaskWorkspacePage
        hero={<header>Hero</header>}
        worklist={{ title: "Fila" }}
        initialLoading={<p>Carregando…</p>}
        editor={<section>Editor oculto</section>}
      >
        <p>itens ocultos</p>
      </TaskWorkspacePage>,
    );
    expect(screen.getByText("Carregando…")).toBeTruthy();
    expect(screen.queryByText("itens ocultos")).toBeNull();
    expect(screen.queryByText("Editor oculto")).toBeNull();
    expect(screen.queryByRole("heading", { name: "Fila" })).toBeNull();
  });

  it("mostra partial error, fatal error e refreshing", () => {
    render(
      <TaskWorkspacePage
        hero={<header>Hero</header>}
        worklist={{ title: "Fila" }}
        partialError={<span>Fonte parcial falhou</span>}
        error={
          <span>
            Falha fatal{" "}
            <button type="button">Tentar de novo</button>
          </span>
        }
        refreshing
        refreshingLabel="Atualizando…"
      >
        <p>itens</p>
      </TaskWorkspacePage>,
    );
    expect(screen.getByText("Fonte parcial falhou")).toBeTruthy();
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tentar de novo" })).toBeTruthy();
    expect(screen.getByText("Atualizando…")).toBeTruthy();
    expect(screen.getByText("itens")).toBeTruthy();
  });
});
