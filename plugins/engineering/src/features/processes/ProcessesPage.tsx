/** Hub Processos — catálogo das ferramentas de Engenharia de
 * Processos. Ferramentas futuras aparecem como planejamento (sem
 * navegação), nunca como funcionalidade simulada. */

import { Gauge, Workflow } from "lucide-react";

import { navigateGovernedHref } from "../../app/engineeringRoutes";
import {
  EngineeringPageHero,
  EngineeringSectionRouteCard,
} from "../../ui/engineeringUi";

const LINE_BALANCING_HREF = "/apps/engineering/processes/line-balancing";

const PLANNED_TOOLS: { title: string; description: string }[] = [
  {
    title: "Mapeamento de processos",
    description: "Em planejamento — fluxos e atividades do processo.",
  },
  {
    title: "Melhoria de processos",
    description: "Em planejamento — desperdícios, causa e plano de ação.",
  },
  {
    title: "Estudos de tempos e métodos",
    description: "Em planejamento — cronoanálise e tempos padrão.",
  },
  {
    title: "Capacidade produtiva",
    description: "Em planejamento — capacidade instalada e gargalos.",
  },
  {
    title: "Padronização do trabalho",
    description: "Em planejamento — instruções e trabalho padrão.",
  },
];

export function ProcessesPage({ basePath }: { basePath?: string }) {
  return (
    <>
      <EngineeringPageHero
        aria-label="Engenharia de Processos"
        eyebrow="Processos"
        title="Engenharia de Processos"
        description="Ferramentas para análise, melhoria e otimização dos processos de fabricação."
      />
      <div className="engineering-home-sections-grid">
        <EngineeringSectionRouteCard
          title="Balanceamento de Linha"
          description="Analise o roteiro de fabricação, dimensione a carga de trabalho e construa cenários de organização da linha."
          icon={<Gauge size={20} aria-hidden="true" />}
          routes={[
            {
              id: "line-balancing-open",
              label: "Abrir ferramenta",
              icon: <Gauge size={16} aria-hidden="true" />,
              kind: "navigate",
              onClick: () =>
                navigateGovernedHref(LINE_BALANCING_HREF, { basePath }),
            },
          ]}
        />
        {PLANNED_TOOLS.map((tool) => (
          <EngineeringSectionRouteCard
            key={tool.title}
            title={tool.title}
            description={tool.description}
            icon={<Workflow size={20} aria-hidden="true" />}
            routes={[
              {
                id: tool.title,
                label: "Em planejamento",
                disabled: true,
                badge: "Em breve",
                kind: "navigate",
                onClick: () => {},
              },
            ]}
          />
        ))}
      </div>
    </>
  );
}
