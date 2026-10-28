/** Base path canônico do plugin (manifest / Portal). */
export const CONTROLLERSHIP_FINANCE_BASE_PATH = "/apps/controllership-finance";

/**
 * Rotas implementadas:
 * - `home` — hub da Central de Fechamento.
 * - `financial_settlements` — baixas financeiras R01/R02 (closing).
 * - `stock_inventory` — estoque histórico R03/P7 (closing).
 * - `pendencies` — fila de pendências e classificações (P4).
 * - `packages` — pacotes por destinatário, submissão e revisão (P5).
 * - `cockpit` — estado consolidado P2/P3/P4/P5 da competência.
 * - `monthly_closing` — workspace «Fechamento mensal» (3 abas, doc 112).
 * - `my_tasks` — projeção self-only de pendências/revisões (P4/P5).
 * - `profile` — dados corporativos do próprio usuário (Core).
 * - `catalogs_admin` — catálogos governados P6 (MANAGE).
 * - `documents_admin` — catálogo mestre de documentos do fechamento
 *   (UX-012, MANAGE): listagem + cadastro/edição em páginas completas.
 * - `checklist_version` — detalhe contextual de uma versão do
 *   checklist mestre (UX-015): metadados, itens e ações por estado.
 * - `checklist_version_document` — documento dentro de uma versão
 *   histórica (UX-015): leitura contextual, edição prospectiva via
 *   catálogo mestre.
 * - `checklist_admin_events` — histórico/auditoria do template ou de
 *   uma versão em página completa (UX-015, substitui o modal).
 * - `received_documents` — «Documentos e interações» do destinatário
 *   externo (DRE-019): projeção restrita `closing/documents` sob a
 *   capability `closing-documents.read`, sem as três abas internas.
 * Rotas futuras (Visão geral dedicada, Sala de interação, Ajuda)
 * entram aqui apenas quando implementadas.
 */
export type PluginView =
  | "home"
  | "financial_settlements"
  | "stock_inventory"
  | "checklist"
  | "checklist_admin"
  | "checklist_version"
  | "checklist_version_document"
  | "checklist_admin_events"
  | "catalogs_admin"
  | "documents_admin"
  | "pendencies"
  | "packages"
  | "cockpit"
  | "monthly_closing"
  | "received_documents"
  | "my_tasks"
  | "profile"
  | "clara_consent"
  | "not_found";

export type PluginNavId = "home" | "my_tasks";

export type PluginNavigationTarget =
  | "home"
  | "financial_settlements"
  | "stock_inventory"
  | "checklist"
  | "checklist_admin"
  | "catalogs_admin"
  | "documents_admin"
  | "pendencies"
  | "packages"
  | "cockpit"
  | "monthly_closing"
  | "received_documents"
  | "my_tasks"
  | "profile";

/** Mapa rota relativa → view (paths técnicos em inglês, kebab-case). */
const RELATIVE_TO_VIEW: Record<string, PluginView> = {
  "closing/financial-settlements": "financial_settlements",
  "closing/stock-inventory": "stock_inventory",
  "closing/checklist": "checklist",
  "closing/admin": "checklist_admin",
  "closing/pendencies": "pendencies",
  "closing/packages": "packages",
  "closing/cockpit": "cockpit",
  "closing/monthly-closing": "monthly_closing",
  "closing/documents": "received_documents",
  "closing/my-tasks": "my_tasks",
  "closing/admin/catalogs": "catalogs_admin",
  "closing/admin/documents": "documents_admin",
  "closing/clara-consent": "clara_consent",
  "profile": "profile",
};

const VIEW_TO_RELATIVE: Record<Exclude<PluginNavigationTarget, "home">, string> = {
  financial_settlements: "closing/financial-settlements",
  stock_inventory: "closing/stock-inventory",
  checklist: "closing/checklist",
  checklist_admin: "closing/admin",
  pendencies: "closing/pendencies",
  packages: "closing/packages",
  cockpit: "closing/cockpit",
  monthly_closing: "closing/monthly-closing",
  received_documents: "closing/documents",
  my_tasks: "closing/my-tasks",
  catalogs_admin: "closing/admin/catalogs",
  documents_admin: "closing/admin/documents",
  profile: "profile",
};

const PERIOD_DEEP_ROUTE_PATTERN =
  /^closing\/(checklist|packages|cockpit|monthly-closing)\/(\d{4}-(0[1-9]|1[0-2]))$/;

const DEEP_ROUTE_VIEWS: Record<string, PluginView> = {
  checklist: "checklist",
  packages: "packages",
  cockpit: "cockpit",
  "monthly-closing": "monthly_closing",
};

/** Detalhe de documento da aba Documentos — deep route contextual (não é aba). */
const DOCUMENT_DETAIL_PATTERN =
  /^closing\/monthly-closing\/(\d{4}-(0[1-9]|1[0-2]))\/documents\/([A-Za-z0-9_.:%~-]+)$/;

/** Página contextual de relatório da aba Relatórios (UX-011) — deep route. */
const REPORT_DETAIL_PATTERN =
  /^closing\/monthly-closing\/(\d{4}-(0[1-9]|1[0-2]))\/reports\/([A-Za-z0-9-]+)$/;

/** Cadastro/edição de documento do catálogo mestre (UX-012) — deep route. */
const DOCUMENT_ADMIN_DETAIL_PATTERN =
  /^closing\/admin\/documents\/([A-Za-z0-9_-]{1,32})$/;

/** Histórico/auditoria do template ou de uma versão (UX-015). */
const ADMIN_EVENTS_PATTERN = /^closing\/admin\/events$/;
const ADMIN_VERSION_EVENTS_PATTERN =
  /^closing\/admin\/versions\/(\d+)\/events$/;

/** Detalhe contextual de uma versão do checklist mestre (UX-015). */
const ADMIN_VERSION_DETAIL_PATTERN =
  /^closing\/admin\/versions\/(\d+)$/;

/** Documento dentro de uma versão histórica (UX-015). */
const ADMIN_VERSION_DOCUMENT_PATTERN =
  /^closing\/admin\/versions\/(\d+)\/documents\/([^/]{1,64})$/;

/** Entrega da competência ao destinatário externo (DRE-019). */
const RECEIVED_DELIVERY_PATTERN =
  /^closing\/documents\/(\d{4}-(0[1-9]|1[0-2]))$/;

/** Detalhe do documento recebido (DRE-019) — deep route contextual. */
const RECEIVED_DOCUMENT_PATTERN =
  /^closing\/documents\/(\d{4}-(0[1-9]|1[0-2]))\/documents\/([A-Za-z0-9_.:%~-]+)$/;

export type ResolvedPluginRoute = {
  view: PluginView;
  pathname: string;
  relativePath: string;
  /** Competência YYYY-MM quando a deep route é `closing/{view}/{period}`. */
  checklistPeriod?: string;
  /** Referência do documento na rota de detalhe (UUID, `item:{key}` ou `new`). */
  documentRef?: string;
  /** Chave do relatório na rota contextual (`financial-settlements`, `stock-inventory`). */
  reportKey?: string;
  /** Chave do documento na rota admin (`new` ou `item_key` do catálogo). */
  documentItemKey?: string;
  /** Número da versão na rota admin em cascata (`versions/{n}`). */
  adminVersion?: string;
};

export function normalizePathname(pathname: string): string {
  const raw = (pathname || "").trim() || "/";
  const withoutQuery = raw.split("?")[0]?.split("#")[0] ?? raw;
  if (withoutQuery.length > 1 && withoutQuery.endsWith("/")) {
    return withoutQuery.slice(0, -1);
  }
  return withoutQuery || "/";
}

export function normalizeBasePath(basePath?: string): string {
  return normalizePathname(basePath?.trim() || CONTROLLERSHIP_FINANCE_BASE_PATH);
}

export function resolvePluginRoute(
  pathname: string | undefined,
  basePath?: string,
): ResolvedPluginRoute {
  const base = normalizeBasePath(basePath);
  const path = normalizePathname(pathname ?? base);

  if (path === base) {
    return { view: "home", pathname: path, relativePath: "" };
  }

  const relativePath = path.startsWith(`${base}/`)
    ? path.slice(base.length + 1)
    : path.slice(base.length);
  const receivedDocumentMatch =
    RECEIVED_DOCUMENT_PATTERN.exec(relativePath);
  if (receivedDocumentMatch) {
    return {
      view: "received_documents",
      pathname: path,
      relativePath,
      checklistPeriod: receivedDocumentMatch[1],
      documentRef: decodeURIComponent(receivedDocumentMatch[3] ?? ""),
    };
  }
  const receivedDeliveryMatch =
    RECEIVED_DELIVERY_PATTERN.exec(relativePath);
  if (receivedDeliveryMatch) {
    return {
      view: "received_documents",
      pathname: path,
      relativePath,
      checklistPeriod: receivedDeliveryMatch[1],
    };
  }
  const documentMatch = DOCUMENT_DETAIL_PATTERN.exec(relativePath);
  if (documentMatch) {
    return {
      view: "monthly_closing",
      pathname: path,
      relativePath,
      checklistPeriod: documentMatch[1],
      documentRef: decodeURIComponent(documentMatch[3] ?? ""),
    };
  }
  const reportMatch = REPORT_DETAIL_PATTERN.exec(relativePath);
  if (reportMatch) {
    return {
      view: "monthly_closing",
      pathname: path,
      relativePath,
      checklistPeriod: reportMatch[1],
      reportKey: reportMatch[3],
    };
  }
  const versionDocumentMatch =
    ADMIN_VERSION_DOCUMENT_PATTERN.exec(relativePath);
  if (versionDocumentMatch) {
    return {
      view: "checklist_version_document",
      pathname: path,
      relativePath,
      adminVersion: versionDocumentMatch[1],
      documentItemKey: decodeURIComponent(versionDocumentMatch[2] ?? ""),
    };
  }
  const versionEventsMatch =
    ADMIN_VERSION_EVENTS_PATTERN.exec(relativePath);
  if (versionEventsMatch) {
    return {
      view: "checklist_admin_events",
      pathname: path,
      relativePath,
      adminVersion: versionEventsMatch[1],
    };
  }
  const versionMatch = ADMIN_VERSION_DETAIL_PATTERN.exec(relativePath);
  if (versionMatch) {
    return {
      view: "checklist_version",
      pathname: path,
      relativePath,
      adminVersion: versionMatch[1],
    };
  }
  if (ADMIN_EVENTS_PATTERN.test(relativePath)) {
    return {
      view: "checklist_admin_events",
      pathname: path,
      relativePath,
    };
  }
  const documentAdminMatch =
    DOCUMENT_ADMIN_DETAIL_PATTERN.exec(relativePath);
  if (documentAdminMatch) {
    return {
      view: "documents_admin",
      pathname: path,
      relativePath,
      documentItemKey: documentAdminMatch[1],
    };
  }
  const periodMatch = PERIOD_DEEP_ROUTE_PATTERN.exec(relativePath);
  const view = periodMatch
    ? DEEP_ROUTE_VIEWS[periodMatch[1] ?? ""] ?? "not_found"
    : RELATIVE_TO_VIEW[relativePath] ?? "not_found";

  return {
    view,
    pathname: path,
    relativePath,
    checklistPeriod: periodMatch?.[2],
  };
}

/** Path canônico da view (paths só via buildPluginPath — sem URL absoluta). */
export function buildPluginPath(
  view: PluginNavigationTarget,
  basePath?: string,
  search?: string,
): string {
  const base = normalizeBasePath(basePath);
  const suffix = view === "home" ? "" : `/${VIEW_TO_RELATIVE[view]}`;
  const normalizedSearch = search?.startsWith("?")
    ? search
    : search
      ? `?${search}`
      : "";
  return `${base}${suffix}${normalizedSearch}`;
}

/** Path da página contextual de uma versão do checklist (UX-015). */
export function checklistAdminVersionPath(
  version: number | string,
  basePath?: string,
): string {
  const base = normalizeBasePath(basePath);
  return `${base}/closing/admin/versions/${version}`;
}

/** Path do documento dentro de uma versão histórica (UX-015). */
export function checklistAdminVersionDocumentPath(
  version: number | string,
  itemKey: string,
  basePath?: string,
): string {
  return `${checklistAdminVersionPath(version, basePath)}/documents/${encodeURIComponent(itemKey)}`;
}

/** Path do histórico/auditoria — template inteiro ou versão (UX-015). */
export function checklistAdminEventsPath(
  version?: number | string,
  basePath?: string,
): string {
  const base = normalizeBasePath(basePath);
  return version === undefined
    ? `${base}/closing/admin/events`
    : `${base}/closing/admin/versions/${version}/events`;
}

export function resolveActiveNavId(view: PluginView): PluginNavId | null {
  if (view === "home") return "home";
  if (view === "my_tasks") return "my_tasks";
  return null;
}
