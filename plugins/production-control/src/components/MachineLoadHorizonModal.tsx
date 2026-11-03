import { useEffect, useMemo, useState } from "react";
import { CalendarPlus, Info } from "lucide-react";

import { HostContainedDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { MachineLoadHorizonPreview } from "../types";

const PRESETS = [21, 28, 42] as const;

type Props = {
  open: boolean;
  workCenter: string;
  workCenterName?: string | null;
  baseEndDate: string | null;
  publicationState?: string | null;
  busy?: boolean;
  error?: string | null;
  preview: MachineLoadHorizonPreview | null;
  previewBusy?: boolean;
  onClose: () => void;
  onPreview: (endDate: string) => void;
  onConfirm: (endDate: string) => void;
};

function addDaysIso(days: number): string {
  const now = new Date();
  // Data civil local do analista — o backend revalida no timezone canônico.
  const local = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  local.setDate(local.getDate() + days);
  const y = local.getFullYear();
  const m = String(local.getMonth() + 1).padStart(2, "0");
  const d = String(local.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Modal compacto: presets 21/28/42 + data personalizada + prévia antes de gravar. */
export function MachineLoadHorizonModal({
  open,
  workCenter,
  workCenterName,
  baseEndDate,
  publicationState,
  busy = false,
  error = null,
  preview,
  previewBusy = false,
  onClose,
  onPreview,
  onConfirm,
}: Props) {
  const texts = copy.machineLoad.horizon;
  const [mode, setMode] = useState<"preset" | "custom">("preset");
  const [presetDays, setPresetDays] = useState<(typeof PRESETS)[number]>(28);
  const [customEnd, setCustomEnd] = useState("");

  useEffect(() => {
    if (!open) return;
    setMode("preset");
    setPresetDays(28);
    setCustomEnd(baseEndDate ? addDaysIso(28) : "");
  }, [open, baseEndDate, workCenter]);

  const endDate = useMemo(() => {
    if (mode === "custom") return customEnd;
    return addDaysIso(presetDays);
  }, [mode, customEnd, presetDays]);

  const liveBlocked = publicationState === "live";
  const centerLabel = workCenterName
    ? `${workCenter} — ${workCenterName}`
    : workCenter;

  return (
    <HostContainedDialog open={open} title={texts.modalTitle} onClose={onClose}>
      <div className="ppc-horizon">
        <p className="ppc-horizon__lead">{texts.lead(centerLabel)}</p>
        {baseEndDate ? (
          <p className="ppc-horizon__meta">{texts.baseWindow(baseEndDate)}</p>
        ) : null}

        {liveBlocked ? (
          <p className="ppc-horizon__error" role="alert">
            {texts.liveBlocked}
          </p>
        ) : (
          <>
            <fieldset className="ppc-horizon__group" disabled={busy || previewBusy}>
              <legend className="ppc-horizon__legend">{texts.presetsLegend}</legend>
              <div className="ppc-horizon__presets">
                {PRESETS.map((days) => (
                  <label key={days} className="ppc-horizon__preset">
                    <input
                      type="radio"
                      name="ppc-horizon-preset"
                      checked={mode === "preset" && presetDays === days}
                      onChange={() => {
                        setMode("preset");
                        setPresetDays(days);
                      }}
                    />
                    <span>{texts.presetDays(days)}</span>
                  </label>
                ))}
                <label className="ppc-horizon__preset">
                  <input
                    type="radio"
                    name="ppc-horizon-preset"
                    checked={mode === "custom"}
                    onChange={() => setMode("custom")}
                  />
                  <span>{texts.customLabel}</span>
                </label>
              </div>
              {mode === "custom" ? (
                <label className="ppc-horizon__date">
                  <span className="ppc-visually-hidden">{texts.customLabel}</span>
                  <input
                    type="date"
                    value={customEnd}
                    min={baseEndDate ?? undefined}
                    onChange={(event) => setCustomEnd(event.target.value)}
                  />
                </label>
              ) : null}
            </fieldset>

            <p className="ppc-horizon__note">
              <Info size={13} strokeWidth={1.9} aria-hidden />
              {texts.publishWarning}
            </p>

            {preview ? (
              <div className="ppc-horizon__preview" role="status">
                <p>
                  {texts.additionalRange(
                    preview.additional_start_date,
                    preview.additional_end_date,
                  )}
                </p>
                <p>
                  {preview.new_operation_count > 0
                    ? texts.previewCount(preview.new_operation_count)
                    : texts.previewEmpty}
                </p>
              </div>
            ) : null}

            {error ? (
              <p className="ppc-horizon__error" role="alert">
                {error}
              </p>
            ) : null}

            <div className="ppc-horizon__actions">
              <button
                type="button"
                className="ppc-optimization__cancel"
                onClick={onClose}
                disabled={busy}
              >
                {texts.cancel}
              </button>
              <button
                type="button"
                className="ppc-optimization__cancel"
                disabled={busy || previewBusy || !endDate}
                onClick={() => onPreview(endDate)}
              >
                <CalendarPlus size={14} strokeWidth={1.9} aria-hidden />
                {previewBusy ? texts.previewBusy : texts.previewAction}
              </button>
              <button
                type="button"
                className="ppc-optimization__confirm"
                disabled={busy || previewBusy || !preview || !endDate}
                aria-busy={busy}
                onClick={() => onConfirm(endDate)}
              >
                {busy ? texts.applyBusy : texts.confirm}
              </button>
            </div>
          </>
        )}

        {liveBlocked ? (
          <div className="ppc-horizon__actions">
            <button type="button" className="ppc-optimization__cancel" onClick={onClose}>
              {texts.cancel}
            </button>
          </div>
        ) : null}
      </div>
    </HostContainedDialog>
  );
}
