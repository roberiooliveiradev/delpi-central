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
import { BranchesPage } from "./BranchesPage";
import { BranchDetailPage } from "./BranchDetailPage";
import { SharedResourcesPage } from "./SharedResourcesPage";
import { SharedResourceDetailPage } from "./SharedResourceDetailPage";
import { DepartmentsPage } from "./DepartmentsPage";
import { DepartmentDetailPage } from "./DepartmentDetailPage";
import {
  SettingsWorkspaceShell,
  useRecursoWorkspaceSection,
} from "../settings/SettingsWorkspaceShell";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import {
  buildSettingsSectionPath,
  parseSettingsSectionFromPath,
  resolveActiveSettingsNodeId,
  type SettingsSectionId,
} from "../settings/settingsWorkspaceNav";

type Props = Pick<AppProps, "getAccessToken"> & {
  route: ParsedTransformometroRoute;
  pathname?: string;
  onNavigate: (path: string) => void;
};

function sectionFromRoute(route: ParsedTransformometroRoute, pathname: string): SettingsSectionId {
  if (route.view === "filial") return "unidades";
  if (route.view === "setor") return "departamentos";
  if (route.view === "recurso") return "recursos";
  return parseSettingsSectionFromPath(pathname);
}

export function isSettingsWorkspaceRoute(route: ParsedTransformometroRoute): boolean {
  return (
    route.view === "configuracoes" ||
    route.view === "filial" ||
    route.view === "setor" ||
    route.view === "recurso"
  );
}

export function SettingsWorkspacePage({ getAccessToken, route, pathname, onNavigate }: Props) {
  const section = sectionFromRoute(route, pathname ?? "");
  const activeRecursoSection = useRecursoWorkspaceSection();

  const activeNodeId = useMemo(
    () =>
      resolveActiveSettingsNodeId({
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
        className={`${DS_GHOST_BTN} tm-processo-workspace-sidebar__action-btn`}
        onClick={() => onNavigate(buildSettingsSectionPath("unidades"))}
      >
        <ArrowLeft size={16} />
        Unidades
      </button>
    ) : route.view === "setor" && route.setorId ? (
      <button
        type="button"
        className={`${DS_GHOST_BTN} tm-processo-workspace-sidebar__action-btn`}
        onClick={() => onNavigate(buildSettingsSectionPath("departamentos"))}
      >
        <ArrowLeft size={16} />
        Departamentos
      </button>
    ) : route.view === "recurso" && route.recursoId ? (
      <button
        type="button"
        className={`${DS_GHOST_BTN} tm-processo-workspace-sidebar__action-btn`}
        onClick={() => onNavigate(buildSettingsSectionPath("recursos"))}
      >
        <ArrowLeft size={16} />
        Recursos
      </button>
    ) : null;

  function renderMain() {
    if (route.view === "filial" && route.filialId) {
      return (
        <BranchDetailPage
          embedded
          getAccessToken={getAccessToken}
          filialId={route.filialId}
          pathname={pathname}
          onNavigate={onNavigate}
          onBack={() => onNavigate(buildSettingsSectionPath("unidades"))}
        />
      );
    }
    if (route.view === "setor" && route.setorId) {
      return (
        <DepartmentDetailPage
          embedded
          getAccessToken={getAccessToken}
          setorId={route.setorId}
          pathname={pathname}
          onNavigate={onNavigate}
          onBack={() => onNavigate(buildSettingsSectionPath("departamentos"))}
        />
      );
    }
    if (route.view === "recurso" && route.recursoId) {
      return (
        <SharedResourceDetailPage
          embedded
          activeSection={activeRecursoSection}
          getAccessToken={getAccessToken}
          recursoId={route.recursoId}
          pathname={pathname}
          onNavigate={onNavigate}
          onBack={() => onNavigate(buildSettingsSectionPath("recursos"))}
        />
      );
    }
    if (section === "departamentos") {
      return (
        <DepartmentsPage embedded getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
      );
    }
    if (section === "recursos") {
      return (
        <SharedResourcesPage embedded getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
      );
    }
    return (
      <BranchesPage embedded getAccessToken={getAccessToken} pathname={pathname} onNavigate={onNavigate} />
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

      <SettingsWorkspaceShell
        activeNodeId={activeNodeId}
        getAccessToken={getAccessToken}
        onNavigate={onNavigate}
        backActions={backAction}
        footerActions={sidebarActions}
      >
        {renderMain()}
      </SettingsWorkspaceShell>
    </TransformometroShell>
  );
}
