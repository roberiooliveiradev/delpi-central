import { configureHttpClient } from "./api/httpClient";
import { useKaizenRouterPath } from "./hooks/useKaizenRouterPath";
import { CadastroKaizenPage } from "./pages/CadastroKaizenPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  permissions,
  isSuperadmin,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());
  const pathname = useKaizenRouterPath(pathnameFromHost);

  return (
    <div className="dashboard-kaizometro dashboard-page">
      <div className="kz-app-shell">
        <CadastroKaizenPage
          pathname={pathname}
          permissions={permissions}
          isSuperadmin={isSuperadmin}
        />
      </div>
    </div>
  );
}
