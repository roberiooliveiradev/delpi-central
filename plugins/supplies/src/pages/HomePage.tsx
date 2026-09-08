import { useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { navigatePluginView } from "../app/pluginNavigation";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import { SuppliesEmptyState, SuppliesStateBanner } from "../app/suppliesUi";
import { SP_HELP } from "../content/helpTooltips";
import {
  collectSearchHits,
  findHubRouteById,
  HUB_CONTENT,
  pickOnboardingShortcuts,
  resolveHomePathSections,
  type HubSectionDef,
} from "../content/pluginRouteCatalog";
import { toHubCapabilities } from "../features/home/homeCatalog";

type HomePageProps = {
  basePath: string;
};

export function HomePage({ basePath }: HomePageProps) {
  const session = useSuppliesSession();
  const hubCaps = useMemo(
    () => toHubCapabilities(session.capabilities),
    [session.capabilities],
  );
  const sections = useMemo(() => resolveHomePathSections(hubCaps), [hubCaps]);
  const onboarding = useMemo(() => pickOnboardingShortcuts(hubCaps), [hubCaps]);
  const [query, setQuery] = useState("");

  const searchHits = useMemo(
    () => collectSearchHits(sections, query, 12),
    [query, sections],
  );

  const visibleSections: HubSectionDef[] = query.trim()
    ? sections
        .map((section) => ({
          ...section,
          routes: section.routes.filter((route) =>
            searchHits.some((hit) => hit.id === route.id),
          ),
        }))
        .filter((section) => section.routes.length > 0)
    : sections;

  return (
    <div className="sp-page-stack sp-home">
      <header className="sp-home__hero">
        <p className="sp-home__eyebrow">{HUB_CONTENT.home.eyebrow}</p>
        <h1>
          {HUB_CONTENT.home.title}{" "}
          <HelpTooltip
            content={SP_HELP.homeVsOverview}
            ariaLabel={HUB_CONTENT.home.helpAriaLabel}
          />
        </h1>
        <p className="sp-home__description">{HUB_CONTENT.home.description}</p>
        {onboarding.length > 0 ? (
          <div className="sp-home__onboarding" aria-label={HUB_CONTENT.home.onboardingTitle}>
            {onboarding.map((route) => (
              <button
                key={route.id}
                type="button"
                className="sp-home__chip"
                onClick={() => navigatePluginView(route.viewId, { basePath })}
              >
                {route.label}
              </button>
            ))}
          </div>
        ) : null}
      </header>

      <section className="sp-home__paths" aria-label={HUB_CONTENT.home.pathsTitle}>
        <div className="sp-home__paths-head">
          <div>
            <h2>{HUB_CONTENT.home.pathsTitle}</h2>
            <p>{HUB_CONTENT.home.pathsSubtitle}</p>
          </div>
          <label className="sp-home__search">
            <span className="sp-visually-hidden">{HUB_CONTENT.home.searchPlaceholder}</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={HUB_CONTENT.home.searchPlaceholder}
            />
          </label>
        </div>

        {visibleSections.length === 0 ? (
          <SuppliesEmptyState
            title={query.trim() ? HUB_CONTENT.home.searchEmpty : HUB_CONTENT.home.pathsEmpty}
            message={HUB_CONTENT.home.pathsSubtitle}
          />
        ) : (
          visibleSections.map((section) => (
            <div key={section.id} className="sp-home__section">
              <h3>{section.title}</h3>
              {section.description ? <p>{section.description}</p> : null}
              <ul className="sp-home__route-list">
                {section.routes.map((route) => (
                  <li key={route.id}>
                    <button
                      type="button"
                      className="sp-home__route"
                      onClick={() => {
                        const target = findHubRouteById(sections, route.id) ?? route;
                        navigatePluginView(target.viewId, { basePath });
                      }}
                    >
                      {route.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))
        )}
      </section>

      {session.allowedUnits.length > 0 ? (
        <SuppliesStateBanner>
          Filiais no seu escopo: {session.allowedUnits.join(", ")}.
        </SuppliesStateBanner>
      ) : null}
    </div>
  );
}
