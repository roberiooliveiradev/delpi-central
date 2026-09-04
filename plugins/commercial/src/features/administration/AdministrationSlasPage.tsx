import { Pencil, Plus, Power, RefreshCw, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createSlaPolicy,
  deactivateSlaPolicy,
  listSlaPolicies,
  SLA_APPLIES_TO_VALUES,
  updateSlaPolicy,
  type SlaAppliesTo,
  type SlaPolicyRow,
} from "../../api/slaPoliciesApi";
import {
  CommercialActionButton,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
} from "../../app/commercialUi";
import { useCommercialConfirm } from "../../app/CommercialConfirmDialogProvider";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginView } from "../../app/pluginNavigation";
import { ADMINISTRATION_CONTENT } from "../../content/administration";
import { CM_HELP } from "../../content/helpTooltips";
import { AdministrationSubNav } from "./AdministrationSubNav";

type AdministrationSlasPageProps = {
  basePath: string;
};

type FormState = {
  code: string;
  name: string;
  appliesTo: SlaAppliesTo;
  durationHours: string;
  calendarCode: string;
  active: boolean;
};

const EMPTY_FORM: FormState = {
  code: "",
  name: "",
  appliesTo: "offer_stage",
  durationHours: "24",
  calendarCode: "",
  active: true,
};

function appliesToLabel(value: string): string {
  const copy = ADMINISTRATION_CONTENT.slas;
  switch (value) {
    case "task":
      return copy.appliesToTask;
    case "sample":
      return copy.appliesToSample;
    case "order_confirmation":
      return copy.appliesToOrderConfirmation;
    case "offer_stage":
      return copy.appliesToOfferStage;
    default:
      return value;
  }
}

function rowToForm(row: SlaPolicyRow): FormState {
  const applies = SLA_APPLIES_TO_VALUES.includes(row.appliesTo as SlaAppliesTo)
    ? (row.appliesTo as SlaAppliesTo)
    : "offer_stage";
  return {
    code: row.code,
    name: row.name,
    appliesTo: applies,
    durationHours: String(row.durationHours),
    calendarCode: row.calendarCode ?? "",
    active: row.active,
  };
}

export function AdministrationSlasPage({ basePath }: AdministrationSlasPageProps) {
  const copy = ADMINISTRATION_CONTENT.slas;
  const confirm = useCommercialConfirm();
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const [items, setItems] = useState<SlaPolicyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const page = await listSlaPolicies({ includeInactive: true, signal });
      if (signal?.aborted) return;
      setItems(page.items ?? []);
    } catch (err: unknown) {
      if (signal?.aborted) return;
      setError(err instanceof Error ? err.message : copy.loadError);
      setItems([]);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [copy.loadError]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load, reloadKey]);

  const appliesOptions = useMemo(
    () =>
      SLA_APPLIES_TO_VALUES.map((value) => ({
        value,
        label: appliesToLabel(value),
      })),
    [],
  );

  const openCreate = () => {
    setEditingId(null);
    setForm(EMPTY_FORM);
    setFormOpen(true);
  };

  const openEdit = (row: SlaPolicyRow) => {
    setEditingId(row.id);
    setForm(rowToForm(row));
    setFormOpen(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
  };

  const submitForm = async () => {
    const code = form.code.trim();
    const name = form.name.trim();
    const hours = Number(form.durationHours);
    if (!code) {
      notifyError(copy.codeRequired);
      return;
    }
    if (!name) {
      notifyError(copy.nameRequired);
      return;
    }
    if (!Number.isInteger(hours) || hours <= 0) {
      notifyError(copy.hoursRequired);
      return;
    }
    setSaving(true);
    try {
      const payload = {
        code,
        name,
        appliesTo: form.appliesTo,
        durationHours: hours,
        calendarCode: form.calendarCode.trim() || null,
        active: form.active,
      };
      if (editingId) {
        await updateSlaPolicy(editingId, payload);
        notifySuccess(copy.updateSuccess);
      } else {
        await createSlaPolicy(payload);
        notifySuccess(copy.createSuccess);
      }
      closeForm();
      setReloadKey((value) => value + 1);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : copy.loadError);
    } finally {
      setSaving(false);
    }
  };

  const onDeactivate = async (row: SlaPolicyRow) => {
    if (!row.active) return;
    const ok = await confirm({
      title: copy.deactivateConfirmTitle,
      message: copy.deactivateConfirmMessage.replace("{name}", row.name),
      confirmLabel: copy.deactivate,
    });
    if (!ok) return;
    setBusyId(row.id);
    try {
      await deactivateSlaPolicy(row.id);
      notifySuccess(copy.deactivateSuccess);
      setReloadKey((value) => value + 1);
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : copy.loadError);
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section className="cm-page-stack cm-administration-slas">
      <CommercialPagePath
        aria-label={copy.title}
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[
          {
            id: "admin-root",
            label: ADMINISTRATION_CONTENT.breadcrumbRoot,
            href: `${basePath}/administration`,
            onNavigate: (event) => {
              event.preventDefault();
              navigatePluginView("administration", { basePath });
            },
          },
        ]}
        current={copy.navLabel}
      />
      <AdministrationSubNav basePath={basePath} active="slas" />
      <CommercialPageHero
        aria-label={copy.title}
        title={
          <CommercialSectionHintLabel label={copy.title} hint={CM_HELP.administration.slasPage} />
        }
        description={copy.description}
        actions={
          <div className="cm-page-hero__actions-row">
            <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
              <RefreshCw size={16} aria-hidden="true" /> {copy.refresh}
            </CommercialActionButton>
            <CommercialActionButton onClick={openCreate}>
              <Plus size={16} aria-hidden="true" /> {copy.create}
            </CommercialActionButton>
          </div>
        }
      />

      {formOpen ? (
        <CommercialSectionCard
          title={editingId ? copy.editFormTitle : copy.createFormTitle}
          actions={
            <CommercialActionButton variant="ghost" onClick={closeForm} disabled={saving}>
              <X size={16} aria-hidden="true" /> {copy.closeForm}
            </CommercialActionButton>
          }
        >
          <div className="cm-administration-slas__form">
            <CommercialTextField
              label={copy.fieldCode}
              hint={CM_HELP.administration.slasCode}
              value={form.code}
              onChange={(value) => setForm((prev) => ({ ...prev, code: value }))}
              disabled={saving}
            />
            <CommercialTextField
              label={copy.fieldName}
              hint={CM_HELP.administration.slasName}
              value={form.name}
              onChange={(value) => setForm((prev) => ({ ...prev, name: value }))}
              disabled={saving}
            />
            <CommercialSelectField
              label={copy.fieldAppliesTo}
              hint={CM_HELP.administration.slasAppliesTo}
              value={form.appliesTo}
              onChange={(value) => {
                if (SLA_APPLIES_TO_VALUES.includes(value as SlaAppliesTo)) {
                  setForm((prev) => ({ ...prev, appliesTo: value as SlaAppliesTo }));
                }
              }}
              options={appliesOptions}
              disabled={saving}
            />
            <CommercialTextField
              label={copy.fieldDurationHours}
              hint={CM_HELP.administration.slasDurationHours}
              value={form.durationHours}
              onChange={(value) => setForm((prev) => ({ ...prev, durationHours: value }))}
              disabled={saving}
            />
            <CommercialTextField
              label={copy.fieldCalendarCode}
              hint={CM_HELP.administration.slasCalendarCode}
              value={form.calendarCode}
              onChange={(value) => setForm((prev) => ({ ...prev, calendarCode: value }))}
              disabled={saving}
            />
            <CommercialSelectField
              label={copy.fieldActive}
              hint={CM_HELP.administration.slasActive}
              value={form.active ? "yes" : "no"}
              onChange={(value) =>
                setForm((prev) => ({ ...prev, active: value === "yes" }))
              }
              options={[
                { value: "yes", label: copy.activeYes },
                { value: "no", label: copy.activeNo },
              ]}
              disabled={saving}
            />
            <CommercialActionButton onClick={() => void submitForm()} disabled={saving}>
              {saving ? copy.saving : editingId ? copy.saveEdit : copy.saveCreate}
            </CommercialActionButton>
          </div>
        </CommercialSectionCard>
      ) : null}

      <CommercialSectionCard title={copy.title} hint={CM_HELP.administration.slasPage}>
        {loading ? <CommercialLoadingCard title={copy.loading} variant="panel" /> : null}
        {error ? <CommercialStateBanner variant="error">{error}</CommercialStateBanner> : null}
        {!loading && !error && items.length === 0 ? (
          <CommercialEmptyState
            defaultTitle={copy.emptyTitle}
            defaultMessage={copy.emptyDescription}
          />
        ) : null}
        {!loading && !error && items.length > 0 ? (
          <CommercialDataTable
            rows={items}
            rowKey={(row) => row.id}
            layout="section"
            columns={[
              { key: "code", header: copy.colCode, render: (row) => row.code },
              { key: "name", header: copy.colName, render: (row) => row.name },
              {
                key: "appliesTo",
                header: copy.colAppliesTo,
                render: (row) => appliesToLabel(row.appliesTo),
              },
              {
                key: "durationHours",
                header: copy.colDuration,
                align: "right",
                render: (row) => String(row.durationHours),
              },
              {
                key: "calendarCode",
                header: copy.colCalendar,
                render: (row) => row.calendarCode || "—",
              },
              {
                key: "active",
                header: copy.colActive,
                render: (row) => (
                  <CommercialStatusBadge
                    label={row.active ? copy.activeYes : copy.activeNo}
                    variant={row.active ? "success" : "neutral"}
                  />
                ),
              },
              {
                key: "actions",
                header: copy.colActions,
                interactive: true,
                rowClick: "stop",
                render: (row) => (
                  <div className="cm-administration-slas__row-actions">
                    <CommercialActionButton
                      variant="ghost"
                      onClick={() => openEdit(row)}
                      disabled={busyId === row.id}
                    >
                      <Pencil size={14} aria-hidden="true" /> {copy.edit}
                    </CommercialActionButton>
                    {row.active ? (
                      <CommercialActionButton
                        variant="ghost"
                        onClick={() => void onDeactivate(row)}
                        disabled={busyId === row.id}
                      >
                        <Power size={14} aria-hidden="true" />{" "}
                        {busyId === row.id ? copy.deactivating : copy.deactivate}
                      </CommercialActionButton>
                    ) : null}
                  </div>
                ),
              },
            ]}
          />
        ) : null}
      </CommercialSectionCard>
    </section>
  );
}
