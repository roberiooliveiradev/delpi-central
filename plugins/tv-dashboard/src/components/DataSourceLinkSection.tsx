import { FormSelectControl } from "@delpi/plugin-ui/index";
import {
  dataSourceOptionsForInspector,
  isDataSourceBlockType,
  isDataViewBlockType,
  isTextDataBoundBlockType,
  listDataSourceBlocks,
  resolveDataSourceLabel,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

const H = TV_DASHBOARD_HELP_TOOLTIPS.data;

export function canLinkBlockToProjectDataSource(
  block: { type: string } | null | undefined,
): boolean {
  if (!block) return false;
  return isDataViewBlockType(block.type) || isTextDataBoundBlockType(block.type);
}

type LinkSectionProps = {
  blocks: ComunicadoBlock[];
  selectedId?: string;
  sourceId: string;
  compactSelect?: string;
  pane?: boolean;
  /** Sem DeckPropertySection — para embutir em «Conexão de dados». */
  embedded?: boolean;
  sectionTitle?: string;
  emptyHint?: string;
  onChangeSourceId: (sourceId: string) => void;
  onOpenCatalog?: () => void;
  catalogLabel?: string;
};

/**
 * Seletor canônico: fontes já no slide + atalho para catálogo (nova).
 * Usado por texto/forma, KPI/gráfico/tabela e cabeçalho do catálogo.
 */
export function DataSourceLinkSection({
  blocks,
  selectedId,
  sourceId,
  compactSelect,
  pane = false,
  embedded = false,
  sectionTitle = "Fonte de dados",
  emptyHint,
  onChangeSourceId,
  onOpenCatalog,
  catalogLabel = "Inserir nova fonte…",
}: LinkSectionProps) {
  const sourceOptions = dataSourceOptionsForInspector(blocks, selectedId);
  const hint =
    emptyHint ??
    (sourceOptions.length === 0
      ? "Insira uma fonte de dados no slide para vincular este bloco."
      : undefined);

  const body = (
    <>
      <DeckField label="Fonte">
        <FormSelectControl
          className={compactSelect}
          value={sourceId}
          onChange={onChangeSourceId}
          options={[
            {
              value: "",
              label:
                sourceOptions.length === 0 ? "Nenhuma fonte no slide" : "Selecione…",
            },
            ...sourceOptions.map((item) => ({ value: item.value, label: item.label })),
          ]}
        />
      </DeckField>
      {hint ? <p className="td-deck-inspector__hint">{hint}</p> : null}
      {onOpenCatalog ? (
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onOpenCatalog}>
          {catalogLabel}
        </button>
      ) : null}
    </>
  );

  if (embedded) return body;

  return (
    <DeckPropertySection title={sectionTitle} hint={H.viewBinding} compact={pane}>
      {body}
    </DeckPropertySection>
  );
}

type ProjectSourcesListProps = {
  blocks: ComunicadoBlock[];
  /** Destaca a fonte já ligada (opcional). */
  activeSourceId?: string;
  onPickSource: (sourceId: string) => void;
  onBrowseCatalog?: () => void;
};

/**
 * Lista «Fontes neste slide» no catálogo — mesmo fluxo de vínculo sem forçar rota nova.
 */
export function ProjectDataSourcesCatalogSection({
  blocks,
  activeSourceId,
  onPickSource,
  onBrowseCatalog,
}: ProjectSourcesListProps) {
  const sources = listDataSourceBlocks(blocks);
  if (sources.length === 0) return null;

  return (
    <DeckPropertySection title="Fontes neste slide" hint={H.projectSources} compact>
      <ul className="td-project-sources-list">
        {sources.map((source) => {
          const active = source.id === activeSourceId;
          return (
            <li key={source.id}>
              <button
                type="button"
                className={[
                  "td-project-sources-list__item",
                  active ? "td-project-sources-list__item--active" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onPickSource(source.id)}
              >
                <span className="td-project-sources-list__label">
                  {resolveDataSourceLabel(source)}
                </span>
                {isDataSourceBlockType(source.type) && source.dataBinding.operationId ? (
                  <span className="td-project-sources-list__meta">
                    {source.dataBinding.operationId}
                  </span>
                ) : null}
                {active ? (
                  <span className="td-project-sources-list__badge">Em uso</span>
                ) : (
                  <span className="td-project-sources-list__badge">Usar</span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
      <p className="td-deck-inspector__hint">
        Ou escolha uma rota nova no catálogo abaixo.
      </p>
      {onBrowseCatalog ? (
        <button type="button" className="td-btn td-btn--sm td-btn--ghost" onClick={onBrowseCatalog}>
          Ir para o catálogo
        </button>
      ) : null}
    </DeckPropertySection>
  );
}
