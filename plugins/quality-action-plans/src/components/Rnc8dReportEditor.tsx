import { Save } from "lucide-react";

import {
  RNC8D_SHARED_FIELD_LABELS,
  RNC8D_SHARED_MIRROR_HINT,
  type Rnc8dSharedIdentification,
} from "../constants/rnc8dSharedFields";
import { PAC_HELP_TOOLTIPS } from "../content/helpTooltips";
import { FormActions } from "./ui/FormActions";
import { FieldLabel } from "./ui/HelpTooltip";
import { ReadOnlyField } from "./ui/ReadOnlyField";
import { SectionCard } from "./ui/SectionCard";
import { TextAreaField } from "./ui/TextAreaField";
import { TextField } from "./ui/TextField";
import type { Rnc8dReportPayload, Rnc8dTemplatePayload } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";

type Props = {
  value: Rnc8dReportPayload;
  sharedIdentification: Rnc8dSharedIdentification;
  onChange: (value: Rnc8dReportPayload) => void;
  onSave: () => void | Promise<void>;
  saving?: boolean;
};

const CONTAINMENT_LABELS: Record<string, string> = {
  end_customer: "Cliente final",
  client_plant: "Cliente (planta)",
  supplier: "Fornecedor",
};

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

export function Rnc8dReportEditor({ value, sharedIdentification, onChange, onSave, saving }: Props) {
  const payload = value.template_payload ?? emptyRnc8dPayload();
  const nc = payload.nc_description ?? {};
  const effectiveness = payload.effectiveness ?? {};
  const preventive = payload.preventive ?? {};
  const containment = payload.containment ?? emptyRnc8dPayload().containment ?? [];
  const documentation = payload.documentation_updates ?? [{}, {}, {}, {}];
  const team = value.team_members ?? [];

  function setContainmentRow(
    area: "end_customer" | "client_plant" | "supplier",
    field: string,
    fieldValue: string,
  ) {
    const rows = containment.map((row) =>
      row.area === area ? { ...row, [field]: fieldValue } : row,
    );
    onChange(updatePayload(value, { containment: rows }));
  }

  return (
    <div className="pac-rnc8d">
      <SectionCard
        title="1. Identificação — relatório 8D (materiais adquiridos)"
        hint={PAC_HELP_TOOLTIPS.rnc8d.identification}
        subtitle="Campos espelhados do painel Problema aparecem somente leitura."
      >
        <div className="pac-form-grid">
          <ReadOnlyField
            id="rnc-nc-registry"
            label={RNC8D_SHARED_FIELD_LABELS.clientNcRegistry}
            hint={RNC8D_SHARED_MIRROR_HINT}
            value={sharedIdentification.client_nc_registry}
          />
          <ReadOnlyField
            id="rnc-customer"
            label={RNC8D_SHARED_FIELD_LABELS.customer}
            hint={RNC8D_SHARED_MIRROR_HINT}
            value={sharedIdentification.customer_name}
          />
          <TextField
            id="rnc-contact"
            label="Contato"
            hint={PAC_HELP_TOOLTIPS.rnc8d.contact}
            value={value.customer_contact ?? ""}
            onChange={(customer_contact) => onChange({ ...value, customer_contact })}
          />
          <ReadOnlyField
            id="rnc-product"
            label={RNC8D_SHARED_FIELD_LABELS.productCode}
            hint={RNC8D_SHARED_MIRROR_HINT}
            value={sharedIdentification.product_code}
          />
          <ReadOnlyField
            id="rnc-product-desc"
            label={RNC8D_SHARED_FIELD_LABELS.productDescription}
            hint={RNC8D_SHARED_MIRROR_HINT}
            value={sharedIdentification.product_description}
            fullWidth
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
            id="rnc-phone"
            label="Telefone"
            hint={PAC_HELP_TOOLTIPS.rnc8d.phone}
            value={payload.contact_phone ?? ""}
            onChange={(contact_phone) => onChange(updatePayload(value, { contact_phone }))}
          />
          <TextField
            id="rnc-client-batch"
            label="Lote do cliente"
            hint={PAC_HELP_TOOLTIPS.rnc8d.clientBatch}
            value={payload.client_batch ?? ""}
            onChange={(client_batch) => onChange(updatePayload(value, { client_batch }))}
          />
          <ReadOnlyField
            id="rnc-supplier-batch"
            label={RNC8D_SHARED_FIELD_LABELS.supplierBatch}
            hint={RNC8D_SHARED_MIRROR_HINT}
            value={sharedIdentification.batch_number}
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
        </div>
      </SectionCard>

      <SectionCard title="1. Descrição da não conformidade" hint={PAC_HELP_TOOLTIPS.rnc8d.ncDescription}>
        <div className="pac-form-grid">
          <TextField
            id="rnc-nc-char"
            label="Característica"
            hint={PAC_HELP_TOOLTIPS.rnc8d.characteristic}
            value={nc.characteristic ?? ""}
            onChange={(characteristic) =>
              onChange(
                updatePayload(value, {
                  nc_description: { ...nc, characteristic },
                }),
              )
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
          <ReadOnlyField
            id="rnc-nc-verified"
            label={RNC8D_SHARED_FIELD_LABELS.reportedProblem}
            hint={RNC8D_SHARED_MIRROR_HINT}
            value={sharedIdentification.reported_problem}
            fullWidth
            multiline
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
      </SectionCard>

      <SectionCard title="Prazo e contato do cliente" hint={PAC_HELP_TOOLTIPS.rnc8d.contact}>
        <div className="pac-form-grid">
          <TextField
            id="rnc-return-by"
            label="Devolver até"
            hint={PAC_HELP_TOOLTIPS.rnc8d.returnBy}
            type="date"
            value={payload.return_by ?? ""}
            onChange={(return_by) => onChange(updatePayload(value, { return_by }))}
          />
          <TextField
            id="rnc-attention"
            label="Atenção para"
            hint={PAC_HELP_TOOLTIPS.rnc8d.attentionTo}
            value={payload.attention_to ?? ""}
            onChange={(attention_to) => onChange(updatePayload(value, { attention_to }))}
          />
          <TextField
            id="rnc-email"
            label="E-mail"
            hint={PAC_HELP_TOOLTIPS.rnc8d.attentionEmail}
            value={payload.attention_email ?? ""}
            onChange={(attention_email) => onChange(updatePayload(value, { attention_email }))}
          />
        </div>
      </SectionCard>

      <SectionCard title="2. Equipe de análise" hint={PAC_HELP_TOOLTIPS.rnc8d.team}>
        <div className="pac-team-list">
          {team.map((member, index) => (
            <div key={`${member.member_name}-${index}`} className="pac-form-grid pac-team-row">
              <TextField
                id={`rnc-team-name-${index}`}
                label={member.is_leader ? "Líder" : "Membro"}
                hint={member.is_leader ? PAC_HELP_TOOLTIPS.rnc8d.teamLeader : PAC_HELP_TOOLTIPS.rnc8d.team}
                value={member.member_name}
                onChange={(member_name) => {
                  const next = [...team];
                  next[index] = { ...member, member_name };
                  onChange({ ...value, team_members: next });
                }}
              />
              <TextField
                id={`rnc-team-dept-${index}`}
                label="Área"
                hint={PAC_HELP_TOOLTIPS.detail.department}
                value={member.department ?? ""}
                onChange={(department) => {
                  const next = [...team];
                  next[index] = { ...member, department };
                  onChange({ ...value, team_members: next });
                }}
              />
              <label className="pac-checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(member.is_leader)}
                  onChange={(event) => {
                    const next = team.map((item, itemIndex) => ({
                      ...item,
                      is_leader: itemIndex === index ? event.target.checked : false,
                    }));
                    onChange({ ...value, team_members: next });
                  }}
                />
                <FieldLabel label="Líder da equipe" hint={PAC_HELP_TOOLTIPS.rnc8d.teamLeader} />
              </label>
            </div>
          ))}
        </div>
        <button
          type="button"
          className="pac-ghost-btn"
          onClick={() =>
            onChange({
              ...value,
              team_members: [...team, { member_name: "", department: "", is_leader: false }],
            })
          }
        >
          Adicionar membro
        </button>
      </SectionCard>

      <SectionCard title="3. Ação de contenção" hint={PAC_HELP_TOOLTIPS.rnc8d.containment}>
        <div className="pac-table-wrap">
          <table className="pac-table">
            <thead>
              <tr>
                <th>Área</th>
                <th>Quantidade</th>
                <th>Plano de ação</th>
                <th>Responsável</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {containment.map((row) => (
                <tr key={row.area}>
                  <td>{CONTAINMENT_LABELS[row.area] ?? row.area}</td>
                  <td>
                    <input
                      className="pac-field__control"
                      value={row.quantity ?? ""}
                      onChange={(event) => setContainmentRow(row.area, "quantity", event.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="pac-field__control"
                      value={row.action_plan ?? ""}
                      onChange={(event) =>
                        setContainmentRow(row.area, "action_plan", event.target.value)
                      }
                    />
                  </td>
                  <td>
                    <input
                      className="pac-field__control"
                      value={row.responsible ?? ""}
                      onChange={(event) =>
                        setContainmentRow(row.area, "responsible", event.target.value)
                      }
                    />
                  </td>
                  <td>
                    <input
                      className="pac-field__control"
                      type="date"
                      value={row.date ?? ""}
                      onChange={(event) => setContainmentRow(row.area, "date", event.target.value)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="6. Verificação da eficácia" hint={PAC_HELP_TOOLTIPS.rnc8d.effectivenessSection}>
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
              onChange(
                updatePayload(value, { effectiveness: { ...effectiveness, ok_material_date } }),
              )
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
          <TextField
            id="rnc-verification-responsible"
            label="Responsável pela verificação"
            hint={PAC_HELP_TOOLTIPS.rnc8d.verificationResponsible}
            value={effectiveness.verification_responsible ?? ""}
            onChange={(verification_responsible) =>
              onChange(
                updatePayload(value, {
                  effectiveness: { ...effectiveness, verification_responsible },
                }),
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
              onChange(
                updatePayload(value, { effectiveness: { ...effectiveness, verification_date } }),
              )
            }
          />
        </div>
      </SectionCard>

      <SectionCard title="7. Ação preventiva e documentação" hint={PAC_HELP_TOOLTIPS.rnc8d.preventiveSection}>
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
          <TextField
            id="rnc-eval-responsible"
            label="Responsável pela avaliação"
            hint={PAC_HELP_TOOLTIPS.rnc8d.evalResponsible}
            value={preventive.evaluation_responsible ?? ""}
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
          <table className="pac-table">
            <thead>
              <tr>
                <th>Documento afetado</th>
                <th>Responsável</th>
                <th>Data</th>
              </tr>
            </thead>
            <tbody>
              {documentation.map((doc, index) => (
                <tr key={index}>
                  <td>
                    <input
                      className="pac-field__control"
                      value={doc.document ?? ""}
                      onChange={(event) => {
                        const next = [...documentation];
                        next[index] = { ...doc, document: event.target.value };
                        onChange(updatePayload(value, { documentation_updates: next }));
                      }}
                    />
                  </td>
                  <td>
                    <input
                      className="pac-field__control"
                      value={doc.responsible ?? ""}
                      onChange={(event) => {
                        const next = [...documentation];
                        next[index] = { ...doc, responsible: event.target.value };
                        onChange(updatePayload(value, { documentation_updates: next }));
                      }}
                    />
                  </td>
                  <td>
                    <input
                      className="pac-field__control"
                      type="date"
                      value={doc.date ?? ""}
                      onChange={(event) => {
                        const next = [...documentation];
                        next[index] = { ...doc, date: event.target.value };
                        onChange(updatePayload(value, { documentation_updates: next }));
                      }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <TextField
          id="rnc-closure"
          label="Fechamento 8D (uso do cliente)"
          hint={PAC_HELP_TOOLTIPS.rnc8d.clientClosure}
          value={payload.client_closure_note ?? ""}
          onChange={(client_closure_note) => onChange(updatePayload(value, { client_closure_note }))}
          fullWidth
        />
      </SectionCard>

      <FormActions>
        <button
          type="button"
          className="pac-primary-btn"
          disabled={saving}
          onClick={() => void onSave()}
        >
          <Save size={16} />
          {saving ? "Salvando…" : "Salvar relatório 8D"}
        </button>
      </FormActions>
    </div>
  );
}
