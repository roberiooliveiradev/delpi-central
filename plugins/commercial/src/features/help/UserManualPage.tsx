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
import { UserManualLinkedText } from "./UserManualLinkedText";

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

      <p className="cm-user-manual__scope-note">
        <UserManualLinkedText text={c.scopeNote} basePath={basePath} />
      </p>

      <div className="cm-user-manual__layout">
        <nav className="cm-user-manual__toc" aria-label={c.tocAriaLabel}>
          <p className="cm-user-manual__toc-title">{c.tocTitle}</p>
          <ul>
            <li>
              <button
                type="button"
                className="cm-user-manual__toc-link"
                onClick={() => scrollToSection("concepts")}
              >
                {c.conceptsTitle}
              </button>
            </li>
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

        <div className="cm-user-manual__main">
          <section id="manual-concepts" className="cm-user-manual__section">
            <SectionCard
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
              title={c.conceptsTitle}
            >
              <ul className="cm-user-manual__concepts">
                {c.concepts.map((item) => (
                  <li key={item.term} className="cm-user-manual__concept-card">
                    <strong>{item.term}</strong>
                    <UserManualLinkedText text={item.meaning} basePath={basePath} />
                  </li>
                ))}
              </ul>
            </SectionCard>
          </section>

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
                  <p className="cm-user-manual__intro">
                    <UserManualLinkedText text={section.intro} basePath={basePath} />
                  </p>
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
                            <td>
                              <UserManualLinkedText text={row.want} basePath={basePath} />
                            </td>
                            <td>
                              <UserManualLinkedText
                                text={row.where}
                                basePath={basePath}
                                className="cm-user-manual__where"
                              />
                            </td>
                            <td>
                              <UserManualLinkedText text={row.how} basePath={basePath} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : null}

                {section.bullets?.length ? (
                  <ul className="cm-user-manual__list">
                    {section.bullets.map((item) => (
                      <li key={item}>
                        <UserManualLinkedText text={item} basePath={basePath} />
                      </li>
                    ))}
                  </ul>
                ) : null}

                {section.faqs?.length ? (
                  <dl className="cm-user-manual__faq">
                    {section.faqs.map((item) => (
                      <div key={item.q} className="cm-user-manual__faq-item">
                        <dt>
                          <UserManualLinkedText text={item.q} basePath={basePath} />
                        </dt>
                        <dd>
                          <UserManualLinkedText text={item.a} basePath={basePath} />
                        </dd>
                      </div>
                    ))}
                  </dl>
                ) : null}

                {section.glossary?.length ? (
                  <dl className="cm-user-manual__glossary">
                    {section.glossary.map((item) => (
                      <div key={item.term} className="cm-user-manual__glossary-item">
                        <dt>
                          <UserManualLinkedText text={item.term} basePath={basePath} />
                        </dt>
                        <dd>
                          <UserManualLinkedText text={item.meaning} basePath={basePath} />
                        </dd>
                      </div>
                    ))}
                  </dl>
                ) : null}
              </SectionCard>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
