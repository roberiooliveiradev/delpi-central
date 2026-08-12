import { ActionButton, EmptyState } from "@delpi/plugin-ui/index";
import { BriefcaseBusiness } from "lucide-react";

import {
  cmEmptyStateClassNames,
  CommercialPageHero,
  CommercialPagePath,
} from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationMembersPageProps = {
  basePath: string;
};

/** Placeholder até E2.S3 (roster FE). Mantém chrome do hub e CTA para Carteiras. */
export function AdministrationMembersPage({ basePath }: AdministrationMembersPageProps) {
  const copy = ADMINISTRATION_CONTENT;

  return (
    <section className="cm-page-stack cm-administration-members">
      <CommercialPagePath
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[
          {
            id: "admin",
            label: copy.breadcrumbRoot,
            href: `${basePath}/administration`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("administration", { basePath });
            },
          },
        ]}
        current={copy.members.navLabel}
      />

      <AdministrationSubNav basePath={basePath} active="members" />

      <CommercialPageHero
        aria-label={copy.members.title}
        eyebrow={copy.members.eyebrow}
        title={copy.members.title}
        description={copy.members.description}
      />

      <EmptyState
        classNames={cmEmptyStateClassNames}
        title={copy.members.title}
        description={copy.members.placeholder}
        action={
          <ActionButton
            variant="primary"
            onClick={() => navigatePluginView("administration_portfolios", { basePath })}
          >
            <BriefcaseBusiness size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.members.openPortfolios}
          </ActionButton>
        }
      />
    </section>
  );
}
