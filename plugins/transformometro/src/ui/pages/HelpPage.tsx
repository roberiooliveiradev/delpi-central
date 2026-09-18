import { SectionCard, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_PAGE_COPY } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { USER_MANUAL_CONTENT } from "../../content/userManualContent";

const SECTION = sectionCardPacBemClasses("ds");
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

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={copy.eyebrow}
        title={copy.title}
        subtitle={copy.description}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.help}
        onNavigate={onNavigate}
      />
      <div className="tm-home-paths">
        <nav aria-label={manual.tocAriaLabel}>
          <SectionCard classNames={SECTION} labels={SECTION_LABELS} title={manual.tocTitle}>
            <ul className="tm-help-toc">
              {manual.sections.map((section) => (
                <li key={section.id}>
                  <button type="button" className={DS_GHOST_BTN} onClick={() => scrollToSection(section.id)}>
                    {section.title}
                  </button>
                </li>
              ))}
            </ul>
          </SectionCard>
        </nav>
        {manual.sections.map((section) => (
          <section key={section.id} id={`manual-${section.id}`}>
            <SectionCard classNames={SECTION} labels={SECTION_LABELS} title={section.title}>
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
              {section.links && section.links.length > 0 ? (
                <ul className="tm-help-toc">
                  {section.links.map((link) => (
                    <li key={link.path}>
                      <button type="button" className={DS_GHOST_BTN} onClick={() => onNavigate(link.path)}>
                        {link.label}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </SectionCard>
          </section>
        ))}
      </div>
    </TransformometroShell>
  );
}
