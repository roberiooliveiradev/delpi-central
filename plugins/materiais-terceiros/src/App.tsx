import { configureHttpClient } from "./api/httpClient";
import { MateriaisTerceirosPage } from "./pages/MateriaisTerceirosPage";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  permissions?: string[];
  hasPermission?: (code: string) => boolean;
  isSuperadmin?: boolean;
};

export default function App({
  getAccessToken,
  pathname: pathnameFromHost,
  permissions,
  hasPermission,
  isSuperadmin,
}: AppProps) {
  configureHttpClient(() => getAccessToken?.());

  return (
    <MateriaisTerceirosPage
      getAccessToken={getAccessToken}
      pathname={pathnameFromHost}
      permissions={permissions}
      hasPermission={hasPermission}
      isSuperadmin={isSuperadmin}
    />
  );
}
