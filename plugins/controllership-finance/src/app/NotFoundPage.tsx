import { buildPluginPath, normalizeBasePath } from "./pluginRoutes";
import { navigatePluginPath } from "./pluginNavigation";
import { CfActionButton, CfPageHero } from "./controllershipFinanceUi";

type NotFoundPageProps = {
  basePath?: string;
};

export function NotFoundPage({ basePath }: NotFoundPageProps) {
  const home = buildPluginPath("home", normalizeBasePath(basePath));

  return (
    <section className="cf-page-stack" aria-label="Página não encontrada">
      <CfPageHero
        eyebrow="Controladoria & Finanças"
        title="Página não encontrada"
        description="A rota solicitada não existe neste portal."
        actions={
          <CfActionButton
            variant="primary"
            onClick={() => navigatePluginPath(home)}
          >
            Voltar ao início
          </CfActionButton>
        }
      />
    </section>
  );
}
