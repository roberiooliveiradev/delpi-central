import { useMemo, type ReactNode } from "react";

import type { PlanAction } from "../../types/actionPlan";
import { DELPI_CONTACT_AREA_OPTIONS } from "../../utils/contactRoles";
import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { PlanSectionEditBindings } from "../../hooks/usePlanSectionEdit";
import { useDragReorder } from "../../hooks/useDragReorder";
import type { Rnc8dContainmentRow, Rnc8dReportPayload, Rnc8dTemplatePayload } from "../../types/rnc8d";
import { emptyRnc8dPayload } from "../../types/rnc8d";
import {
  findTeamMemberBindings,
  formatTeamMemberBindingMessage,
} from "../../utils/teamMemberBindings";
import { buildTeamMemberSelectOptions } from "../../utils/teamMemberOptions";
import {
  Rnc8dClosureRead,
  Rnc8dContainmentRead,
  Rnc8dEffectivenessRead,
  Rnc8dNcDescriptionRead,
  Rnc8dPreventiveRead,
  Rnc8dTeamRead,
} from "../plan-detail/PlanDetailReadViews";
import { SectionSaveButton } from "../ui/SectionSaveButton";
import { EditableSectionCard } from "../ui/EditableSectionCard";
import { TeamMemberRow } from "../TeamMemberRow";
import { TeamMemberSelectField } from "./TeamMemberSelectField";
import { FormActions } from "../ui/FormActions";
import { FieldLabel, HelpTooltip, TableHeaderCell } from "../ui/HelpTooltip";
import { DragHandle, RemoveRowButton } from "../ui/RowActions";
import { SectionCard } from "../ui/SectionCard";
import { TableMemberSelect } from "../ui/TableMemberSelect";
import { TextAreaField } from "../ui/TextAreaField";
import { TextField } from "../ui/TextField";

export type Rnc8dSectionsProps = {
  value: Rnc8dReportPayload;
  onChange: (value: Rnc8dReportPayload) => void;
};

export type Rnc8dSectionSaveProps = {
  saveKey: string;
  saving: string | null;
  onSave?: () => void;
  dirty?: boolean;
  saveLabel?: string;
};

type Rnc8dSectionProps = Rnc8dSectionsProps & Rnc8dSectionSaveProps & {
  sectionEdit: PlanSectionEditBindings;
};

function Rnc8dSectionShell({
  title,
  hint,
  subtitle,
  sectionEdit,
  readContent,
  editContent,
}: {
  title: string;
  hint?: string;
  subtitle?: string;
  sectionEdit: PlanSectionEditBindings;
  readContent: ReactNode;
  editContent: ReactNode;
}) {
  return (
    <EditableSectionCard
      title={title}
      hint={hint}
      subtitle={subtitle}
      isEditing={sectionEdit.isEditing}
      onEdit={sectionEdit.onEdit}
      onCancelEdit={sectionEdit.onCancelEdit}
      readContent={readContent}
      editContent={editContent}
    />
  );
}

function Rnc8dSectionFooter({
  saveKey,
  saving,
  onSave,
  dirty = false,
  saveLabel,
}: Rnc8dSectionSaveProps) {
  if (!onSave) {
    return null;
  }

  return (
    <FormActions align="end">
      <SectionSaveButton
        saveKey={saveKey}
        saving={saving}
        onSave={onSave}
        dirty={dirty}
        label={saveLabel}
      />
    </FormActions>
  );
}

function Rnc8dSectionToolbar({
  addLabel,
  onAdd,
  saveKey,
  saving,
  onSave,
  dirty = false,
  saveLabel,
}: {
  addLabel: string;
  onAdd: () => void;
} & Rnc8dSectionSaveProps) {
  return (
    <div className="pac-section-toolbar">
      <button type="button" className="pac-ghost-btn" onClick={onAdd}>
        {addLabel}
      </button>
      {onSave ? (
        <SectionSaveButton
          saveKey={saveKey}
          saving={saving}
          onSave={onSave}
          dirty={dirty}
          label={saveLabel}
          inline
        />
      ) : null}
    </div>
  );
}

const CONTAINMENT_AREAS = [
  { value: "end_customer", label: "Cliente final" },
  { value: "client_plant", label: "Cliente (planta)" },
  { value: "supplier", label: "Fornecedor" },
] as const;

function updatePayload(
  current: Rnc8dReportPayload,
  patch: Partial<Rnc8dTemplatePayload>,
): Rnc8dReportPayload {
  return {
    ...current,
    template_payload: {
      ...(current.template_payload ?? emptyRnc8dPayload()),
      ...patch,
    },
  };
}

export function Rnc8dHeaderFields({ value, onChange }: Rnc8dSectionsProps) {
  const payload = value.template_payload ?? emptyRnc8dPayload();

  return (
    <div className="pac-form-grid">
      <h4 className="pac-form-grid__subtitle pac-form-grid__subtitle--full">Contato no cliente</h4>
      <TextField
        id="rnc-customer-contact"
        label="Contato no cliente"
        hint={PAC_HELP_TOOLTIPS.rnc8d.contact}
        value={value.customer_contact ?? ""}
        onChange={(customer_contact) => onChange({ ...value, customer_contact })}
      />
      <TextField
        id="rnc-customer-email"
        label="E-mail do cliente"
        hint={PAC_HELP_TOOLTIPS.rnc8d.customerEmail}
        value={value.customer_contact_email ?? ""}
        onChange={(customer_contact_email) => onChange({ ...value, customer_contact_email })}
      />
      <TextField
        id="rnc-customer-phone"
        label="Telefone do cliente"
        hint={PAC_HELP_TOOLTIPS.rnc8d.customerPhone}
        value={value.customer_contact_phone ?? ""}
        onChange={(customer_contact_phone) => onChange({ ...value, customer_contact_phone })}
      />

      <h4 className="pac-form-grid__subtitle pac-form-grid__subtitle--full">Interlocutores DELPI</h4>
      <TextField
        id="rnc-delpi-contact"
        label="Contato DELPI"
        hint={PAC_HELP_TOOLTIPS.rnc8d.delpiContact}
        value={value.delpi_contact_name ?? ""}
        onChange={(delpi_contact_name) => onChange({ ...value, delpi_contact_name })}
      />
      <label className="pac-field">
        <span className="pac-field__label">
          Área DELPI
          <HelpTooltip text={PAC_HELP_TOOLTIPS.rnc8d.delpiContactArea} />
        </span>
        <select
          className="pac-field__input"
          value={value.delpi_contact_area ?? ""}
          onChange={(event) =>
            onChange({ ...value, delpi_contact_area: event.target.value || undefined })
          }
        >
          <option value="">Selecione…</option>
          {DELPI_CONTACT_AREA_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <TextField
        id="rnc-delpi-sales-rep"
        label="Vendedor DELPI"
        hint={PAC_HELP_TOOLTIPS.rnc8d.delpiSalesRep}
        value={value.delpi_sales_rep ?? ""}
        onChange={(delpi_sales_rep) => onChange({ ...value, delpi_sales_rep })}
      />
      <TextField
        id="rnc-delpi-quality-contact"
        label="Qualidade DELPI"
        hint={PAC_HELP_TOOLTIPS.rnc8d.delpiQualityContact}
        value={value.delpi_quality_contact ?? ""}
        onChange={(delpi_quality_contact) => onChange({ ...value, delpi_quality_contact })}
      />
      <TextField
        id="rnc-phone"
        label="Telefone DELPI"
        hint={PAC_HELP_TOOLTIPS.rnc8d.phone}
        value={payload.contact_phone ?? ""}
        onChange={(contact_phone) => onChange(updatePayload(value, { contact_phone }))}
      />
      <TextField
        id="rnc-purchase-order"
        label="Ordem compra / posição"
        hint={PAC_HELP_TOOLTIPS.rnc8d.purchaseOrder}
        value={payload.purchase_order ?? ""}
        onChange={(purchase_order) => onChange(updatePayload(value, { purchase_order }))}
      />
      <TextField
        id="rnc-invoice"
        label="Nota fiscal"
        hint={PAC_HELP_TOOLTIPS.rnc8d.invoice}
        value={payload.invoice_number ?? ""}
        onChange={(invoice_number) => onChange(updatePayload(value, { invoice_number }))}
      />
      <TextField
        id="rnc-invoice-date"
        label="Data digitação NF"
        hint={PAC_HELP_TOOLTIPS.rnc8d.invoiceDate}
        type="date"
        value={payload.invoice_date ?? ""}
        onChange={(invoice_date) => onChange(updatePayload(value, { invoice_date }))}
      />
      <TextField
        id="rnc-defective-qty"
        label="Quantidade defeituosa"
        hint={PAC_HELP_TOOLTIPS.rnc8d.defectiveQty}
        value={payload.defective_quantity ?? ""}
        onChange={(defective_quantity) => onChange(updatePayload(value, { defective_quantity }))}
      />
      <TextField
        id="rnc-client-batch"
        label="Lote do cliente"
        hint={PAC_HELP_TOOLTIPS.rnc8d.clientBatch}
        value={payload.client_batch ?? ""}
        onChange={(client_batch) => onChange(updatePayload(value, { client_batch }))}
      />
      <TextField
        id="rnc-batch-qty"
        label="Quantidade lote"
        hint={PAC_HELP_TOOLTIPS.rnc8d.batchQty}
        value={payload.batch_quantity ?? ""}
        onChange={(batch_quantity) => onChange(updatePayload(value, { batch_quantity }))}
      />
      <TextField
        id="rnc-disposition"
        label="Disposição"
        hint={PAC_HELP_TOOLTIPS.rnc8d.disposition}
        value={payload.disposition ?? ""}
        onChange={(disposition) => onChange(updatePayload(value, { disposition }))}
      />
      <TextField
        id="rnc-rejected-qty"
        label="Quantidade rejeitada"
        hint={PAC_HELP_TOOLTIPS.rnc8d.rejectedQty}
        value={payload.rejected_quantity ?? ""}
        onChange={(rejected_quantity) => onChange(updatePayload(value, { rejected_quantity }))}
      />
      <TextField
        id="rnc-return-by"
        label="Devolver relatório até"
        hint={PAC_HELP_TOOLTIPS.rnc8d.returnBy}
        type="date"
        value={payload.return_by ?? ""}
        onChange={(return_by) => onChange(updatePayload(value, { return_by }))}
      />
    </div>
  );
}

/** @deprecated Preferir `Rnc8dHeaderFields` embutido no painel Problema. */
export function Rnc8dHeaderSection({ value, onChange }: Rnc8dSectionsProps) {
  return (
    <SectionCard
      title="Cabeçalho — material e nota fiscal"
      hint={PAC_HELP_TOOLTIPS.rnc8d.identification}
      subtitle="Complemento da planilha 8D. Cliente, material, lote fornecedor e registro NC ficam no painel Problema."
    >
      <Rnc8dHeaderFields value={value} onChange={onChange} />
    </SectionCard>
  );
}

export function Rnc8dNcDescriptionSection({
  value,
  onChange,
  sectionEdit,
  saveKey,
  saving,
  onSave,
  dirty,
  saveLabel = "Salvar descrição NC",
}: Rnc8dSectionProps) {
  const payload = value.template_payload ?? emptyRnc8dPayload();
  const nc = payload.nc_description ?? {};

  return (
    <Rnc8dSectionShell
      title="1. Descrição da não conformidade"
      hint={PAC_HELP_TOOLTIPS.rnc8d.ncDescription}
      sectionEdit={sectionEdit}
      readContent={<Rnc8dNcDescriptionRead value={value} />}
      editContent={
        <>
          <p className="pac-muted pac-field-hint">
            Na planilha, a coluna <strong>Verificado</strong> é o campo <strong>Relato do problema</strong> no painel
            Problema.
          </p>
          <div className="pac-form-grid">
            <TextField
              id="rnc-nc-char"
              label="Característica"
              hint={PAC_HELP_TOOLTIPS.rnc8d.characteristic}
              value={nc.characteristic ?? ""}
              onChange={(characteristic) =>
                onChange(updatePayload(value, { nc_description: { ...nc, characteristic } }))
              }
              fullWidth
            />
            <TextField
              id="rnc-nc-spec"
              label="Especificado"
              hint={PAC_HELP_TOOLTIPS.rnc8d.specified}
              value={nc.specified ?? ""}
              onChange={(specified) =>
                onChange(updatePayload(value, { nc_description: { ...nc, specified } }))
              }
              fullWidth
            />
            <TextAreaField
              id="rnc-nc-obs"
              label="Observações"
              hint={PAC_HELP_TOOLTIPS.rnc8d.observations}
              value={nc.observations ?? payload.observations ?? ""}
              onChange={(observations) =>
                onChange(
                  updatePayload(value, {
                    nc_description: { ...nc, observations },
                    observations,
                  }),
                )
              }
              rows={2}
              fullWidth
            />
          </div>
          <Rnc8dSectionFooter
            saveKey={saveKey}
            saving={saving}
            onSave={onSave}
            dirty={dirty}
            saveLabel={saveLabel}
          />
        </>
      }
    />
  );
}

export function Rnc8dTeamSection({
  value,
  onChange,
  sectionEdit,
  saveKey,
  saving,
  onSave,
  dirty,
  saveLabel = "Salvar equipe",
  planActions,
  onBindingConflict,
}: Rnc8dSectionProps & {
  planActions?: PlanAction[];
  onBindingConflict?: (message: string) => void;
}) {
  const team = value.team_members ?? [];
  const teamDrag = useDragReorder(team, (team_members) => onChange({ ...value, team_members }));
  const linkedUserIds = team
    .map((item) => item.member_user_id)
    .filter((id): id is string => Boolean(id));

  return (
    <Rnc8dSectionShell
      title="2. Membros da equipe de análise"
      hint={PAC_HELP_TOOLTIPS.rnc8d.team}
      sectionEdit={sectionEdit}
      readContent={<Rnc8dTeamRead members={value.team_members} />}
      editContent={
        <>
          <div className="pac-team-list">
            {team.map((member, index) => (
              <TeamMemberRow
                key={`team-${index}`}
                index={index}
                member={member}
                excludedUserIds={linkedUserIds}
                rowClassName={teamDrag.rowClassName("pac-team-card", index)}
                rowDropProps={teamDrag.rowDropProps(index)}
                canDrag={teamDrag.canDrag}
                dragProps={teamDrag.canDrag ? teamDrag.handleDragProps(index) : null}
                removeDisabled={team.length <= 1}
                onChange={(nextMember) => {
                  const next = [...team];
                  next[index] = nextMember;
                  onChange({ ...value, team_members: next });
                }}
                onLeaderToggle={(checked) => {
                  const next = team.map((item, itemIndex) => ({
                    ...item,
                    is_leader: itemIndex === index ? checked : false,
                  }));
                  onChange({ ...value, team_members: next });
                }}
                onRemove={() => {
                  const member = team[index];
                  const bindings = findTeamMemberBindings(member, {
                    rnc8dForm: value,
                    actions: planActions,
                  });
                  if (bindings.length) {
                    onBindingConflict?.(
                      formatTeamMemberBindingMessage(member.member_name, bindings),
                    );
                    return;
                  }
                  onChange({
                    ...value,
                    team_members: team.filter((_, itemIndex) => itemIndex !== index),
                  });
                }}
              />
            ))}
          </div>
          <Rnc8dSectionToolbar
            addLabel="Adicionar membro"
            onAdd={() =>
              onChange({
                ...value,
                team_members: [...team, { member_name: "", department: "", is_leader: false }],
              })
            }
            saveKey={saveKey}
            saving={saving}
            onSave={onSave}
            dirty={dirty}
            saveLabel={saveLabel}
          />
        </>
      }
    />
  );
}

export function Rnc8dContainmentSection({
  value,
  onChange,
  sectionEdit,
  saveKey,
  saving,
  onSave,
  dirty,
  saveLabel = "Salvar contenção",
}: Rnc8dSectionProps) {
  const payload = value.template_payload ?? emptyRnc8dPayload();
  const containment = payload.containment ?? emptyRnc8dPayload().containment ?? [];
  const teamOptions = useMemo(
    () =>
      buildTeamMemberSelectOptions(
        value.team_members,
        containment.map((row) => row.responsible),
      ),
    [value.team_members, containment],
  );
  const containmentDrag = useDragReorder(containment, (next) =>
    onChange(updatePayload(value, { containment: next })),
  );

  function updateContainmentRow(index: number, patch: Partial<Rnc8dContainmentRow>) {
    const next = containment.map((row, rowIndex) =>
      rowIndex === index ? { ...row, ...patch } : row,
    );
    onChange(updatePayload(value, { containment: next }));
  }

  function removeContainmentRow(index: number) {
    if (containment.length <= 1) return;
    onChange(updatePayload(value, { containment: containment.filter((_, i) => i !== index) }));
  }

  return (
    <Rnc8dSectionShell
      title="3. Ação de contenção"
      hint={PAC_HELP_TOOLTIPS.rnc8d.containment}
      sectionEdit={sectionEdit}
      readContent={<Rnc8dContainmentRead value={value} />}
      editContent={
        <>
      <div className="pac-table-wrap">
        <table className="pac-table pac-table--containment">
          <thead>
            <tr>
              <th className="pac-table__drag-col" scope="col">
                <HelpTooltip
                  content={PAC_HELP_TOOLTIPS.tables.reorder}
                  ariaLabel="Ajuda: Ordenar"
                />
              </th>
              <th>
                <FieldLabel label="Área" hint={PAC_HELP_TOOLTIPS.rnc8d.containmentArea} />
              </th>
              <th>
                <FieldLabel label="Quantidade" hint={PAC_HELP_TOOLTIPS.rnc8d.containmentQty} />
              </th>
              <th>
                <FieldLabel label="Plano de ação" hint={PAC_HELP_TOOLTIPS.rnc8d.containmentActionPlan} />
              </th>
              <th>
                <FieldLabel label="Responsável" hint={PAC_HELP_TOOLTIPS.rnc8d.containmentResponsible} />
              </th>
              <th>
                <FieldLabel label="Data" hint={PAC_HELP_TOOLTIPS.rnc8d.containmentDate} />
              </th>
              <TableHeaderCell
                label="Ações"
                hint={PAC_HELP_TOOLTIPS.tables.rowActions}
                className="pac-table__actions-col"
              />
            </tr>
          </thead>
          <tbody>
            {containment.map((row, index) => (
              <tr
                key={`containment-${index}-${row.area}`}
                className={containmentDrag.rowClassName("", index)}
                {...containmentDrag.rowDropProps(index)}
              >
                <td className="pac-table__drag-col">
                  {containmentDrag.canDrag ? (
                    <DragHandle dragProps={containmentDrag.handleDragProps(index)} />
                  ) : null}
                </td>
                <td>
                  <select
                    className="pac-field__control"
                    value={row.area}
                    aria-label="Área da contenção"
                    onChange={(event) =>
                      updateContainmentRow(index, {
                        area: event.target.value as Rnc8dContainmentRow["area"],
                      })
                    }
                  >
                    {CONTAINMENT_AREAS.map((area) => (
                      <option key={area.value} value={area.value}>
                        {area.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    className="pac-field__control"
                    value={row.quantity ?? ""}
                    aria-label="Quantidade"
                    onChange={(event) =>
                      updateContainmentRow(index, { quantity: event.target.value })
                    }
                  />
                </td>
                <td>
                  <input
                    className="pac-field__control"
                    value={row.action_plan ?? ""}
                    aria-label="Plano de ação"
                    onChange={(event) =>
                      updateContainmentRow(index, { action_plan: event.target.value })
                    }
                  />
                </td>
                <td>
                  <TableMemberSelect
                    value={row.responsible ?? ""}
                    options={teamOptions}
                    ariaLabel="Responsável"
                    onChange={(responsible) => updateContainmentRow(index, { responsible })}
                  />
                </td>
                <td>
                  <input
                    className="pac-field__control"
                    type="date"
                    value={row.date ?? ""}
                    aria-label="Data"
                    onChange={(event) => updateContainmentRow(index, { date: event.target.value })}
                  />
                </td>
                <td className="pac-table__actions-cell">
                  <div className="pac-table-actions">
                  <RemoveRowButton
                    onRemove={() => removeContainmentRow(index)}
                    removeDisabled={containment.length <= 1}
                    removeTitle={
                      containment.length <= 1 ? "Mantenha ao menos uma linha" : "Remover linha"
                    }
                    removeAriaLabel="Remover linha de contenção"
                  />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Rnc8dSectionToolbar
        addLabel="Adicionar linha de contenção"
        onAdd={() =>
          onChange(
            updatePayload(value, {
              containment: [...containment, { area: "end_customer" }],
            }),
          )
        }
        saveKey={saveKey}
        saving={saving}
        onSave={onSave}
        dirty={dirty}
        saveLabel={saveLabel}
      />
        </>
      }
    />
  );
}

export function Rnc8dEffectivenessSection({
  value,
  onChange,
  sectionEdit,
  saveKey,
  saving,
  onSave,
  dirty,
  saveLabel = "Salvar eficácia (8D)",
}: Rnc8dSectionProps) {
  const payload = value.template_payload ?? emptyRnc8dPayload();
  const effectiveness = payload.effectiveness ?? {};

  return (
    <Rnc8dSectionShell
      title="6. Verificação da eficácia da ação corretiva"
      hint={PAC_HELP_TOOLTIPS.rnc8d.effectivenessSection}
      sectionEdit={sectionEdit}
      readContent={<Rnc8dEffectivenessRead value={value} />}
      editContent={
        <>
      <TextAreaField
        id="rnc-effectiveness-resolved"
        label="O problema foi resolvido? Como?"
        hint={PAC_HELP_TOOLTIPS.rnc8d.resolvedHow}
        value={effectiveness.resolved_how ?? ""}
        onChange={(resolved_how) =>
          onChange(updatePayload(value, { effectiveness: { ...effectiveness, resolved_how } }))
        }
        rows={3}
        fullWidth
      />
      <div className="pac-form-grid">
        <TextField
          id="rnc-ok-material-date"
          label="Data material OK (ponto de corte)"
          hint={PAC_HELP_TOOLTIPS.rnc8d.okMaterialDate}
          type="date"
          value={effectiveness.ok_material_date ?? ""}
          onChange={(ok_material_date) =>
            onChange(updatePayload(value, { effectiveness: { ...effectiveness, ok_material_date } }))
          }
        />
        <TextField
          id="rnc-new-parts-id"
          label="Como as peças novas serão identificadas?"
          hint={PAC_HELP_TOOLTIPS.rnc8d.newPartsId}
          value={effectiveness.new_parts_identification ?? ""}
          onChange={(new_parts_identification) =>
            onChange(
              updatePayload(value, {
                effectiveness: { ...effectiveness, new_parts_identification },
              }),
            )
          }
          fullWidth
        />
        <TeamMemberSelectField
          id="rnc-verification-responsible"
          label="Responsável pela verificação"
          hint={PAC_HELP_TOOLTIPS.rnc8d.verificationResponsible}
          value={effectiveness.verification_responsible ?? ""}
          teamMembers={value.team_members}
          extraValues={[effectiveness.verification_responsible]}
          onChange={(verification_responsible) =>
            onChange(
              updatePayload(value, { effectiveness: { ...effectiveness, verification_responsible } }),
            )
          }
        />
        <TextField
          id="rnc-verification-date"
          label="Data de verificação"
          hint={PAC_HELP_TOOLTIPS.rnc8d.verificationDate}
          type="date"
          value={effectiveness.verification_date ?? ""}
          onChange={(verification_date) =>
            onChange(updatePayload(value, { effectiveness: { ...effectiveness, verification_date } }))
          }
        />
      </div>
      <Rnc8dSectionFooter
        saveKey={saveKey}
        saving={saving}
        onSave={onSave}
        dirty={dirty}
        saveLabel={saveLabel}
      />
        </>
      }
    />
  );
}

export function Rnc8dPreventiveSection({
  value,
  onChange,
  sectionEdit,
  saveKey,
  saving,
  onSave,
  dirty,
  saveLabel = "Salvar preventiva",
}: Rnc8dSectionProps) {
  const payload = value.template_payload ?? emptyRnc8dPayload();
  const preventive = payload.preventive ?? {};
  const documentation = payload.documentation_updates?.length
    ? payload.documentation_updates
    : [{}];
  const teamOptions = useMemo(
    () =>
      buildTeamMemberSelectOptions(
        value.team_members,
        [
          preventive.evaluation_responsible,
          ...documentation.map((doc) => doc.responsible),
        ],
      ),
    [value.team_members, preventive.evaluation_responsible, documentation],
  );
  const documentationDrag = useDragReorder(documentation, (next) =>
    onChange(updatePayload(value, { documentation_updates: next })),
  );

  function removeDocumentationRow(index: number) {
    if (documentation.length <= 1) return;
    onChange(
      updatePayload(value, {
        documentation_updates: documentation.filter((_, i) => i !== index),
      }),
    );
  }

  return (
    <Rnc8dSectionShell
      title="7. Ação preventiva e evidência das ações"
      hint={PAC_HELP_TOOLTIPS.rnc8d.preventiveSection}
      sectionEdit={sectionEdit}
      readContent={<Rnc8dPreventiveRead value={value} />}
      editContent={
        <>
      <TextAreaField
        id="rnc-preventive-how"
        label="Como evitar no futuro?"
        hint={PAC_HELP_TOOLTIPS.rnc8d.howAvoidFuture}
        value={preventive.how_avoid_future ?? ""}
        onChange={(how_avoid_future) =>
          onChange(updatePayload(value, { preventive: { ...preventive, how_avoid_future } }))
        }
        rows={3}
        fullWidth
      />
      <TextAreaField
        id="rnc-preventive-scope"
        label="Outros processos/produtos afetados?"
        hint={PAC_HELP_TOOLTIPS.rnc8d.otherProcesses}
        value={preventive.other_processes_products ?? ""}
        onChange={(other_processes_products) =>
          onChange(
            updatePayload(value, { preventive: { ...preventive, other_processes_products } }),
          )
        }
        rows={2}
        fullWidth
      />
      <div className="pac-form-grid">
        <TeamMemberSelectField
          id="rnc-eval-responsible"
          label="Responsável pela avaliação"
          hint={PAC_HELP_TOOLTIPS.rnc8d.evalResponsible}
          value={preventive.evaluation_responsible ?? ""}
          teamMembers={value.team_members}
          extraValues={[preventive.evaluation_responsible]}
          onChange={(evaluation_responsible) =>
            onChange(
              updatePayload(value, { preventive: { ...preventive, evaluation_responsible } }),
            )
          }
        />
        <TextField
          id="rnc-eval-date"
          label="Data conclusão da avaliação"
          hint={PAC_HELP_TOOLTIPS.rnc8d.evalDate}
          type="date"
          value={preventive.evaluation_completion_date ?? ""}
          onChange={(evaluation_completion_date) =>
            onChange(
              updatePayload(value, {
                preventive: { ...preventive, evaluation_completion_date },
              }),
            )
          }
        />
      </div>
      <p className="pac-muted pac-rnc8d-doc-hint">
        <FieldLabel label="Atualização de documentos" hint={PAC_HELP_TOOLTIPS.rnc8d.documentation} />
      </p>
      <div className="pac-table-wrap">
        <table className="pac-table pac-table--documentation">
          <thead>
            <tr>
              <th className="pac-table__drag-col" scope="col">
                <HelpTooltip
                  content={PAC_HELP_TOOLTIPS.tables.reorder}
                  ariaLabel="Ajuda: Ordenar"
                />
              </th>
              <th>
                <FieldLabel label="Documento afetado" hint={PAC_HELP_TOOLTIPS.rnc8d.docAffected} />
              </th>
              <th>
                <FieldLabel label="Responsável" hint={PAC_HELP_TOOLTIPS.rnc8d.docResponsible} />
              </th>
              <th>
                <FieldLabel label="Data" hint={PAC_HELP_TOOLTIPS.rnc8d.docDate} />
              </th>
              <TableHeaderCell
                label="Ações"
                hint={PAC_HELP_TOOLTIPS.tables.rowActions}
                className="pac-table__actions-col"
              />
            </tr>
          </thead>
          <tbody>
            {documentation.map((doc, index) => (
              <tr
                key={`doc-${index}`}
                className={documentationDrag.rowClassName("", index)}
                {...documentationDrag.rowDropProps(index)}
              >
                <td className="pac-table__drag-col">
                  {documentationDrag.canDrag ? (
                    <DragHandle dragProps={documentationDrag.handleDragProps(index)} />
                  ) : null}
                </td>
                <td>
                  <input
                    className="pac-field__control"
                    value={doc.document ?? ""}
                    aria-label="Documento afetado"
                    onChange={(event) => {
                      const next = [...documentation];
                      next[index] = { ...doc, document: event.target.value };
                      onChange(updatePayload(value, { documentation_updates: next }));
                    }}
                  />
                </td>
                <td>
                  <TableMemberSelect
                    value={doc.responsible ?? ""}
                    options={teamOptions}
                    ariaLabel="Responsável pelo documento"
                    onChange={(responsible) => {
                      const next = [...documentation];
                      next[index] = { ...doc, responsible };
                      onChange(updatePayload(value, { documentation_updates: next }));
                    }}
                  />
                </td>
                <td>
                  <input
                    className="pac-field__control"
                    type="date"
                    value={doc.date ?? ""}
                    aria-label="Data do documento"
                    onChange={(event) => {
                      const next = [...documentation];
                      next[index] = { ...doc, date: event.target.value };
                      onChange(updatePayload(value, { documentation_updates: next }));
                    }}
                  />
                </td>
                <td className="pac-table__actions-cell">
                  <div className="pac-table-actions">
                  <RemoveRowButton
                    onRemove={() => removeDocumentationRow(index)}
                    removeDisabled={documentation.length <= 1}
                    removeTitle={
                      documentation.length <= 1 ? "Mantenha ao menos uma linha" : "Remover linha"
                    }
                    removeAriaLabel="Remover linha de documento"
                  />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Rnc8dSectionToolbar
        addLabel="Adicionar documento"
        onAdd={() =>
          onChange(updatePayload(value, { documentation_updates: [...documentation, {}] }))
        }
        saveKey={saveKey}
        saving={saving}
        onSave={onSave}
        dirty={dirty}
        saveLabel={saveLabel}
      />
        </>
      }
    />
  );
}

export function Rnc8dClosureSection({
  value,
  onChange,
  sectionEdit,
  saveKey,
  saving,
  onSave,
  dirty,
  saveLabel = "Salvar fechamento",
}: Rnc8dSectionProps) {
  const payload = value.template_payload ?? emptyRnc8dPayload();

  return (
    <Rnc8dSectionShell
      title="8. Fechamento do relatório 8D"
      hint={PAC_HELP_TOOLTIPS.rnc8d.clientClosure}
      sectionEdit={sectionEdit}
      readContent={<Rnc8dClosureRead value={value} />}
      editContent={
        <>
      <TextField
        id="rnc-closure"
        label="Fechamento 8D (uso do cliente)"
        hint={PAC_HELP_TOOLTIPS.rnc8d.clientClosure}
        value={payload.client_closure_note ?? ""}
        onChange={(client_closure_note) => onChange(updatePayload(value, { client_closure_note }))}
        fullWidth
      />
      <Rnc8dSectionFooter
        saveKey={saveKey}
        saving={saving}
        onSave={onSave}
        dirty={dirty}
        saveLabel={saveLabel}
      />
        </>
      }
    />
  );
}
