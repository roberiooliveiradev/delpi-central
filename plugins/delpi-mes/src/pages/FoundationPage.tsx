import { EmptyState, emptyStatePanelBemClasses } from "@delpi/plugin-ui/index";

import { DELPI_MES_COPY } from "../content/copy";
import type { DelpiMesArea } from "../constants/routes";

const COPY_BY_AREA = {
  monitoring: DELPI_MES_COPY.monitoring,
  downtimes: DELPI_MES_COPY.downtimes,
  history: DELPI_MES_COPY.history,
} as const;

export function FoundationPage({ area }: { area: Exclude<DelpiMesArea, "registrations"> }) {
  const content = COPY_BY_AREA[area];
  return (
    <section className="delpi-mes-page" aria-labelledby="delpi-mes-page-title">
      <div className="delpi-mes-page__heading">
        <p className="delpi-mes-eyebrow">Fundação gerencial MES</p>
        <h2 id="delpi-mes-page-title">{content.title}</h2>
        <p>{content.description}</p>
      </div>
      <EmptyState
        title="Estrutura integrada à Minha DELPI"
        message={content.guidance}
        defaultMessage={content.guidance}
        classNames={emptyStatePanelBemClasses("delpi-mes")}
        role="status"
      />
    </section>
  );
}
