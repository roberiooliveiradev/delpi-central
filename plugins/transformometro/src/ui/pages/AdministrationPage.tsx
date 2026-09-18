import { SectionCard, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_ADMIN_LINKS } from "../../constants/portalExperience";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

const SECTION = sectionCardPacBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

type AdministrationPageProps = Pick<AppProps, "pathname"> & {
  onNavigate: (path: string) => void;
};

export function AdministrationPage({ pathname, onNavigate }: AdministrationPageProps) {
  const settings = PORTAL_ADMIN_LINKS.filter((link) => link.id !== "data");
  const transfer = PORTAL_ADMIN_LINKS.find((link) => link.id === "data");

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow="Administração"
        title="Administração"
        subtitle="Configurações e capabilities administrativas do domínio."
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.administration}
        onNavigate={onNavigate}
      />
      <div className="tm-portal-catalog">
        <SectionCard classNames={SECTION} labels={SECTION_LABELS} title="Configurações">
          <ul className="tm-portal-catalog__links">
            {settings.map((link) => (
              <li key={link.id}>
                <button type="button" className={DS_GHOST_BTN} onClick={() => onNavigate(link.path)}>
                  {link.label}
                </button>
              </li>
            ))}
          </ul>
        </SectionCard>
        {transfer ? (
          <SectionCard classNames={SECTION} labels={SECTION_LABELS} title="Dados">
            <ul className="tm-portal-catalog__links">
              <li>
                <button
                  type="button"
                  className={DS_GHOST_BTN}
                  onClick={() => onNavigate(transfer.path)}
                >
                  {transfer.label}
                </button>
              </li>
            </ul>
          </SectionCard>
        ) : null}
      </div>
    </TransformometroShell>
  );
}
