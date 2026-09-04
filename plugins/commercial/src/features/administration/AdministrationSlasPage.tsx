import { RefreshCw } from "lucide-react";

import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionHintLabel,
} from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import { CM_HELP } from "../../content/helpTooltips";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationSlasPageProps = {
  basePath: string;
};

/** Shell da aba SLAs — CRUD operacional chega na subetapa seguinte. */
export function AdministrationSlasPage({ basePath }: AdministrationSlasPageProps) {
  const copy = ADMINISTRATION_CONTENT.slas;

  return (
    <section className="cm-page-stack cm-administration-slas">
      <CommercialPagePath
        aria-label={copy.title}
        items={[
          {
            id: "admin-root",
            label: ADMINISTRATION_CONTENT.breadcrumbRoot,
            href: `${basePath}/administration`,
            onNavigate: () => {
              navigatePluginView("administration", { basePath });
            },
          },
          { id: "slas", label: copy.title, current: true },
        ]}
      />
      <AdministrationSubNav basePath={basePath} active="slas" />
      <CommercialPageHero
        aria-label={copy.title}
        title={
          <CommercialSectionHintLabel label={copy.title} hint={CM_HELP.administration.slasPage} />
        }
        description={copy.description}
        actions={
          <CommercialActionButton variant="ghost" disabled>
            <RefreshCw size={16} aria-hidden="true" /> {copy.refresh}
          </CommercialActionButton>
        }
      />
      <CommercialEmptyState
        defaultTitle={copy.emptyTitle}
        defaultMessage={copy.emptyDescription}
      />
    </section>
  );
}
