import { useMemo } from "react";
import { ArrowLeft, Plus } from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { CATALOG_CREATE } from "../../constants/catalogRoutes";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  buildFilialPath,
  buildRecursoPath,
  buildSetorPath,
  type ParsedTransformometroRoute,
} from "../../utils/routeParser";
import { FiliaisPage } from "./FiliaisPage";
import { FilialDetailPage } from "./FilialDetailPage";
import { RecursosPage } from "./RecursosPage";
import { RecursoDetailPage } from "./RecursoDetailPage";
import { SetoresPage } from "./SetoresPage";
import { SetorDetailPage } from "./SetorDetailPage";
import {
  ConfiguracoesWorkspaceShell,
  useRecursoWorkspaceSection,
} from "../configuracoes/ConfiguracoesWorkspaceShell";
import {
  buildConfiguracoesSectionPath,
  parseConfiguracoesSectionFromPath,
  resolveActiveConfiguracoesNodeId,
  type ConfiguracoesSectionId,
} from "../configuracoes/configuracoesWorkspaceNav";

type Props = Pick<AppProps, "getAccessToken"> & {
  route: ParsedTransformometroRoute;
  pathname?: string;
  onNavigate: (path: string) => void;
};

function sectionFromRoute(route: ParsedTransformometroRoute, pathname: string): ConfiguracoesSectionId {
  if (route.view === "filial") return "unidades";
  if (route.view === "setor") return "departamentos";
  if (route.view === "recurso") return "recursos";
  return parseConfiguracoesSectionFromPath(pathname);
}

export function isConfiguracoesWorkspaceRoute(route: ParsedTransformometroRoute): boolean {
  return (
    route.view === "configuracoes" ||
    route.view === "filial" ||
    route.view === "setor" ||
    route.view === "recurso"
  );
}

export function ConfiguracoesWorkspacePage({ getAccessToken, route, pathname, onNavigate }: Props) {
  const section = sectionFromRoute(route, pathname ?? "");
  const activeRecursoSection = useRecursoWorkspaceSection();

  const activeNodeId = useMemo(
    () =>
      resolveActiveConfiguracoesNodeId({
        view:
          route.view === "configuracoes"
            ? "configuracoes"
            : (route.view as "filial" | "setor" | "recurso"),
        section,
        filialId: route.filialId,
        setorId: route.setorId,
        recursoId: route.recursoId,
        recursoSection: activeRecursoSection,
      }),
    [
      activeRecursoSection,
      route.filialId,
      route.recursoId,
      route.setorId,
      route.view,
      section,
    ]
  );

  const sidebarActions = useMemo(() => {
    if (section === "unidades" && route.view !== "filial") {
      return (
        <button
          type="button"
          className="ds-primary-btn tm-processo-workspace-sidebar__action-btn"
          onClick={() => onNavigate(buildFilialPath(CATALOG_CREATE.filial))}
        >
          <Plus size={16} />
          Nova unidade
        </button>
      );
    }
    if (section === "departamentos" && route.view !== "setor") {
      return (
        <button
          type="button"
          className="ds-primary-btn tm-processo-workspace-sidebar__action-btn"
          onClick={() => onNavigate(buildSetorPath(CATALOG_CREATE.setor))}
        >
          <Plus size={16} />
          Novo departamento
        </button>
      );
    }
    if (section === "recursos" && route.view !== "recurso") {
      return (
        <button
          type="button"
          className="ds-primary-btn tm-processo-workspace-sidebar__action-btn"
          onClick={() => onNavigate(buildRecursoPath(CATALOG_CREATE.recurso))}
        >
          <Plus size={16} />
          Novo recurso
        </button>
      );
    }
    return null;
  }, [onNavigate, route.view, section]);

  const backAction =
    route.view === "filial" && route.filialId ? (
      <button
        type="button"
        className="ds-ghost-btn tm-processo-workspace-sidebar__action-btn"
        onClick={() => onNavigate(buildConfiguracoesSectionPath("unidades"))}
      >
        <ArrowLeft size={16} />
        Unidades
      </button>
    ) : route.view === "setor" && route.setorId ? (
      <button
        type="button"
        className="ds-ghost-btn tm-processo-workspace-sidebar__action-btn"
        onClick={() => onNavigate(buildConfiguracoesSectionPath("departamentos"))}
      >
        <ArrowLeft size={16} />
        Departamentos
      </button>
    ) : route.view === "recurso" && route.recursoId ? (
      <button
        type="button"
        className="ds-ghost-btn tm-processo-workspace-sidebar__action-btn"
        onClick={() => onNavigate(buildConfiguracoesSectionPath("recursos"))}
      >
        <ArrowLeft size={16} />
        Recursos
      </button>
    ) : null;

  function renderMain() {
    if (route.view === "filial" && route.filialId) {
      return (
        <FilialDetailPage
          embedded
          getAccessToken={getAccessToken}
          filialId={route.filialId}
          pathname={pathname}
          onNavigate={onNavigate}
          onBack={() => onNavigate(buildConfiguracoesSectionPath("unidades"))}
        />
      );
    }
    if (route.view === "setor" && route.setorId) {
      return (
        <SetorDetailPage
          embedded
          getAccessToken={getAccessToken}
          setorId={route.setorId}
          pathname={pathname}
          onNavigate={onNavigate}
          onBack={() => onNavigate(buildConfiguracoesSectionPath("departamentos"))}
        />
      );
    }
    if (route.view === "recurso" && route.recursoId) {
      return (
        <RecursoDetailPage
          embedded
          activeSection={activeRecursoSection}
          getAccessToken={getAccessToken}
          recursoId={route.recursoId}
          pathname={pathname}
          onNavigate={onNavigate}
          onBack={() => onNavigate(buildConfiguracoesSectionPath("recursos"))}
        />
      );
    }
    if (section === "departamentos") {
      return (
        <SetoresPage embedded getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
      );
    }
    if (section === "recursos") {
      return (
        <RecursosPage embedded getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
      );
    }
    return (
      <FiliaisPage embedded getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
    );
  }

  return (
    <TransformometroShell>
      <PageHeader
        title="Configurações"
        subtitle="Unidades, departamentos e recursos compartilhados usados nos processos e no dashboard"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.configuracoesUnidades}
        onNavigate={onNavigate}
      />

      <ConfiguracoesWorkspaceShell
        activeNodeId={activeNodeId}
        getAccessToken={getAccessToken}
        onNavigate={onNavigate}
        backActions={backAction}
        footerActions={sidebarActions}
      >
        {renderMain()}
      </ConfiguracoesWorkspaceShell>
    </TransformometroShell>
  );
}
