import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  PortalUserProfilePage,
  createDashboardPortalUserProfilePage,
  portalUserProfilePageBemClasses,
} from "./PortalUserProfilePage";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "PortalUserProfilePage.tsx"), "utf8");
/** Comentários declaram o que o kit NÃO faz; a asserção olha só o código. */
const code = source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");

const CLASS_NAMES = portalUserProfilePageBemClasses("ds");

const PAGE_PATH = {
  back: { label: "Voltar", href: "/apps/demo" },
  current: "Ana Souza",
};

afterEach(() => {
  cleanup();
});

describe("PortalUserProfilePage", () => {
  it("é presentation-only: sem HTTP, AuthZ ou domínio de portal", () => {
    expect(code).not.toMatch(/\bfetch\(/);
    expect(code).not.toMatch(/localStorage|sessionStorage|axios/);
    expect(code).not.toMatch(/commercial|transformometro|supplies/i);
    expect(code).not.toMatch(/\/apps\//);
    expect(code).not.toMatch(/isSelf|permission|capabilit/i);
  });

  it("renderiza identidade somente leitura com contatos e nota", () => {
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        pagePath={PAGE_PATH}
        hero={{ eyebrow: "Portal Demo", title: "Ana Souza" }}
        identity={{
          name: "Ana Souza",
          email: "ana@delpi.com.br",
          jobTitle: "Compradora",
          phone: "+551130000000",
          whatsapp: "+5511999990000",
          note: "Editar identidade no Meu Perfil.",
          actions: <button type="button">Editar identidade</button>,
        }}
      />,
    );

    /** Região nomeada — `aria-label` em div genérica seria ignorada pelo leitor. */
    expect(screen.getByRole("region", { name: "Perfil do usuário" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Identidade" })).toBeTruthy();
    expect(screen.getByText("ana@delpi.com.br")).toBeTruthy();
    expect(screen.getByText("Compradora")).toBeTruthy();
    expect(screen.getByText("+551130000000")).toBeTruthy();
    expect(screen.getByText("+5511999990000")).toBeTruthy();
    expect(screen.getByText("Editar identidade no Meu Perfil.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Editar identidade" })).toBeTruthy();
    /** Sem valor de celular e sem `showEmptyFields` → linha omitida. */
    expect(screen.queryByText("Celular")).toBeNull();
    /** Identidade não tem campos editáveis no kit. */
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
  });

  it("mostra `—` nos contatos vazios quando o host pede showEmptyFields", () => {
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        identity={{ name: "Ana Souza", showEmptyFields: true }}
      />,
    );

    expect(screen.getByText("Celular")).toBeTruthy();
    expect(screen.getAllByText("—").length).toBeGreaterThan(1);
  });

  it("dispara onSelect do atalho clicado", () => {
    const onHome = vi.fn();
    const onTasks = vi.fn();
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        shortcuts={[
          { id: "home", label: "Início", onSelect: onHome },
          { id: "tasks", label: "Minhas tarefas", onSelect: onTasks },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Minhas tarefas" }));
    expect(onTasks).toHaveBeenCalledTimes(1);
    expect(onHome).not.toHaveBeenCalled();
  });

  it("loading substitui o corpo e mantém o caminho navegável", () => {
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        pagePath={PAGE_PATH}
        loading
        loadingNode={<p>Carregando perfil…</p>}
        hero={{ title: "Ana Souza" }}
        identity={{ name: "Ana Souza" }}
        shortcuts={[{ id: "home", label: "Início", onSelect: () => {} }]}
      />,
    );

    expect(screen.getByText("Carregando perfil…")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Voltar" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Identidade" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Início" })).toBeNull();
  });

  it("erro do host é anunciado como alert", () => {
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        error={<span>Não foi possível abrir o perfil.</span>}
      />,
    );

    expect(screen.getByRole("alert").textContent).toContain(
      "Não foi possível abrir o perfil.",
    );
  });

  it("hospeda seções de domínio do portal", () => {
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        identity={{ name: "Ana Souza" }}
        sections={<section>Preferências do portal</section>}
      />,
    );

    expect(screen.getByText("Preferências do portal")).toBeTruthy();
  });

  it("factory aplica prefixo do portal e labels sobrescritas", () => {
    const DemoProfilePage = createDashboardPortalUserProfilePage({
      prefix: "sp",
      labels: { shortcutsTitle: "Atalhos do Portal" },
    });
    const { container } = render(
      <DemoProfilePage
        identity={{ name: "Ana Souza" }}
        shortcuts={[{ id: "home", label: "Início", onSelect: () => {} }]}
      />,
    );

    expect(container.querySelector(".sp-portal-user-profile")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-portal-user-profile")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Atalhos do Portal" })).toBeTruthy();
    /** Rótulos não sobrescritos herdam o bundle PT do kit. */
    expect(screen.getByRole("heading", { name: "Identidade" })).toBeTruthy();
  });
});
