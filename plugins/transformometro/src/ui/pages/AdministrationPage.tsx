import { SectionCard, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { TransformometroShell } from "../../components/TransformometroShell";
import { PORTAL_ADMIN_LINKS, PORTAL_PRODUCT_NAME } from "../../constants/portalExperience";
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

  return (
    <TransformometroShell>
      <PageHeader
        eyebrow={PORTAL_PRODUCT_NAME}
        title="Administração"
        subtitle="Gerencie configurações e recursos administrativos do Portal Transforma+."
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
      </div>
    </TransformometroShell>
  );
}
