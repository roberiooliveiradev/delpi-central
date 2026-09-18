import {
  ActionButton,
  PagePath,
  SectionCard,
  createDashboardUserManual,
  pagePathBemClasses,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";
import { BookOpen } from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { USER_MANUAL_CONTENT, visibleManualLinks } from "../../content/userManualContent";
import { useCanManagePortal } from "../../state/portalChrome";

const SECTION = sectionCardPacBemClasses("ds");
const PATH = pagePathBemClasses("ds");
const Manual = createDashboardUserManual({ prefix: "ds" });
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

type HelpPageProps = Pick<AppProps, "pathname"> & {
  onNavigate: (path: string) => void;
};

function scrollToSection(id: string) {
  document.getElementById(`manual-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function HelpPage({ pathname, onNavigate }: HelpPageProps) {
  const copy = PORTAL_PAGE_COPY.help;
  const manual = USER_MANUAL_CONTENT;
  const canManage = useCanManagePortal();
  const home = TRANSFORMOMETRO_ROUTES.home;

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={
          <Manual.Eyebrow>
            <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.eyebrow}
          </Manual.Eyebrow>
        }
        title={copy.title}
        subtitle={copy.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.help}
        onNavigate={onNavigate}
        lead={
          <PagePath
            classNames={PATH}
            portalScopeClassName="dashboard-transformometro"
            back={{
              label: "Início",
              href: home,
              onNavigate: (event) => {
                event.preventDefault();
                onNavigate(home);
              },
            }}
            items={[]}
            current={copy.title}
          />
        }
        actions={
          <ActionButton variant="ghost" onClick={() => onNavigate(home)}>
            {manual.backHome}
          </ActionButton>
        }
      />
      <Manual.Frame>
        <Manual.Scope>{manual.scopeNote}</Manual.Scope>
        <Manual.Layout
          title={manual.tocTitle}
          aria-label={manual.tocAriaLabel}
          items={[
            {
              id: "concepts",
              label: manual.conceptsTitle,
              onSelect: () => scrollToSection("concepts"),
            },
            ...manual.sections.map((section) => ({
              id: section.id,
              label: section.title,
              onSelect: () => scrollToSection(section.id),
            })),
          ]}
        >
          <Manual.Section id="manual-concepts">
            <SectionCard classNames={SECTION} labels={SECTION_LABELS} title={manual.conceptsTitle}>
              <Manual.Concepts
                items={manual.concepts.map((item) => ({
                  term: item.term,
                  meaning: item.meaning,
                }))}
              />
            </SectionCard>
          </Manual.Section>
          {manual.sections.map((section) => {
            const links = visibleManualLinks(section.links, canManage);
            return (
              <Manual.Section key={section.id} id={`manual-${section.id}`}>
                <SectionCard classNames={SECTION} labels={SECTION_LABELS} title={section.title}>
                  {section.intro ? <p className={Manual.classNames.intro}>{section.intro}</p> : null}
                  {section.bullets && section.bullets.length > 0 ? (
                    <ul className={Manual.classNames.list}>
                      {section.bullets.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                  {links.length > 0 ? (
                    <Manual.GuideTable
                      rows={links.map((link) => ({
                        want: link.want,
                        where: link.path ? (
                          <button
                            type="button"
                            className={Manual.classNames.where}
                            onClick={() => onNavigate(link.path!)}
                          >
                            {link.where}
                          </button>
                        ) : (
                          link.where
                        ),
                        how: link.how,
                      }))}
                    />
                  ) : null}
                </SectionCard>
              </Manual.Section>
            );
          })}
        </Manual.Layout>
      </Manual.Frame>
    </TransformometroShell>
  );
}
