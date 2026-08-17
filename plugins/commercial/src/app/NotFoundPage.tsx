import { ActionButton } from "@delpi/plugin-ui/index";

import { buildPluginPath, normalizeBasePath } from "./pluginRoutes";
import { navigatePluginPath } from "./pluginNavigation";

type NotFoundPageProps = {
  basePath?: string;
};

export function NotFoundPage({ basePath }: NotFoundPageProps) {
  const home = buildPluginPath("home", normalizeBasePath(basePath));

  return (
    <section className="cm-page-stack">
      <h2>Página não encontrada</h2>
      <p>A rota solicitada não existe no Portal Comercial.</p>
      <ActionButton variant="primary" onClick={() => navigatePluginPath(home)}>
        Voltar ao início
      </ActionButton>
    </section>
  );
}
