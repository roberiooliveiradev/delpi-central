import { SelectionSectionsHost } from "./SelectionSectionsHost";
import {
  COMMON_RIBBON_TAIL,
  COMMON_TYPOGRAPHY_PREFIX,
  commonTailForLayout,
} from "./commonSectionPresets";
import type { SelectionSectionId, SelectionSectionLayout } from "./types";

type Labels = Record<string, string>;

type CommonHostProps = {
  layout: SelectionSectionLayout;
  labels?: Labels;
};

/**
 * Host do rabo transversal: Tamanho e posição · Organizar · Ações · (pane) Animação.
 * Intersecta com `resolveSelectionSections` — só renderiza o que a seleção admite.
 */
export function SelectionCommonTailHost({ layout, labels }: CommonHostProps) {
  return (
    <SelectionSectionsHost
      layout={layout}
      labels={labels}
      only={[...commonTailForLayout(layout)]}
    />
  );
}

/**
 * Só frame (quando o consumidor gera o chrome e omite Organize).
 */
export function SelectionFrameHost({ layout, labels }: CommonHostProps) {
  return <SelectionSectionsHost layout={layout} labels={labels} only={["frame"]} />;
}

/**
 * Tipografia + Forma — prefixo compartilhado (texto/heading = mesmo chrome que shape).
 */
export function SelectionTypographyHost({ layout, labels }: CommonHostProps) {
  return (
    <SelectionSectionsHost
      layout={layout}
      labels={labels}
      only={[...COMMON_TYPOGRAPHY_PREFIX]}
    />
  );
}

/**
 * Design tipado (sem rabo) + rabo comum no mesmo host.
 * Ex.: chart Design, table Design no painel/ribbon.
 */
export function SelectionTypedWithTailHost({
  layout,
  typed,
  labels,
  lightTail = false,
}: CommonHostProps & {
  typed: SelectionSectionId[];
  /** true → só display+organize+actions (sem animação). */
  lightTail?: boolean;
}) {
  const tail: SelectionSectionId[] = lightTail
    ? [...COMMON_RIBBON_TAIL]
    : [...commonTailForLayout(layout)];
  return (
    <SelectionSectionsHost
      layout={layout}
      labels={labels}
      only={[...typed, ...tail]}
    />
  );
}
