import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  EFFICIENCY_PIN_DEFAULT_GOOD_MIN_PCT,
  EFFICIENCY_PIN_DEFAULT_VALID_MAX_PCT,
  EFFICIENCY_PIN_DEFAULT_WARN_MIN_PCT,
  EFFICIENCY_PIN_OPERATION_ID,
  applyEfficiencyPinBandsToSharedPins,
  applySharedDataSourceToUnlinkedEfficiencyPins,
  buildEfficiencyPinInfoBlock,
  dataSourceOptionsForInspector,
  findSharedEfficiencyPinBands,
  findSharedEfficiencyPinDataSourceId,
  isDataSourceBlockType,
  isEfficiencyPinBlock,
  isEfficiencyPinInfoRole,
  listWorkCentersFromResolved,
  resolveEfficiencyPinBands,
  resolveEfficiencyPinInfoMode,
  resolveEfficiencyPinRole,
  type ComunicadoEfficiencyPinBinding,
  type ComunicadoEfficiencyPinInfoMode,
  type ComunicadoShapeBlock,
} from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import { DataSourceLinkSection } from "./DataSourceLinkSection";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import type { PanelLayout } from "./SelectedDataSidePanel";
import { DeckField } from "./deck/DeckField";
import { DeckPropertySection } from "./deck/DeckPropertySection";

type Props = {
  pane?: boolean;
  layout?: PanelLayout;
  onOpenDataSources?: () => void;
};

export function canShowEfficiencyPinInspector(
  selected: { type?: string; shape?: string } | null | undefined,
): boolean {
  return isEfficiencyPinBlock(selected as never);
}

export function EfficiencyPinInspector({
  pane = false,
  layout = "pane",
  onOpenDataSources,
}: Props) {
  const {
    selected,
    blocks,
    updateSelected,
    updateBlock,
    updateBlocks,
    openDataCatalog,
    addPreparedShapeBlock,
    selectBlock,
  } = useComunicadoEditor();
  const isRibbon = layout === "ribbon";
  const compactSelect = isRibbon ? "delpi-ui-select--compact" : undefined;
  const compactNative = isRibbon ? "delpi-ui-native-control--compact" : undefined;

  const pin = selected && isEfficiencyPinBlock(selected) ? selected : null;
  const binding = pin?.efficiencyPin ?? {};
  const role = resolveEfficiencyPinRole(binding);
  const infoMode = resolveEfficiencyPinInfoMode(binding);
  const bands = resolveEfficiencyPinBands(binding.bands);
  const sourceId = pin?.dataSourceId?.trim() ?? "";
  const sharedSourceId = useMemo(() => findSharedEfficiencyPinDataSourceId(blocks), [blocks]);
  const linkedSource = sourceId ? blocks.find((block) => block.id === sourceId) ?? null : null;
  const resolved =
    linkedSource && "resolved" in linkedSource && linkedSource.resolved
      ? linkedSource.resolved
      : pin?.resolved;

  const linkedInfo = useMemo(() => {
    if (!pin || role === "info") return null;
    const linkedId = binding.linkedBlockId?.trim();
    if (linkedId) {
      const found = blocks.find((block) => block.id === linkedId);
      if (found && isEfficiencyPinBlock(found) && isEfficiencyPinInfoRole(found.efficiencyPin)) {
        return found;
      }
    }
    return (
      blocks.find(
        (block) =>
          isEfficiencyPinBlock(block) &&
          isEfficiencyPinInfoRole(block.efficiencyPin) &&
          block.efficiencyPin?.linkedBlockId === pin.id,
      ) ?? null
    );
  }, [binding.linkedBlockId, blocks, pin, role]);

  const workCenters = useMemo(() => listWorkCentersFromResolved(resolved), [resolved]);
  const workCenterOptions = useMemo(() => {
    const options = workCenters.map((value) => ({ value, label: value }));
    const current = binding.workCenter?.trim();
    if (current && !workCenters.includes(current)) {
      options.unshift({ value: current, label: `${current} (não encontrado na fonte)` });
    }
    return [{ value: "", label: "Selecionar CT…" }, ...options];
  }, [binding.workCenter, workCenters]);

  const sourceOptionsSorted = useMemo(() => {
    const options = dataSourceOptionsForInspector(blocks, pin?.id);
    return [...options].sort((a, b) => {
      const aBlock = blocks.find((block) => block.id === a.value);
      const bBlock = blocks.find((block) => block.id === b.value);
      const aEff =
        aBlock &&
        isDataSourceBlockType(aBlock.type) &&
        aBlock.dataBinding?.operationId === EFFICIENCY_PIN_OPERATION_ID
          ? 0
          : 1;
      const bEff =
        bBlock &&
        isDataSourceBlockType(bBlock.type) &&
        bBlock.dataBinding?.operationId === EFFICIENCY_PIN_OPERATION_ID
          ? 0
          : 1;
      return aEff - bEff || a.label.localeCompare(b.label, "pt-BR");
    });
  }, [blocks, pin?.id]);

  function patchEfficiencyPin(patch: Partial<ComunicadoEfficiencyPinBinding>) {
    if (!pin) return;
    const nextBands = patch.bands ? { ...binding.bands, ...patch.bands } : binding.bands;
    const next: ComunicadoEfficiencyPinBinding = {
      ...binding,
      ...patch,
      ...(nextBands ? { bands: nextBands } : {}),
    };
    const selectedPatch = {
      ...pin,
      efficiencyPin: next,
      content: next.workCenter?.trim() || pin.content || "",
    } as ComunicadoShapeBlock;
    /* Faixas de cor: uma regra para o mapa — propaga aos pins da mesma fonte. */
    if (patch.bands && nextBands) {
      const withSelected = blocks.map((block) => (block.id === pin.id ? selectedPatch : block));
      updateBlocks(
        applyEfficiencyPinBandsToSharedPins(withSelected, nextBands, {
          sourceId: pin.dataSourceId,
        }),
      );
      return;
    }
    updateSelected({
      efficiencyPin: next,
      content: next.workCenter?.trim() || pin.content || "",
    } as Partial<ComunicadoShapeBlock>);
  }

  function linkSource(nextSourceId: string) {
    if (!pin) return;
    const trimmed = nextSourceId.trim();
    const inheritedBands = trimmed
      ? findSharedEfficiencyPinBands(blocks, trimmed) ?? binding.bands
      : binding.bands;
    const withSelected = blocks.map((block) =>
      block.id === pin.id
        ? ({
            ...block,
            dataSourceId: trimmed || undefined,
            textProjection: undefined,
            efficiencyPin: {
              ...(block.efficiencyPin ?? {}),
              ...(inheritedBands ? { bands: inheritedBands } : {}),
            },
          } as typeof block)
        : block,
    );
    updateBlocks(
      trimmed
        ? applySharedDataSourceToUnlinkedEfficiencyPins(withSelected, trimmed)
        : withSelected,
    );
  }

  function useSharedSource() {
    if (!pin || !sharedSourceId) return;
    linkSource(sharedSourceId);
  }

  function setInfoMode(mode: ComunicadoEfficiencyPinInfoMode) {
    if (!pin || role === "info") return;
    if (mode === "detached") {
      if (linkedInfo) {
        patchEfficiencyPin({
          infoMode: "detached",
          showLabel: false,
          linkedBlockId: linkedInfo.id,
        });
        updateBlock(linkedInfo.id, {
          dataSourceId: pin.dataSourceId,
          efficiencyPin: {
            ...(linkedInfo.efficiencyPin ?? {}),
            workCenter: binding.workCenter,
            bands: binding.bands,
            role: "info",
            infoMode: "detached",
            linkedBlockId: pin.id,
            showLabel: true,
          },
          content: binding.workCenter?.trim() || linkedInfo.content || "",
        } as Partial<ComunicadoShapeBlock>);
        return;
      }
      const infoBlock = buildEfficiencyPinInfoBlock(pin);
      patchEfficiencyPin({
        infoMode: "detached",
        showLabel: false,
        linkedBlockId: infoBlock.id,
      });
      addPreparedShapeBlock(infoBlock);
      return;
    }
    patchEfficiencyPin({
      infoMode: mode,
      showLabel: mode === "attached",
    });
  }

  if (!pin) return null;

  const sourceHint =
    linkedSource &&
    isDataSourceBlockType(linkedSource.type) &&
    linkedSource.dataBinding?.operationId &&
    linkedSource.dataBinding.operationId !== EFFICIENCY_PIN_OPERATION_ID
      ? `Fonte atual: ${linkedSource.dataBinding.operationId}. Prefira ${EFFICIENCY_PIN_OPERATION_ID}.`
      : null;

  const hasSlideSources = sourceOptionsSorted.length > 0;

  return (
    <>
      <DeckPropertySection
        title={role === "info" ? "Info CT (planta)" : "Pin CT (planta)"}
        pane={pane}
        defaultOpen
      >
        <p className="td-deck-inspector__hint">
          {role === "info"
            ? "Cartão de texto separado — arraste e redimensione pelos handles."
            : "Uma fonte de eficiência por CT no slide basta: cada pin só escolhe o centro de trabalho. Arraste os handles para o tamanho do radar."}
        </p>
        {!sourceId && sharedSourceId ? (
          <button type="button" className="td-btn td-btn--sm" onClick={useSharedSource}>
            Usar fonte já no slide
          </button>
        ) : null}
        <DataSourceLinkSection
          blocks={blocks}
          selectedId={pin.id}
          sourceId={sourceId}
          compactSelect={compactSelect}
          pane={pane}
          embedded
          sourceOptions={sourceOptionsSorted}
          emptyHint={
            hasSlideSources
              ? "Selecione a mesma fonte nos outros pins — não é preciso inserir outra."
              : "Insira uma vez a rota de eficiência por CT; os próximos pins reutilizam essa fonte."
          }
          onChangeSourceId={linkSource}
          onOpenCatalog={onOpenDataSources ?? (() => openDataCatalog("insert"))}
          catalogLabel={
            hasSlideSources ? "Inserir outra fonte…" : "Inserir fonte de eficiência…"
          }
        />
        {sourceHint ? <p className="td-deck-inspector__hint">{sourceHint}</p> : null}
        <DeckField label="Centro de trabalho">
          <FormSelectControl
            className={compactSelect}
            value={binding.workCenter ?? ""}
            options={workCenterOptions}
            onChange={(value) => {
              patchEfficiencyPin({ workCenter: value || undefined });
              if (role === "pin" && linkedInfo) {
                updateBlock(linkedInfo.id, {
                  content: value || linkedInfo.content || "",
                  efficiencyPin: {
                    ...(linkedInfo.efficiencyPin ?? {}),
                    workCenter: value || undefined,
                    linkedBlockId: pin.id,
                    role: "info",
                  },
                } as Partial<ComunicadoShapeBlock>);
              }
            }}
          />
        </DeckField>
        {role === "pin" ? (
          <DeckField label="Informação (CT / %)">
            <FormSelectControl
              className={compactSelect}
              value={infoMode}
              options={[
                { value: "attached", label: "Junto do pin" },
                { value: "detached", label: "Elemento separado" },
                { value: "hidden", label: "Ocultar" },
              ]}
              onChange={(value) => setInfoMode(value as ComunicadoEfficiencyPinInfoMode)}
            />
          </DeckField>
        ) : null}
        {role === "pin" && infoMode === "detached" && linkedInfo ? (
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => selectBlock(linkedInfo.id)}
          >
            Selecionar rótulo separado
          </button>
        ) : null}
        {role === "info" && binding.linkedBlockId ? (
          <button
            type="button"
            className="td-btn td-btn--sm td-btn--ghost"
            onClick={() => selectBlock(binding.linkedBlockId!)}
          >
            Selecionar pin (radar)
          </button>
        ) : null}
      </DeckPropertySection>
      <DeckPropertySection title="Faixas do radar" pane={pane} defaultOpen={false}>
        <p className="td-deck-inspector__hint">
          Compartilhadas com todos os pins da mesma fonte. Verde ≥ Bom · amarelo ≥ Atenção e &lt;
          Bom · vermelho &lt; Atenção · laranja fora do máx. válido.
        </p>
        <DeckField label={`Bom (verde) ≥ % — padrão ${EFFICIENCY_PIN_DEFAULT_GOOD_MIN_PCT}`}>
          <NativeTextControl
            className={compactNative}
            type="number"
            value={String(bands.goodMinPct)}
            onChange={(value) => {
              const n = Number(value);
              patchEfficiencyPin({
                bands: {
                  goodMinPct: Number.isFinite(n) ? n : EFFICIENCY_PIN_DEFAULT_GOOD_MIN_PCT,
                },
              });
            }}
          />
        </DeckField>
        <DeckField
          label={`Atenção (amarelo) ≥ % — abaixo = vermelho (padrão ${EFFICIENCY_PIN_DEFAULT_WARN_MIN_PCT})`}
        >
          <NativeTextControl
            className={compactNative}
            type="number"
            value={String(bands.warnMinPct)}
            onChange={(value) => {
              const n = Number(value);
              patchEfficiencyPin({
                bands: {
                  warnMinPct: Number.isFinite(n) ? n : EFFICIENCY_PIN_DEFAULT_WARN_MIN_PCT,
                },
              });
            }}
          />
        </DeckField>
        <DeckField label={`Máx. válido % (padrão ${EFFICIENCY_PIN_DEFAULT_VALID_MAX_PCT})`}>
          <NativeTextControl
            className={compactNative}
            type="number"
            value={String(bands.validMaxPct)}
            onChange={(value) => {
              const n = Number(value);
              patchEfficiencyPin({
                bands: {
                  validMaxPct: Number.isFinite(n) ? n : EFFICIENCY_PIN_DEFAULT_VALID_MAX_PCT,
                },
              });
            }}
          />
        </DeckField>
      </DeckPropertySection>
    </>
  );
}
