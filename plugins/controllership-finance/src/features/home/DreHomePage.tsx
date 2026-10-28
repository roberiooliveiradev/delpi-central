/**
 * Home DRE (DRE-019-RW02) — página inicial do Portal para o público
 * externo da Contabilidade/DRE sob `access.dre` (legada
 * `closing-documents.read` em compatibilidade transitória).
 *
 * Mesmo MFE e mesmos primitivos da Home interna — saudação honesta +
 * card da única funcionalidade autorizada («Fechamento Mensal» →
 * Documentos e interações). Nenhuma rota interna, relatório ou métrica
 * é oferecida: a composição é a projeção visual da capability, sem
 * duplicar autorização — a BFF continua fail-closed por vínculo.
 */
import { CalendarCheck2 } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { useViewerContext } from "../../app/ViewerContext";
import {
  CfActionButton,
  CfLoadingCard,
  CfSectionCard,
  CfSectionRouteCard,
  CfStateBanner,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";

const FORBIDDEN_STATUS = 403;

export function DreHomePage({ basePath }: { basePath: string }) {
  const { viewer, loading, errorStatus, reload } = useViewerContext();

  if (loading) {
    return (
      <section className="cf-page-stack cf-home-layout" aria-label="Início">
        <CfLoadingCard title="Carregando contexto…" variant="panel" />
      </section>
    );
  }

  if (errorStatus === FORBIDDEN_STATUS) {
    return (
      <section className="cf-page-stack cf-home-layout" aria-label="Início">
        <CfStateBanner variant="error">
          <p className="cf-banner-title">Acesso restrito</p>
          <p className="cf-banner-text">
            Você não tem permissão para acessar o Portal Controladoria &amp;
            Finanças.
          </p>
        </CfStateBanner>
      </section>
    );
  }

  const firstName = viewer?.firstName;

  return (
    <section className="cf-page-stack cf-home-layout" aria-label="Início">
      <div className="cf-home-stack">
        {errorStatus != null ? (
          <CfStateBanner>
            <p className="cf-banner-title">Contexto indisponível</p>
            <p className="cf-banner-text">
              Não foi possível carregar os dados do seu perfil. A navegação
              permanece disponível.
            </p>
            <CfActionButton variant="ghost" onClick={reload}>
              Tentar novamente
            </CfActionButton>
          </CfStateBanner>
        ) : null}

        <CfSectionCard
          title={
            firstName
              ? `Bem-vindo, ${firstName}`
              : "Bem-vindo ao Portal Controladoria & Finanças"
          }
          subtitle="Acompanhe os fechamentos e documentos disponibilizados pela Controladoria."
          hint={CF_HELP.dreHome.features}
        >
          <div className="cf-home-sections-grid" aria-label="Funcionalidades disponíveis">
            <CfSectionRouteCard
              title="Fechamento Mensal"
              description="Consulte documentos recebidos, baixe arquivos e acompanhe interações com a Controladoria."
              icon={
                <CalendarCheck2
                  size={20}
                  strokeWidth={1.75}
                  aria-hidden="true"
                />
              }
              routes={[
                {
                  id: "closing-documents",
                  label: "Documentos e interações",
                  kind: "navigate",
                  onClick: () =>
                    navigatePluginView("received_documents", {
                      basePath,
                    }),
                },
              ]}
            />
          </div>
        </CfSectionCard>
      </div>
    </section>
  );
}

