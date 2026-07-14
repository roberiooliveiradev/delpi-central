import { FormSelectControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  BLOCK_ENTRANCE_DELAY_MAX_MS,
  BLOCK_ENTRANCE_DELAY_MIN_MS,
  BLOCK_ENTRANCE_DELAY_STEP_MS,
  BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
  BLOCK_ENTRANCE_DURATION_MAX_MS,
  BLOCK_ENTRANCE_DURATION_MIN_MS,
  BLOCK_ENTRANCE_DURATION_STEP_MS,
  BLOCK_ENTRANCE_PRESET_OPTIONS,
  entranceAnimationFromPreset,
  entrancePresetValue,
  resolveEntranceAnimation,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "../deck/DeckField";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

/**
 * Animação de entrada — painel colapsável (ribbon omite).
 */
export function AnimationSection({ layout }: { layout: SelectionSectionLayout }) {
  const { selected, selectedIds, updateSelected } = useComunicadoEditor();
  if (layout === "ribbon") return null;
  if (!selected || selectedIds.length > 1) return null;

  const entrance = resolveEntranceAnimation(selected.animations);

  return (
    <SelectionPaneSection title="Animação de entrada" hint={E.entranceAnimation} defaultOpen={false}>
      <DeckField id="td-entrance-kind" label="Efeito" hint={E.entranceAnimation}>
        <FormSelectControl
          id="td-entrance-kind"
          ariaLabel="Efeito"
          value={entrancePresetValue(entrance)}
          onChange={(value) => {
            const current = resolveEntranceAnimation(selected.animations);
            updateSelected({
              animations: entranceAnimationFromPreset(value, {
                delayMs: current?.delayMs ?? 0,
                durationMs: current?.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
              }),
            } as Partial<ComunicadoBlock>);
          }}
          options={BLOCK_ENTRANCE_PRESET_OPTIONS.map((option) => ({
            value: option.value,
            label: option.label,
          }))}
        />
      </DeckField>
      {entrance ? (
        <>
          <DeckField id="td-entrance-delay" label="Atraso (ms)" hint={E.entranceDelay}>
            <NativeTextControl
              id="td-entrance-delay"
              type="number"
              min={BLOCK_ENTRANCE_DELAY_MIN_MS}
              max={BLOCK_ENTRANCE_DELAY_MAX_MS}
              step={BLOCK_ENTRANCE_DELAY_STEP_MS}
              value={entrance.delayMs ?? 0}
              onChange={(value) => {
                const current = resolveEntranceAnimation(selected.animations);
                if (!current) return;
                updateSelected({
                  animations: entranceAnimationFromPreset(entrancePresetValue(current), {
                    delayMs: Number(value),
                    durationMs: current.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
                  }),
                } as Partial<ComunicadoBlock>);
              }}
            />
          </DeckField>
          <DeckField id="td-entrance-duration" label="Duração (ms)" hint={E.entranceDuration}>
            <NativeTextControl
              id="td-entrance-duration"
              type="number"
              min={BLOCK_ENTRANCE_DURATION_MIN_MS}
              max={BLOCK_ENTRANCE_DURATION_MAX_MS}
              step={BLOCK_ENTRANCE_DURATION_STEP_MS}
              value={entrance.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS}
              onChange={(value) => {
                const current = resolveEntranceAnimation(selected.animations);
                if (!current) return;
                updateSelected({
                  animations: entranceAnimationFromPreset(entrancePresetValue(current), {
                    delayMs: current.delayMs ?? 0,
                    durationMs: Number(value),
                  }),
                } as Partial<ComunicadoBlock>);
              }}
            />
          </DeckField>
        </>
      ) : null}
    </SelectionPaneSection>
  );
}
