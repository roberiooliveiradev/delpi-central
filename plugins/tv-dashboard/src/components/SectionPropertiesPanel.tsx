import { useEffect, useState } from "react";
import {
  NativeCheckboxControl,
  NativeTextControl,
  TransitionGallery,
} from "@delpi/plugin-ui/index";
import {
  formatPresentationTransitionLabel,
  PRESENTATION_TRANSITION_STYLES,
  type PresentationTransitionStyle,
} from "@delpi/tv-dashboard-presentation";

import type { PlaylistSection } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { DeckField } from "./deck/DeckField";
import { TdNativeTextField } from "./tdFormFields";
import { TvRibbonColorPicker } from "./deck/TvRibbonColorPicker";
import { HostContainedDialog } from "./ui/Modal";

type Props = {
  section: PlaylistSection;
  open: boolean;
  onClose: () => void;
  onSave: (patch: Partial<PlaylistSection>) => void;
};

const F = TV_DASHBOARD_HELP_TOOLTIPS.fields;
const SECTION_TRANSITION_OPTIONS = [
  {
    id: "",
    label: F.transitionSectionInheritLabel,
    description: F.transitionInheritDescription,
    previewStyle: "fade",
  },
  ...PRESENTATION_TRANSITION_STYLES.map((id) => ({
    id,
    label: formatPresentationTransitionLabel(id),
    description: F.transitionDescriptions[id as PresentationTransitionStyle],
  })),
];

/** Propriedades da seção — controles do plugin-ui (sem select/input crus). */
export function SectionPropertiesPanel({ section, open, onClose, onSave }: Props) {
  const [name, setName] = useState(section.name);
  const [durationDraft, setDurationDraft] = useState(
    section.defaultDurationSec == null ? "" : String(section.defaultDurationSec),
  );

  useEffect(() => {
    setName(section.name);
    setDurationDraft(
      section.defaultDurationSec == null ? "" : String(section.defaultDurationSec),
    );
  }, [section.id, section.name, section.defaultDurationSec]);

  const masterEnabled = Boolean(section.masterConfig?.enabled);
  const masterBg =
    section.masterConfig?.background?.type === "color"
      ? section.masterConfig.background.value || "#0f172a"
      : "#0f172a";

  return (
    <HostContainedDialog
      open={open}
      onClose={onClose}
      title="Propriedades da seção"
      className="td-modal--section-props"
      footer={
        <div className="td-modal-actions td-modal-actions--end">
          <button type="button" className="td-btn td-btn--primary" onClick={onClose}>
            Fechar
          </button>
        </div>
      }
    >
      <div className="td-deck-section-props-form">
        <TdNativeTextField
          id="td-section-name"
          label="Nome"
          value={name}
          onChange={setName}
          onBlur={() => {
            const trimmed = name.trim();
            if (trimmed && trimmed !== section.name) onSave({ name: trimmed });
          }}
        />
        <DeckField id="td-section-duration" label="Duração padrão (s)">
          <NativeTextControl
            id="td-section-duration"
            type="number"
            min={5}
            max={600}
            placeholder="Herdar playlist"
            aria-label="Duração padrão da seção em segundos"
            value={durationDraft}
            onChange={setDurationDraft}
            onBlur={() => {
              const raw = durationDraft.trim();
              onSave({
                defaultDurationSec: raw ? Number(raw) : null,
              });
            }}
          />
        </DeckField>
        <DeckField id="td-section-transition" label="Transição">
          <TransitionGallery
            ariaLabel="Transição da seção"
            value={section.transitionStyle ?? ""}
            options={SECTION_TRANSITION_OPTIONS}
            onChange={(value) => onSave({ transitionStyle: value ? value : null })}
          />
        </DeckField>
        <NativeCheckboxControl
          label="Visível na TV"
          checked={section.isActive !== false}
          onChange={(checked) => onSave({ isActive: checked })}
        />
        <NativeCheckboxControl
          label="Master da seção ativo (fundo/logo)"
          checked={masterEnabled}
          onChange={(checked) =>
            onSave({
              masterConfig: {
                ...(section.masterConfig ?? {}),
                enabled: checked,
              },
            })
          }
        />
        {masterEnabled ? (
          <TvRibbonColorPicker
            label="Cor de fundo da seção"
            value={masterBg}
            onChange={(color) =>
              onSave({
                masterConfig: {
                  ...(section.masterConfig ?? {}),
                  enabled: true,
                  background: { type: "color", value: color },
                },
              })
            }
          />
        ) : null}
      </div>
    </HostContainedDialog>
  );
}
