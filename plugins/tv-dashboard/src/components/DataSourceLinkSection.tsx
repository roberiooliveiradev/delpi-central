import { FormSelectControl } from "@delpi/plugin-ui/index";
import {
  dataModelOptionsForInspector,
  dataSourceOptionsForInspector,
  isCanvasTableDataBoundBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isTextDataBoundBlockType,
  listDataSourceBlocks,
  resolveDataSourceLabel,
  type ComunicadoBlock,
  type DataSourceLabelCatalog,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

const H = TV_DASHBOARD_HELP_TOOLTIPS.data;

/** Prefixo de valor no select unificado — `model:{id}` distingue DataModel de fonte. */
export const MODEL_TARGET_PREFIX = "model:";

export function modelSelectValue(modelId: string): string {
  return `${MODEL_TARGET_PREFIX}${modelId}`;
}

export function canLinkBlockToProjectDataSource(
  block: { type: string; shape?: string } | null | undefined,
): boolean {
  if (!block) return false;
  if (block.type === "shape" && block.shape === "efficiency-pin") return true;
  return (
    isDataViewBlockType(block.type) ||
    isTextDataBoundBlockType(block.type) ||
    isCanvasTableDataBoundBlockType(block.type)
  );
}

type LinkSectionProps = {
  blocks: ComunicadoBlock[];
  selectedId?: string;
  sourceId: string;
  /** Binding ativo via `modelId` — vence `sourceId` quando presente. */
  modelId?: string;
  /** DataModels do slide (seletor unificado modelo/fonte). */
  dataModels?: TvDataModel[];
  compactSelect?: string;
  pane?: boolean;
  /** Sem DeckPropertySection — para embutir em «Conexão de dados». */
  embedded?: boolean;
  sectionTitle?: string;
  emptyHint?: string;
  /** Catálogo vivo para rótulos (sem snapshot). */
  labelCatalog?: DataSourceLabelCatalog | null;
  /** Sobrescreve opções (ex.: fontes de eficiência primeiro). */
  sourceOptions?: Array<{ value: string; label: string }>;
  onChangeSourceId: (sourceId: string) => void;
  /** Troca de target para DataModel (write exclusivo: remove dataSourceId). */
  onChangeModelId?: (modelId: string) => void;
  onOpenCatalog?: () => void;
  catalogLabel?: string;
};

/**
 * Seletor canônico: DataModels + fontes já no slide + atalho para catálogo.
 * Usado por texto/forma, KPI/gráfico/tabela e Grade — o mesmo fluxo de binding.
 */
export function DataSourceLinkSection({
  blocks,
  selectedId,
  sourceId,
  modelId = "",
  dataModels,
  compactSelect,
  pane = false,
  embedded = false,
  sectionTitle = "Fonte de dados",
  emptyHint,
  labelCatalog = null,
  sourceOptions: sourceOptionsProp,
  onChangeSourceId,
  onChangeModelId,
  onOpenCatalog,
  catalogLabel = "Inserir nova fonte…",
}: LinkSectionProps) {
  const sourceOptions =
    sourceOptionsProp ?? dataSourceOptionsForInspector(blocks, selectedId, labelCatalog);
  const modelOptions = dataModels ? dataModelOptionsForInspector({ dataModels }) : [];
  const hint =
    emptyHint ??
    (sourceOptions.length === 0 && modelOptions.length === 0
      ? "Insira uma fonte de dados no slide para vincular este bloco."
      : undefined);

  // modelId vence (contrato DM2) — o select expõe um único target ativo.
  const selectValue = modelId.trim() ? modelSelectValue(modelId.trim()) : sourceId;

  const handleChange = (value: string) => {
    if (value.startsWith(MODEL_TARGET_PREFIX)) {
      onChangeModelId?.(value.slice(MODEL_TARGET_PREFIX.length));
      return;
    }
    onChangeSourceId(value);
  };

  const body = (
    <>
      <DeckField label="Fonte">
        <FormSelectControl
          className={compactSelect}
          value={selectValue}
          onChange={handleChange}
          options={[
            {
              value: "",
              label:
                sourceOptions.length === 0 && modelOptions.length === 0
                  ? "Nenhuma fonte no slide"
                  : "Selecione…",
            },
            ...modelOptions.map((item) => ({
              value: modelSelectValue(item.value),
              label: `Modelo · ${item.label}`,
            })),
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
    <DeckPropertySection title={sectionTitle} hint={H.viewBinding} pane={pane}>
      {body}
    </DeckPropertySection>
  );
}

type ProjectSourcesListProps = {
  blocks: ComunicadoBlock[];
  /** Destaca a fonte já ligada (opcional). */
  activeSourceId?: string;
  labelCatalog?: DataSourceLabelCatalog | null;
  onPickSource: (sourceId: string) => void;
  onBrowseCatalog?: () => void;
};

/**
 * Lista «Fontes neste slide» no catálogo — mesmo fluxo de vínculo sem forçar rota nova.
 */
export function ProjectDataSourcesCatalogSection({
  blocks,
  activeSourceId,
  labelCatalog = null,
  onPickSource,
  onBrowseCatalog,
}: ProjectSourcesListProps) {
  const sources = listDataSourceBlocks(blocks);
  if (sources.length === 0) return null;

  return (
    <DeckPropertySection title="Fontes neste slide" hint={H.projectSources} pane>
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
                  {resolveDataSourceLabel(source, labelCatalog)}
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

export type DataModelPreviewStatus = "loading" | "error" | "ready" | "idle";

type DataModelsCatalogSectionProps = {
  dataModels: TvDataModel[];
  /** Destaca o modelo já ligado ao bloco selecionado. */
  activeModelId?: string;
  /** Status do preview por model id (resolved/error/loading do editor). */
  statusById?: Record<string, { status: DataModelPreviewStatus; message?: string }>;
  onPickModel: (modelId: string) => void;
  onInspectModel?: (modelId: string) => void;
};

/**
 * «Modelos de dados neste slide» — UM item lógico por DataModel, independente
 * de quantos inputs compõem o modelo. Selecionar liga o visual ao `modelId`.
 */
export function DataModelsCatalogSection({
  dataModels,
  activeModelId,
  statusById = {},
  onPickModel,
  onInspectModel,
}: DataModelsCatalogSectionProps) {
  if (dataModels.length === 0) return null;

  const statusLabel = (modelId: string): { text: string; tone: string } | null => {
    const entry = statusById[modelId];
    if (!entry || entry.status === "idle") return null;
    if (entry.status === "loading") return { text: "Carregando…", tone: "loading" };
    if (entry.status === "error") return { text: entry.message ?? "Erro no modelo", tone: "error" };
    return { text: "Pronto", tone: "ready" };
  };

  return (
    <DeckPropertySection title="Modelos de dados" hint={H.dataModels} pane>
      <ul className="td-project-sources-list">
        {dataModels.map((model) => {
          const active = model.id === activeModelId;
          const status = statusLabel(model.id);
          const inputCount = model.inputs.length;
          return (
            <li key={model.id}>
              <button
                type="button"
                className={[
                  "td-project-sources-list__item",
                  active ? "td-project-sources-list__item--active" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => onPickModel(model.id)}
                title={model.id}
              >
                <span className="td-project-sources-list__label">
                  {model.label?.trim() || model.id}
                </span>
                <span className="td-project-sources-list__meta">
                  {inputCount === 1 ? "1 rota" : `${inputCount} rotas`}
                  {status ? ` · ${status.text}` : ""}
                </span>
                {active ? (
                  <span className="td-project-sources-list__badge">Em uso</span>
                ) : (
                  <span className="td-project-sources-list__badge">Usar</span>
                )}
              </button>
              {onInspectModel ? (
                <button
                  type="button"
                  className="td-btn td-btn--sm td-btn--ghost td-project-sources-list__inspect"
                  onClick={() => onInspectModel(model.id)}
                >
                  Detalhes
                </button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </DeckPropertySection>
  );
}
