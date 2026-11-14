import { CommercialPagePath } from "../../app/commercialUi";
import { navigatePluginPath, navigatePluginView } from "../../app/pluginNavigation";
import {
  buildPluginPath,
  buildSatisfactionCampaignDetailPath,
} from "../../app/pluginRoutes";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";

type SatisfactionPagePathProps = {
  basePath: string;
  ariaLabel: string;
  /** Página atual (último segmento, sem link). */
  current: string;
  /** Presente nas páginas abaixo da lista: «Pesquisa de Satisfação» vira link. */
  showListLink?: boolean;
  /** Presente no detalhe do participante: nome da campanha vira link. */
  campaign?: { id: string; name: string };
};

type NavEvent = { preventDefault: () => void };

/** Breadcrumb compartilhado das 3 páginas de configuração da Pesquisa de Satisfação. */
export function SatisfactionPagePath({
  basePath,
  ariaLabel,
  current,
  showListLink = false,
  campaign,
}: SatisfactionPagePathProps) {
  const listHref = buildPluginPath("satisfaction_surveys", basePath);
  const items = [
    ...(showListLink
      ? [
          {
            id: "satisfaction-list",
            label: SATISFACTION_CONTENT.breadcrumbRoot,
            href: listHref,
            onNavigate: (event: NavEvent) => {
              event.preventDefault();
              navigatePluginView("satisfaction_surveys", { basePath });
            },
          },
        ]
      : []),
    ...(campaign
      ? (() => {
          const href = buildSatisfactionCampaignDetailPath(basePath, campaign.id) ?? listHref;
          return [
            {
              id: "satisfaction-campaign",
              label: campaign.name,
              href,
              onNavigate: (event: NavEvent) => {
                event.preventDefault();
                navigatePluginPath(href);
              },
            },
          ];
        })()
      : []),
  ];

  return (
    <CommercialPagePath
      aria-label={ariaLabel}
      back={{
        label: "Portal Comercial",
        href: basePath,
        onNavigate: (event) => {
          event.preventDefault();
          navigatePluginView("home", { basePath });
        },
      }}
      items={items}
      current={current}
    />
  );
}
