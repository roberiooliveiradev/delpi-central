import { useEffect, type ReactNode } from "react";

import { configureHttpClient } from "./api/httpClient";
import { ReportsAppShell } from "./layout/ReportsAppShell";
import { CreateDefinitionPage } from "./pages/CreateDefinitionPage";
import { DefinitionDetailPage } from "./pages/DefinitionDetailPage";
import { DefinitionsListPage } from "./pages/DefinitionsListPage";
import { FollowUpNotesListPage } from "./pages/FollowUpNotesListPage";
import { FollowUpNotesPage } from "./pages/FollowUpNotesPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ReportsAccessDenied } from "./pages/ReportsAccessDenied";
import {
  REPORTS_FOLLOW_UP_LIST_PATH,
  resolveReportsRoute,
  type ReportsRoute,
} from "./utils/route";
import type { ReportsPermissionFlags } from "./utils/reportsPermissions";
import { useReportsPermissions } from "./utils/useReportsPermissions";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
  hasPermission?: (code: string) => boolean;
};

function isAdminRoute(route: ReportsRoute): boolean {
  return (
    route.kind === "overview" ||
    route.kind === "list" ||
    route.kind === "create" ||
    route.kind === "detail"
  );
}

function isFollowUpRoute(route: ReportsRoute): boolean {
  return route.kind === "followUpList" || route.kind === "followUp";
}

function redirectTo(href: string) {
  if (typeof window === "undefined") return;
  if (window.location.pathname === href) return;
  window.location.replace(href);
}

function resolveContent(
  route: ReportsRoute,
  flags: ReportsPermissionFlags,
): { content: ReactNode; nav: ReportsRoute["nav"] } {
  if (isAdminRoute(route) && !flags.canUseAdminNav) {
    if (flags.canUseFollowUpNav) {
      return {
        content: null,
        nav: "followUp",
      };
    }
    return {
      content: (
        <ReportsAccessDenied message="É necessário reports.view ou reports.manage para esta área." />
      ),
      nav: route.nav,
    };
  }

  if (isFollowUpRoute(route) && !flags.canUseFollowUpNav) {
    return {
      content: (
        <ReportsAccessDenied message="É necessário reports.notes.manage (ou permissão de administração) para acompanhamentos." />
      ),
      nav: route.nav,
    };
  }

  if (route.kind === "list") {
    return { content: <DefinitionsListPage />, nav: route.nav };
  }
  if (route.kind === "create") {
    return { content: <CreateDefinitionPage />, nav: route.nav };
  }
  if (route.kind === "detail") {
    return {
      content: <DefinitionDetailPage definitionId={route.definitionId} />,
      nav: route.nav,
    };
  }
  if (route.kind === "followUpList") {
    return { content: <FollowUpNotesListPage />, nav: route.nav };
  }
  if (route.kind === "followUp") {
    return {
      content: (
        <FollowUpNotesPage
          definitionId={route.definitionId}
          initialProductCode={route.productCode}
        />
      ),
      nav: route.nav,
    };
  }
  return { content: <OverviewPage />, nav: route.nav };
}

export default function App({
  getAccessToken,
  pathname,
  permissions,
  isSuperadmin,
  hasPermission,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  const route = resolveReportsRoute(pathname);
  const { flags, ready } = useReportsPermissions({
    permissions,
    isSuperadmin,
    hasPermission,
  });

  useEffect(() => {
    if (!ready) return;
    if (isAdminRoute(route) && !flags.canUseAdminNav && flags.canUseFollowUpNav) {
      redirectTo(REPORTS_FOLLOW_UP_LIST_PATH);
    }
  }, [ready, route, flags.canUseAdminNav, flags.canUseFollowUpNav]);

  if (!ready) {
    return (
      <ReportsAppShell
        nav={route.nav}
        canUseAdminNav={false}
        canUseFollowUpNav={false}
      >
        <div className="rp-page-content">
          <p className="rp-inline-note">Carregando permissões…</p>
        </div>
      </ReportsAppShell>
    );
  }

  const { content, nav } = resolveContent(route, flags);

  if (content === null) {
    return (
      <ReportsAppShell
        nav="followUp"
        canUseAdminNav={flags.canUseAdminNav}
        canUseFollowUpNav={flags.canUseFollowUpNav}
      >
        <div className="rp-page-content">
          <p className="rp-inline-note">Redirecionando para acompanhamentos…</p>
        </div>
      </ReportsAppShell>
    );
  }

  return (
    <ReportsAppShell
      nav={nav}
      canUseAdminNav={flags.canUseAdminNav}
      canUseFollowUpNav={flags.canUseFollowUpNav}
    >
      {content}
    </ReportsAppShell>
  );
}
