import { useMemo, useState } from "react";
import {
  discoverResolvedFieldOptions,
  resolveDataBlockErrorText,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useTvDataRouteLabelCatalog } from "../hooks/useTvDataRouteLabelCatalog";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  model: TvDataModel;
  pane?: boolean;
  layout?: PanelLayout;
};

/**
 * Inspector de DataModel — objeto lógico de dados (nunca visual).
 * Inspect inputs/transform, preview output (ready/loading/error/empty),
 * rename label e delete via mutation ops do backend.
 */
export function DataModelInspector({ model, pane = false, layout = "pane" }: Props) {
  const {
    getDataPreviewResolved,
    refreshingSourceIds,
    refreshDataPreview,
    saveDataModel,
    deleteDataModel,
  } = useComunicadoEditor();
  const { routes } = useTvDataRouteLabelCatalog();
  const isRibbon = layout === "ribbon";

  const [labelDraft, setLabelDraft] = useState(model.label ?? "");
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const resolved = getDataPreviewResolved?.(model.id);
  const loading = refreshingSourceIds.includes(model.id);
  const errorText = resolveDataBlockErrorText(resolved);

  const outputFields = useMemo(
    () => discoverResolvedFieldOptions(resolved, undefined, model.fieldLabels),
    [resolved, model.fieldLabels],
  );

  const routeLabelById = useMemo(() => {
    const map = new Map<string, string>();
    for (const route of routes) {
      if (route.operationId) map.set(route.operationId, route.label ?? route.operationId);
    }
    return map;
  }, [routes]);

  const isEmpty =
    !loading &&
    !errorText &&
    resolved != null &&
    outputFields.length === 0;

  const status = loading
    ? "Carregando modelo…"
    : errorText
      ? `Erro no modelo: ${errorText}`
      : isEmpty
        ? "Resultado vazio — o modelo respondeu sem campos."
        : resolved
          ? "Pronto"
          : "Sem preview ainda — atualize para carregar.";

  const saveLabel = () => {
    const next = { ...model, label: labelDraft.trim() || undefined };
    if (next.label === model.label) return;
    setBusy(true);
    setActionError(null);
    void saveDataModel(next)
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : "Falha ao salvar o modelo.");
      })
      .finally(() => setBusy(false));
  };

  const onDelete = () => {
    setBusy(true);
    setActionError(null);
    void deleteDataModel(model.id)
      .catch((err: unknown) => {
        setActionError(
          err instanceof Error ? err.message : "Não foi possível excluir o modelo.",
        );
      })
      .finally(() => setBusy(false));
  };

  if (isRibbon) {
    return (
      <p className="td-deck-inspector__hint">
        Modelo «{model.label?.trim() || model.id}» — {model.inputs.length} rota(s). Detalhes no
        painel Dados.
      </p>
    );
  }

  return (
    <>
      <DeckPropertySection
        pane={pane}
        title="Modelo de dados"
        hint={TV_DASHBOARD_HELP_TOOLTIPS.data.modelInspector}
        defaultOpen
      >
        <p className="td-deck-inspector__meta" title={model.id}>
          {model.inputs.length === 1
            ? "1 rota de dados"
            : `${model.inputs.length} rotas de dados`}
          {model.transform ? " · transform" : ""}
        </p>
        <DeckField label="Nome do modelo">
          <div className="td-deck-ribbon__toolbar-row">
            <NativeTextControl
              value={labelDraft}
              onChange={setLabelDraft}
              placeholder={model.id}
            />
            <button
              type="button"
              className="td-btn td-btn--sm"
              disabled={busy}
              onClick={saveLabel}
            >
              Salvar
            </button>
          </div>
        </DeckField>
        <p
          className={
            errorText
              ? "td-deck-inspector__hint td-deck-inspector__hint--error"
              : "td-deck-inspector__hint"
          }
          role={errorText ? "alert" : undefined}
        >
          {status}
        </p>
        {actionError ? (
          <p className="td-deck-inspector__hint td-deck-inspector__hint--error" role="alert">
            {actionError}
          </p>
        ) : null}
        <div className="td-deck-ribbon__toolbar-row">
          <button
            type="button"
            className="td-btn td-btn--sm"
            disabled={loading}
            onClick={() =>
              void refreshDataPreview({ force: true, blockIds: [model.id] })
            }
          >
            {loading ? "Carregando…" : "Atualizar preview"}
          </button>
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            disabled={busy}
            onClick={onDelete}
          >
            Excluir modelo
          </button>
        </div>
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title="Rotas do modelo" defaultOpen={false}>
        <ul className="td-project-sources-list">
          {model.inputs.map((input) => (
            <li key={input.id} className="td-project-sources-list__item--static">
              <span className="td-project-sources-list__label">
                {input.label?.trim() || routeLabelById.get(input.operationId) || input.operationId}
              </span>
              <span className="td-project-sources-list__meta">
                {input.operationId}
                {input.id === model.primaryInputId ? " · principal" : ""}
                {input.transform ? " · transform" : ""}
                {input.params && Object.keys(input.params).length > 0
                  ? ` · ${Object.keys(input.params).length} parâmetro(s)`
                  : ""}
              </span>
            </li>
          ))}
        </ul>
      </DeckPropertySection>

      {outputFields.length > 0 ? (
        <DeckPropertySection pane={pane} title="Campos de saída" defaultOpen={false}>
          <ul className="td-project-sources-list">
            {outputFields.map((item) => (
              <li key={item.field} className="td-project-sources-list__item--static">
                <span className="td-project-sources-list__label">{item.label}</span>
                <span className="td-project-sources-list__meta">{item.field}</span>
              </li>
            ))}
          </ul>
        </DeckPropertySection>
      ) : null}
    </>
  );
}
