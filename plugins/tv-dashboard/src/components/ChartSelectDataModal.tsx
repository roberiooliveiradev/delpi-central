import {
  discoverResolvedFieldOptions,
  type ChartViewProjection,
  type ComunicadoChartViewBlock,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import { ChartAxesProjectionEditor, type ChartAxisFieldOption } from "./ChartAxesProjectionEditor";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { Modal } from "./ui/Modal";

type Props = {
  open: boolean;
  onClose: () => void;
  block: ComunicadoChartViewBlock;
};

/**
 * Diálogo Excel «Selecionar dados» — categoria X + séries Y sobre o resultado da Query.
 * Campos vêm de `resolved.table` já calculado no backend (não reaplica steps no browser).
 */
export function ChartSelectDataModal({ open, onClose, block }: Props) {
  const { blocks, updateSelected, selectedChartPart, selectChartPart } = useComunicadoEditor();

  const source = useMemo(() => {
    if (!block.dataSourceId) return null;
    const found = blocks.find((item) => item.id === block.dataSourceId);
    return found?.type === "data_source" ? (found as ComunicadoDataSourceBlock) : null;
  }, [block.dataSourceId, blocks]);

  const fieldOptions: ChartAxisFieldOption[] = useMemo(() => {
    const resolved = source?.resolved ?? block.resolved;
    if (!resolved) return [];
    const columns = resolved.table?.columns ?? [];
    if (columns.length) {
      return columns.map((col) => ({
        field: col.key,
        label: col.label?.trim() || col.key,
      }));
    }
    return discoverResolvedFieldOptions(resolved).map((item) => ({
      field: item.field,
      label: item.label,
    }));
  }, [block.resolved, source]);

  const applyProjection = (next: ChartViewProjection | undefined) => {
    updateSelected({ chartProjection: next } as Partial<ComunicadoChartViewBlock>);
  };

  return (
    <Modal open={open} title="Selecionar dados" onClose={onClose}>
      <p className="td-deck-inspector__hint">
        Escolha a categoria (eixo X) e as séries (eixo Y). Os campos refletem a tabela após Preparar
        dados, quando houver steps na fonte.
      </p>
      {fieldOptions.length === 0 ? (
        <p className="td-deck-inspector__meta">
          Sem campos disponíveis. Conecte uma fonte e atualize o visual.
        </p>
      ) : (
        <ChartAxesProjectionEditor
          idPrefix="td-select-data"
          options={fieldOptions}
          chartProjection={block.chartProjection}
          onChange={applyProjection}
          focusedSeriesField={
            selectedChartPart?.kind === "series"
              ? block.chartProjection?.series?.[selectedChartPart.seriesIndex ?? -1]?.field ?? null
              : null
          }
          onSeriesActivate={(_field, seriesIndex) => {
            selectChartPart(block.id, { kind: "series", seriesIndex });
          }}
        />
      )}
      <div className="td-data-prepare__row" style={{ marginTop: 12, justifyContent: "flex-end" }}>
        <button type="button" className="td-btn td-btn--sm" onClick={onClose}>
          Concluir
        </button>
      </div>
    </Modal>
  );
}
