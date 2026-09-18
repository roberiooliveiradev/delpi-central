import { BookOpen } from "lucide-react";

import {
  CommercialActionButton,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialUserManual,
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
  const Manual = CommercialUserManual;

  return (
    <Manual.Frame className="cm-page-stack">
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
          <Manual.Eyebrow>
            <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
            Ajuda
          </Manual.Eyebrow>
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

      <Manual.Scope>
        <UserManualLinkedText text={c.scopeNote} basePath={basePath} />
      </Manual.Scope>

      <Manual.Layout
        title={c.tocTitle}
        aria-label={c.tocAriaLabel}
        items={[
          { id: "concepts", label: c.conceptsTitle, onSelect: () => scrollToSection("concepts") },
          ...c.sections.map((section) => ({
            id: section.id,
            label: section.title,
            onSelect: () => scrollToSection(section.id),
          })),
        ]}
      >
        <Manual.Section id="manual-concepts">
          <CommercialSectionCard title={c.conceptsTitle}>
            <Manual.Concepts
              items={c.concepts.map((item) => ({
                term: item.term,
                meaning: <UserManualLinkedText text={item.meaning} basePath={basePath} />,
              }))}
            />
          </CommercialSectionCard>
        </Manual.Section>

        {c.sections.map((section) => (
          <Manual.Section key={section.id} id={`manual-${section.id}`}>
            <CommercialSectionCard title={section.title}>
              {section.intro ? (
                <p className={Manual.classNames.intro}>
                  <UserManualLinkedText text={section.intro} basePath={basePath} />
                </p>
              ) : null}

              {section.links?.length ? (
                <Manual.GuideTable
                  rows={section.links.map((row) => ({
                    want: <UserManualLinkedText text={row.want} basePath={basePath} />,
                    where: (
                      <UserManualLinkedText
                        text={row.where}
                        basePath={basePath}
                        className={Manual.classNames.where}
                      />
                    ),
                    how: <UserManualLinkedText text={row.how} basePath={basePath} />,
                  }))}
                />
              ) : null}

              {section.bullets?.length ? (
                <ul className={Manual.classNames.list}>
                  {section.bullets.map((item) => (
                    <li key={item}>
                      <UserManualLinkedText text={item} basePath={basePath} />
                    </li>
                  ))}
                </ul>
              ) : null}

              {section.faqs?.length ? (
                <Manual.Faq
                  items={section.faqs.map((item) => ({
                    q: <UserManualLinkedText text={item.q} basePath={basePath} />,
                    a: <UserManualLinkedText text={item.a} basePath={basePath} />,
                  }))}
                />
              ) : null}

              {section.glossary?.length ? (
                <Manual.Glossary
                  items={section.glossary.map((item) => ({
                    term: <UserManualLinkedText text={item.term} basePath={basePath} />,
                    meaning: <UserManualLinkedText text={item.meaning} basePath={basePath} />,
                  }))}
                />
              ) : null}

              {section.glossaryGroups?.map((group) => (
                <div key={group.id} className={Manual.classNames.glossaryGroup}>
                  <h3 className={Manual.classNames.glossaryGroupTitle}>{group.title}</h3>
                  <Manual.Glossary
                    appliesLabel="Onde aparece"
                    items={group.entries.map((item) => ({
                      term: <UserManualLinkedText text={item.term} basePath={basePath} />,
                      meaning: <UserManualLinkedText text={item.meaning} basePath={basePath} />,
                      applies: <UserManualLinkedText text={item.applies} basePath={basePath} />,
                    }))}
                  />
                </div>
              ))}
            </CommercialSectionCard>
          </Manual.Section>
        ))}
      </Manual.Layout>
    </Manual.Frame>
  );
}
