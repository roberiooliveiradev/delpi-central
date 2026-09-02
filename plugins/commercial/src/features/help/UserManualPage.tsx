import { SectionCard } from "@delpi/plugin-ui/index";
import { BookOpen } from "lucide-react";

import {
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialPageHero,
  CommercialPagePath,
} from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { USER_MANUAL_CONTENT } from "../../content/userManualContent";

type UserManualPageProps = {
  basePath: string;
};

function scrollToSection(id: string) {
  const el = document.getElementById(`manual-${id}`);
  el?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function UserManualPage({ basePath }: UserManualPageProps) {
  const c = USER_MANUAL_CONTENT;
  const homeHref = buildPluginPath("home", basePath);

  return (
    <div className="cm-page-stack cm-user-manual">
      <CommercialPagePath
        back={{
          label: "Início",
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={c.pageTitle}
      />
      <CommercialPageHero
        eyebrow={
          <span className="cm-user-manual__eyebrow">
            <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
            Ajuda
          </span>
        }
        title={c.pageTitle}
        description={c.pageSubtitle}
        actions={
          <CommercialActionButton
            variant="secondary"
            onClick={() => navigatePluginView("home", { basePath })}
          >
            {c.backHome}
          </CommercialActionButton>
        }
      />

      <p className="cm-user-manual__scope-note">{c.scopeNote}</p>

      <SectionCard
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
        title={c.conceptsTitle}
      >
        <ul className="cm-user-manual__concepts">
          {c.concepts.map((item) => (
            <li key={item.term}>
              <strong>{item.term}</strong> — {item.meaning}
            </li>
          ))}
        </ul>
      </SectionCard>

      <nav className="cm-user-manual__toc" aria-label={c.tocAriaLabel}>
        <p className="cm-user-manual__toc-title">{c.tocTitle}</p>
        <ul>
          {c.sections.map((section) => (
            <li key={section.id}>
              <button
                type="button"
                className="cm-user-manual__toc-link"
                onClick={() => scrollToSection(section.id)}
              >
                {section.title}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {c.sections.map((section) => (
        <section
          key={section.id}
          id={`manual-${section.id}`}
          className="cm-user-manual__section"
        >
          <SectionCard
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
            title={section.title}
          >
            {section.intro ? (
              <p className="cm-user-manual__intro">{section.intro}</p>
            ) : null}

            {section.links?.length ? (
              <div className="cm-user-manual__table-wrap">
                <table className="cm-user-manual__table">
                  <thead>
                    <tr>
                      <th scope="col">Quero…</th>
                      <th scope="col">Onde ir</th>
                      <th scope="col">Como</th>
                    </tr>
                  </thead>
                  <tbody>
                    {section.links.map((row) => (
                      <tr key={row.want}>
                        <td>{row.want}</td>
                        <td>
                          <strong>{row.where}</strong>
                        </td>
                        <td>{row.how}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}

            {section.bullets?.length ? (
              <ul className="cm-user-manual__list">
                {section.bullets.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : null}

            {section.faqs?.length ? (
              <dl className="cm-user-manual__faq">
                {section.faqs.map((item) => (
                  <div key={item.q} className="cm-user-manual__faq-item">
                    <dt>{item.q}</dt>
                    <dd>{item.a}</dd>
                  </div>
                ))}
              </dl>
            ) : null}

            {section.glossary?.length ? (
              <dl className="cm-user-manual__glossary">
                {section.glossary.map((item) => (
                  <div key={item.term} className="cm-user-manual__glossary-item">
                    <dt>{item.term}</dt>
                    <dd>{item.meaning}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
          </SectionCard>
        </section>
      ))}
    </div>
  );
}
