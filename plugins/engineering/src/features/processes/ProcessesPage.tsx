/** Hub Processos — entrada da área de Engenharia de Processos. Apenas
 * ferramentas operacionais ocupam a tela; expansões futuras entram por
 * catálogo quando disponíveis, sem cards placeholder. */

import { Gauge } from "lucide-react";

import { navigateGovernedHref } from "../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringPageHero,
  EngineeringSectionCard,
} from "../../ui/engineeringUi";

const LINE_BALANCING_HREF = "/apps/engineering/processes/line-balancing";

export function ProcessesPage({ basePath }: { basePath?: string }) {
  return (
    <>
      <EngineeringPageHero
        aria-label="Engenharia de Processos"
        eyebrow="Processos"
        title="Engenharia de Processos"
        description="Ferramentas para análise, melhoria e otimização dos processos de fabricação."
      />
      <EngineeringSectionCard
        title="Ferramentas"
        subtitle="Ferramentas operacionais da área — novas capacidades entram por catálogo quando disponíveis."
      >
        <div className="engineering-processes__tool-row">
          <div className="engineering-processes__tool-identity">
            <Gauge size={18} aria-hidden="true" />
            <strong>Balanceamento de Linha</strong>
          </div>
          <EngineeringActionButton
            variant="primary"
            onClick={() =>
              navigateGovernedHref(LINE_BALANCING_HREF, { basePath })
            }
          >
            Abrir ferramenta
          </EngineeringActionButton>
        </div>
      </EngineeringSectionCard>
    </>
  );
}
