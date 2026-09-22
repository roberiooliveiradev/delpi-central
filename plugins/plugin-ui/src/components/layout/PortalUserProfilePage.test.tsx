import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  PORTAL_USER_PROFILE_LABELS_PT,
  PortalUserProfilePage,
  createDashboardPortalUserProfilePage,
  portalUserProfileAccessBemClasses,
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
    expect(code).not.toMatch(/permission|capabilit|jwt/i);
    expect(code).not.toMatch(/keycloak/i);
  });

  it("força density comfortable no Hero", () => {
    expect(code).toMatch(/density="comfortable"/);
    const { container } = render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        hero={{ title: "Ana Souza" }}
      />,
    );
    expect(container.querySelector('[data-density="comfortable"]')).toBeTruthy();
    expect(container.querySelector('[data-density="compact"]')).toBeNull();
  });

  it("renderiza identidade somente leitura com contatos e helper canônico", () => {
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
        }}
      />,
    );

    expect(screen.getByRole("region", { name: "Perfil do usuário" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Identidade" })).toBeTruthy();
    expect(screen.getByText("ana@delpi.com.br")).toBeTruthy();
    expect(screen.getByText("Compradora")).toBeTruthy();
    expect(screen.getByText("+551130000000")).toBeTruthy();
    expect(screen.getByText("+5511999990000")).toBeTruthy();
    expect(screen.getByText(PORTAL_USER_PROFILE_LABELS_PT.identityHostNote)).toBeTruthy();
    expect(screen.queryByText("(/profile)")).toBeNull();
    /** Chave ausente → linha omitida. */
    expect(screen.queryByText("Celular")).toBeNull();
    expect(screen.queryAllByRole("textbox")).toHaveLength(0);
  });

  it("mostra «Não informado» quando a chave de contato existe e o valor é vazio", () => {
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        identity={{
          name: "Ana Souza",
          jobTitle: null,
          phone: "",
          mobile: undefined,
          whatsapp: null,
        }}
      />,
    );

    expect(screen.getByText("Cargo")).toBeTruthy();
    expect(screen.getByText("Telefone")).toBeTruthy();
    expect(screen.getByText("Celular")).toBeTruthy();
    expect(screen.getByText("WhatsApp")).toBeTruthy();
    expect(screen.getAllByText("Não informado").length).toBeGreaterThanOrEqual(4);
  });

  it("injeta badge Você e CTA Editar no Meu Perfil só quando isSelf", () => {
    const onEditSelf = vi.fn();
    const { rerender } = render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        isSelf
        onEditSelf={onEditSelf}
        hero={{ title: "Ana Souza" }}
        contextBadges={<span>Filiais: 01</span>}
      />,
    );

    expect(screen.getByText("Você")).toBeTruthy();
    expect(screen.getByText("Filiais: 01")).toBeTruthy();
    const edit = screen.getByRole("button", { name: "Editar no Meu Perfil" });
    fireEvent.click(edit);
    expect(onEditSelf).toHaveBeenCalledTimes(1);

    rerender(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        isSelf={false}
        onEditSelf={onEditSelf}
        hero={{ title: "Outro" }}
        contextBadges={<span>Filiais: 01</span>}
      />,
    );
    expect(screen.queryByText("Você")).toBeNull();
    expect(screen.queryByRole("button", { name: "Editar no Meu Perfil" })).toBeNull();
    expect(screen.getByText("Filiais: 01")).toBeTruthy();
  });

  it("não inventa badge Diretório / Leitura admin", () => {
    expect(code).not.toMatch(/Diretório|Leitura admin/);
    render(
      <PortalUserProfilePage
        classNames={CLASS_NAMES}
        isSelf={false}
        hero={{ title: "Outro" }}
      />,
    );
    expect(screen.queryByText("Diretório")).toBeNull();
    expect(screen.queryByText("Leitura admin")).toBeNull();
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
    expect(screen.getByRole("heading", { name: "Identidade" })).toBeTruthy();
  });

  it("access BEM dual-class é canônico para chrome de Acesso", () => {
    const access = portalUserProfileAccessBemClasses("cm");
    expect(access.access).toContain("delpi-ui-portal-user-profile__access");
    expect(access.accessList).toContain(
      "delpi-ui-portal-user-profile__access-list",
    );
    expect(access.accessBadges).toContain(
      "delpi-ui-portal-user-profile__access-badges",
    );
  });
});
