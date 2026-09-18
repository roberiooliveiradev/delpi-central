import { BookOpen } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesUserManual,
} from "../../app/suppliesUi";
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
  const Manual = SuppliesUserManual;

  return (
    <Manual.Frame className="sp-page-stack">
      <SuppliesPagePath
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

      <SuppliesPageHero
        eyebrow={
          <Manual.Eyebrow>
            <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
            Ajuda
          </Manual.Eyebrow>
        }
        title={c.pageTitle}
        description={c.pageSubtitle}
        actions={
          <SuppliesActionButton
            variant="default"
            onClick={() => navigatePluginView("home", { basePath })}
          >
            {c.backHome}
          </SuppliesActionButton>
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
          <SuppliesSectionCard title={c.conceptsTitle}>
            <Manual.Concepts
              items={c.concepts.map((item) => ({
                term: item.term,
                meaning: <UserManualLinkedText text={item.meaning} basePath={basePath} />,
              }))}
            />
          </SuppliesSectionCard>
        </Manual.Section>

        {c.sections.map((section) => (
          <Manual.Section key={section.id} id={`manual-${section.id}`}>
            <SuppliesSectionCard title={section.title}>
              {section.intro ? (
                <p className={Manual.classNames.intro}>
                  <UserManualLinkedText text={section.intro} basePath={basePath} />
                </p>
              ) : null}

              {section.links?.length ? (
                <Manual.GuideTable
                  rows={section.links.map((row) => ({
                    want: <UserManualLinkedText text={row.want} basePath={basePath} />,
                    where: <UserManualLinkedText text={row.where} basePath={basePath} />,
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
                    term: item.term,
                    meaning: <UserManualLinkedText text={item.meaning} basePath={basePath} />,
                  }))}
                />
              ) : null}
            </SuppliesSectionCard>
          </Manual.Section>
        ))}
      </Manual.Layout>
    </Manual.Frame>
  );
}
