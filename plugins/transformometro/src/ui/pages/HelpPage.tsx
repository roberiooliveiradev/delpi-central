import {
  ActionButton,
  PagePath,
  SectionCard,
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
          <span className="tm-user-manual__eyebrow">
            <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
            {copy.eyebrow}
          </span>
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
      <div className="tm-user-manual">
        <p className="tm-user-manual__scope">{manual.scopeNote}</p>
        <div className="tm-user-manual__layout">
          <nav className="tm-user-manual__toc" aria-label={manual.tocAriaLabel}>
            <p className="tm-user-manual__toc-title">{manual.tocTitle}</p>
            <ul>
              <li>
                <button type="button" className="tm-user-manual__toc-link" onClick={() => scrollToSection("concepts")}>
                  {manual.conceptsTitle}
                </button>
              </li>
              {manual.sections.map((section) => (
                <li key={section.id}>
                  <button
                    type="button"
                    className="tm-user-manual__toc-link"
                    onClick={() => scrollToSection(section.id)}
                  >
                    {section.title}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
          <div className="tm-user-manual__main">
            <section id="manual-concepts">
              <SectionCard classNames={SECTION} labels={SECTION_LABELS} title={manual.conceptsTitle}>
                <ul className="tm-user-manual__concepts">
                  {manual.concepts.map((item) => (
                    <li key={item.term} className="tm-user-manual__concept">
                      <strong>{item.term}</strong>
                      <p>{item.meaning}</p>
                    </li>
                  ))}
                </ul>
              </SectionCard>
            </section>
            {manual.sections.map((section) => {
              const links = visibleManualLinks(section.links, canManage);
              return (
                <section key={section.id} id={`manual-${section.id}`}>
                  <SectionCard classNames={SECTION} labels={SECTION_LABELS} title={section.title}>
                    {section.intro ? <p>{section.intro}</p> : null}
                    {section.bullets && section.bullets.length > 0 ? (
                      <ul className="tm-user-manual__list">
                        {section.bullets.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    ) : null}
                    {links.length > 0 ? (
                      <div className="tm-user-manual__table-wrap">
                        <table className="tm-user-manual__table">
                          <thead>
                            <tr>
                              <th scope="col">Quero…</th>
                              <th scope="col">Onde ir</th>
                              <th scope="col">Como</th>
                            </tr>
                          </thead>
                          <tbody>
                            {links.map((link) => (
                              <tr key={`${link.want}-${link.where}`}>
                                <td>{link.want}</td>
                                <td>
                                  {link.path ? (
                                    <button
                                      type="button"
                                      className="tm-user-manual__where"
                                      onClick={() => onNavigate(link.path!)}
                                    >
                                      {link.where}
                                    </button>
                                  ) : (
                                    link.where
                                  )}
                                </td>
                                <td>{link.how}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </SectionCard>
                </section>
              );
            })}
          </div>
        </div>
      </div>
    </TransformometroShell>
  );
}
