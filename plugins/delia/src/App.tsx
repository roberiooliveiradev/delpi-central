import { DELIA_ROOT_CLASS, DeliaEmptyState, DeliaPageHeader } from "./ui/deliaUi";

/** Host props from Portal AppHost — presentation/transport only. */
export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
  search?: string;
  alternateEntry?: string;
  appRoutes?: Array<{ path: string; entry?: string; openInNewTab?: boolean }>;
  routeLabel?: string;
  /** Frontend presentation hint only — never backend authorization authority. */
  permissions?: string[];
  /** Frontend presentation hint only — never backend authorization authority. */
  isSuperadmin?: boolean;
};

/**
 * Minimal DÉLIA shell for C1 federated foundation.
 *
 * permissions / isSuperadmin are accepted for host-contract compatibility and
 * MUST NOT be treated as authoritative allow/deny for backend operations.
 */
export default function App({
  pathname,
  basePath,
  routeLabel,
  getAccessToken: _getAccessToken,
  permissions: _permissions,
  isSuperadmin: _isSuperadmin,
}: AppProps) {
  void _getAccessToken;
  void _permissions;
  void _isSuperadmin;

  const hostPath = pathname || basePath || "/apps/delia";

  return (
    <div className={`${DELIA_ROOT_CLASS} dashboard-page`}>
      <main className="delia-page-stack" aria-label="DÉLIA">
        <DeliaPageHeader
          title="DÉLIA"
          subtitle="Inteligência operacional standalone"
        />
        <DeliaEmptyState
          title="Fundação operacional pronta"
          message="Shell standalone da DÉLIA. Capacidades de negócio entram em tarefas posteriores."
        />
        <p className="delia-host-meta">
          {routeLabel ? `${routeLabel} · ` : null}
          Contexto de host: <span>{hostPath}</span>
        </p>
      </main>
    </div>
  );
}
