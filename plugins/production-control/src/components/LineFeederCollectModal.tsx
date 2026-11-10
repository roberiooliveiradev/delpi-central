import { useCallback, useEffect, useMemo, useState } from "react";

import { httpErrorStatus } from "../api/httpClient";
import { fetchLineFeederPublishedQueue } from "../api/ppcApi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import type { LineFeederPublishedWorkCenter, PpcBranch } from "../types";
import {
  LINE_FEEDER_MAX_HOURS,
  readPreferredLineFeederHours,
  savePreferredLineFeederHours,
} from "../utils/lineFeederHourPreference";
import { HostContainedWideDialog } from "./PpcConfirmModal";
import { LineFeederWorkCenterMultiSelect } from "./lineFeederUi";

const HOUR_SHORTCUTS = [1, 2, 3, 4] as const;
const MAX_HOURS = LINE_FEEDER_MAX_HOURS;

export type LineFeederCollectSelection = {
  workCenters: string[];
  hoursPerWorkCenter: number;
};

type Props = {
  open: boolean;
  branch: PpcBranch;
  initial?: LineFeederCollectSelection | null;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: (selection: LineFeederCollectSelection) => void;
};

function parseHours(raw: string): number | null {
  const normalized = raw.trim().replace(",", ".");
  if (!normalized) return null;
  const value = Number(normalized);
  if (!Number.isFinite(value) || value <= 0) return null;
  return value;
}

export function LineFeederCollectModal({
  open,
  branch,
  initial,
  submitting = false,
  onClose,
  onSubmit,
}: Props) {
  const texts = copy.lineFeeder.collectModal;
  const [centers, setCenters] = useState<LineFeederPublishedWorkCenter[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [hoursRaw, setHoursRaw] = useState("3");
  const [loadingCenters, setLoadingCenters] = useState(false);
  const [centersError, setCentersError] = useState<string | null>(null);
  const [noPublication, setNoPublication] = useState(false);

  const loadCenters = useCallback(async (signal?: AbortSignal) => {
    setLoadingCenters(true);
    setCentersError(null);
    setNoPublication(false);
    try {
      const payload = await fetchLineFeederPublishedQueue({ branch, signal });
      setCenters(payload.work_centers ?? []);
    } catch (err: unknown) {
      if (signal?.aborted) return;
      if (httpErrorStatus(err) === 404) {
        setNoPublication(true);
        setCenters([]);
        setCentersError(null);
        return;
      }
      setCenters([]);
      setCentersError(err instanceof Error ? err.message : texts.loadCentersError);
    } finally {
      if (!signal?.aborted) setLoadingCenters(false);
    }
  }, [branch, texts.loadCentersError]);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setSelected(initial?.workCenters ?? []);
    setHoursRaw(
      initial?.hoursPerWorkCenter != null
        ? String(initial.hoursPerWorkCenter)
        : String(readPreferredLineFeederHours(branch)),
    );
    void loadCenters(controller.signal);
    return () => controller.abort();
  }, [open, branch, initial, loadCenters]);

  const handleHoursChange = useCallback((raw: string) => {
    setHoursRaw(raw);
    const value = parseHours(raw);
    if (value !== null && value <= MAX_HOURS) {
      savePreferredLineFeederHours(branch, value);
    }
  }, [branch]);

  const options = useMemo(
    () =>
      [...centers]
        .sort((a, b) =>
          a.work_center.localeCompare(b.work_center, "pt-BR", {
            numeric: true,
            sensitivity: "base",
          }),
        )
        .map((center) => ({
          value: center.work_center,
          label: center.work_center_name
            ? `${center.work_center} · ${center.work_center_name}`
            : center.work_center,
        })),
    [centers],
  );

  const hours = parseHours(hoursRaw);
  const hoursError =
    hoursRaw.trim() === ""
      ? texts.hoursInvalid
      : hours === null
        ? texts.hoursInvalid
        : hours > MAX_HOURS
          ? texts.hoursMax(MAX_HOURS)
          : null;

  const canSubmit =
    selected.length > 0 && hours !== null && hoursError === null && !submitting;

  return (
    <HostContainedWideDialog
      open={open}
      title={texts.title}
      onClose={submitting ? () => undefined : onClose}
    >
      <div className="ppc-feeder-collect">
        <p className="ppc-feeder-collect__intro" title={helpTooltips.lineFeederCollect}>
          {texts.description}
        </p>

        {loadingCenters ? (
          <p className="ppc-feeder-collect__hint" role="status">
            {texts.loadingCenters}
          </p>
        ) : null}

        {noPublication ? (
          <div className="ppc-state" role="status">
            {texts.noPublication}
          </div>
        ) : null}

        {centersError ? (
          <div className="ppc-state ppc-state--error" role="alert">
            {centersError}
          </div>
        ) : null}

        {!loadingCenters && !noPublication && !centersError && centers.length === 0 ? (
          <div className="ppc-state" role="status">
            {texts.emptyCenters}
          </div>
        ) : null}

        <div className="ppc-feeder-collect__field">
          <LineFeederWorkCenterMultiSelect
            label={texts.workCentersLabel}
            options={options}
            selectedValues={selected}
            onChange={setSelected}
            disabled={loadingCenters || noPublication || submitting}
            showBulkActions
            searchable
          />
        </div>

        <div className="ppc-feeder-collect__hours">
          <label className="ppc-field" htmlFor="ppc-feeder-hours">
            <span className="ppc-field__label">{texts.hoursLabel}</span>
            <input
              id="ppc-feeder-hours"
              type="number"
              inputMode="decimal"
              min={0.1}
              max={MAX_HOURS}
              step={0.5}
              value={hoursRaw}
              aria-label={texts.hoursAria}
              aria-invalid={Boolean(hoursError)}
              disabled={submitting}
              onChange={(event) => handleHoursChange(event.target.value)}
            />
          </label>
          <p className="ppc-feeder-collect__hint">{texts.hoursHint}</p>
          {hoursError ? (
            <p className="ppc-feeder-collect__error" role="alert">
              {hoursError}
            </p>
          ) : null}
          <div className="ppc-feeder-collect__shortcuts" role="group" aria-label={texts.hoursShortcuts}>
            {HOUR_SHORTCUTS.map((value) => (
              <button
                key={value}
                type="button"
                className={
                  hours === value
                    ? "ppc-feeder-collect__chip ppc-feeder-collect__chip--active"
                    : "ppc-feeder-collect__chip"
                }
                disabled={submitting}
                onClick={() => handleHoursChange(String(value))}
              >
                {value}h
              </button>
            ))}
          </div>
        </div>

        <div className="ppc-feeder-collect__actions">
          <button
            type="button"
            className="ppc-icon-btn"
            onClick={onClose}
            disabled={submitting}
          >
            {texts.cancel}
          </button>
          <button
            type="button"
            className="ppc-icon-btn ppc-feeder__collect-cta"
            disabled={!canSubmit}
            onClick={() => {
              if (!canSubmit || hours === null) return;
              onSubmit({
                workCenters: selected,
                hoursPerWorkCenter: hours,
              });
            }}
          >
            {submitting ? texts.submitting : texts.submit}
          </button>
        </div>
      </div>
    </HostContainedWideDialog>
  );
}
