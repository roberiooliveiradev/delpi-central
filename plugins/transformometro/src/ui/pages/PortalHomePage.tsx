import { useMemo, useState } from "react";
import { FieldLabel, NativeTextControl, SectionCard, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TransformometroShell } from "../../components/TransformometroShell";
import {
  PORTAL_HOME_DESCRIPTION,
  PORTAL_LAUNCHER_GROUPS,
  PORTAL_PRODUCT_NAME,
  PORTAL_WELCOME,
} from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const SECTION = sectionCardPacBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

type PortalHomePageProps = Pick<AppProps, "pathname"> & {
  onNavigate: (path: string) => void;
};

export function PortalHomePage({ pathname, onNavigate }: PortalHomePageProps) {
  const [query, setQuery] = useState("");
  const needle = query.trim().toLowerCase();
  const groups = useMemo(
    () =>
      PORTAL_LAUNCHER_GROUPS.map((group) => ({
        ...group,
        links: group.links.filter((link) =>
          needle
            ? `${group.title} ${link.label} ${link.description}`.toLowerCase().includes(needle)
            : true,
        ),
      })).filter((group) => group.links.length > 0),
    [needle],
  );

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={PORTAL_PRODUCT_NAME}
        title={PORTAL_WELCOME}
        subtitle={PORTAL_HOME_DESCRIPTION}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.home}
        onNavigate={onNavigate}
      />
      <section className="tm-portal-catalog" aria-label="Caminhos e funcionalidades">
        <div className="tm-portal-catalog__search">
          <FieldLabel className="tm-field__label" label="Caminhos e funcionalidades" />
          <NativeTextControl
            id="tm-portal-catalog-search"
            type="search"
            placeholder="Buscar caminhos e funcionalidades…"
            value={query}
            onChange={setQuery}
          />
        </div>
        <div className="ds-shortcuts-grid">
          {groups.map((group) => (
            <SectionCard
              key={group.id}
              classNames={SECTION}
              labels={SECTION_LABELS}
              title={group.title}
            >
              <ul className="tm-portal-catalog__links">
                {group.links.map((link) => (
                  <li key={link.id}>
                    <button
                      type="button"
                      className={DS_GHOST_BTN}
                      onClick={() => onNavigate(link.path)}
                    >
                      {link.label}
                    </button>
                  </li>
                ))}
              </ul>
            </SectionCard>
          ))}
        </div>
        {groups.length === 0 ? (
          <p className="ds-hint">Nenhuma funcionalidade encontrada.</p>
        ) : null}
      </section>
    </TransformometroShell>
  );
}
