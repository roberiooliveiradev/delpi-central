import { useCallback, useEffect, useState } from "react";

import {
  fetchStockBalancesEmailSchedule,
  saveStockBalancesEmailSchedule,
  type StockBalancesEmailSchedule,
} from "../api/ppcApi";
import { HostContainedDialog } from "./PpcConfirmModal";
import { copy } from "../content/copy";
import type { PpcBranch } from "../types";

type Props = {
  branch: PpcBranch;
  open: boolean;
  onClose: () => void;
};

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

function toTimeValue(hour: number, minute: number): string {
  return `${pad2(hour)}:${pad2(minute)}`;
}

function parseTimeValue(value: string): { hour: number; minute: number } | null {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (hour < 0 || hour > 23 || minute < 0 || minute > 59) return null;
  return { hour, minute };
}

export function PpcStockBalancesEmailSchedule({ branch, open, onClose }: Props) {
  const texts = copy.reports.stockBalances;
  const [schedule, setSchedule] = useState<StockBalancesEmailSchedule | null>(null);
  const [enabled, setEnabled] = useState(false);
  const [timeValue, setTimeValue] = useState("07:00");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSavedMessage(null);
    fetchStockBalancesEmailSchedule({ branch, signal: controller.signal })
      .then((payload) => {
        setSchedule(payload);
        setEnabled(Boolean(payload.enabled && payload.configured));
        setTimeValue(toTimeValue(payload.hour, payload.minute));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : texts.scheduleLoadError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, open, texts.scheduleLoadError]);

  const onSave = useCallback(async () => {
    const parsed = parseTimeValue(timeValue);
    if (!parsed) {
      setError(texts.scheduleSaveError);
      return;
    }
    setSaving(true);
    setError(null);
    setSavedMessage(null);
    try {
      const payload = await saveStockBalancesEmailSchedule({
        branch,
        hour: parsed.hour,
        minute: parsed.minute,
        enabled,
      });
      setSchedule(payload);
      setEnabled(Boolean(payload.enabled));
      setTimeValue(toTimeValue(payload.hour, payload.minute));
      setSavedMessage(texts.scheduleSaved);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : texts.scheduleSaveError);
    } finally {
      setSaving(false);
    }
  }, [branch, enabled, texts.scheduleSaveError, texts.scheduleSaved, timeValue]);

  return (
    <HostContainedDialog open={open} title={texts.scheduleTitle} onClose={onClose}>
      <div className="ppc-email-schedule" aria-label={texts.scheduleTitle}>
        <p className="ppc-email-schedule__hint">{texts.scheduleHint}</p>

        {loading ? (
          <p className="ppc-email-schedule__status">{copy.table.loading}</p>
        ) : (
          <div className="ppc-email-schedule__form">
            <label className="ppc-email-schedule__field ppc-email-schedule__field--toggle">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(event) => setEnabled(event.target.checked)}
              />
              <span>{texts.scheduleEnabledLabel}</span>
            </label>

            <div className="ppc-email-schedule__field">
              <span className="ppc-email-schedule__label">{texts.schedulePeriodLabel}</span>
              <strong className="ppc-email-schedule__value">{texts.schedulePeriodValue}</strong>
            </div>

            <label className="ppc-email-schedule__field">
              <span className="ppc-email-schedule__label">{texts.scheduleTimeLabel}</span>
              <input
                type="time"
                value={timeValue}
                onChange={(event) => setTimeValue(event.target.value)}
                disabled={saving}
              />
            </label>

            <div className="ppc-email-schedule__actions">
              <button
                type="button"
                className="ppc-period-filter__btn ppc-period-filter__btn--primary"
                onClick={() => void onSave()}
                disabled={saving}
              >
                {saving ? texts.scheduleSaving : texts.scheduleSave}
              </button>
            </div>

            {schedule?.nextRunAt && enabled ? (
              <p className="ppc-email-schedule__meta">
                {texts.scheduleNextRun(new Date(schedule.nextRunAt).toLocaleString("pt-BR"))}
              </p>
            ) : null}
          </div>
        )}

        {error ? (
          <p className="ppc-email-schedule__error" role="alert">
            {error}
          </p>
        ) : null}
        {savedMessage ? (
          <p className="ppc-email-schedule__ok" role="status">
            {savedMessage}
          </p>
        ) : null}
      </div>
    </HostContainedDialog>
  );
}
