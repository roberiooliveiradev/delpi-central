import { Save } from "lucide-react";

import { FormActions } from "./ui/FormActions";
import { SectionCard } from "./ui/SectionCard";
import { TextAreaField } from "./ui/TextAreaField";
import { TextField } from "./ui/TextField";
import type { Rnc8dReportPayload, Rnc8dTemplatePayload } from "../types/rnc8d";
import { emptyRnc8dPayload } from "../types/rnc8d";

type Props = {
  value: Rnc8dReportPayload;
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

export function Rnc8dReportEditor({ value, onChange, onSave, saving }: Props) {
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
      <SectionCard title="1. Identificação — relatório 8D (materiais adquiridos)">
        <div className="pac-form-grid">
          <TextField
            id="rnc-nc-registry"
            label="Registro NC (cliente)"
            value={value.client_nc_registry ?? ""}
            onChange={(client_nc_registry) => onChange({ ...value, client_nc_registry })}
          />
          <TextField
            id="rnc-customer"
            label="Cliente"
            value={value.customer_name ?? ""}
            onChange={(customer_name) => onChange({ ...value, customer_name })}
          />
          <TextField
            id="rnc-contact"
            label="Contato"
            value={value.customer_contact ?? ""}
            onChange={(customer_contact) => onChange({ ...value, customer_contact })}
          />
          <TextField
            id="rnc-product"
            label="Código material"
            value={value.product_code ?? ""}
            onChange={(product_code) => onChange({ ...value, product_code })}
          />
          <TextField
            id="rnc-product-desc"
            label="Descrição material"
            value={value.product_description ?? ""}
            onChange={(product_description) => onChange({ ...value, product_description })}
            fullWidth
          />
          <TextField
            id="rnc-purchase-order"
            label="Ordem compra / posição"
            value={payload.purchase_order ?? ""}
            onChange={(purchase_order) => onChange(updatePayload(value, { purchase_order }))}
          />
          <TextField
            id="rnc-invoice"
            label="Nota fiscal"
            value={payload.invoice_number ?? ""}
            onChange={(invoice_number) => onChange(updatePayload(value, { invoice_number }))}
          />
          <TextField
            id="rnc-invoice-date"
            label="Data digitação NF"
            type="date"
            value={payload.invoice_date ?? ""}
            onChange={(invoice_date) => onChange(updatePayload(value, { invoice_date }))}
          />
          <TextField
            id="rnc-defective-qty"
            label="Quantidade defeituosa"
            value={payload.defective_quantity ?? ""}
            onChange={(defective_quantity) => onChange(updatePayload(value, { defective_quantity }))}
          />
          <TextField
            id="rnc-phone"
            label="Telefone"
            value={payload.contact_phone ?? ""}
            onChange={(contact_phone) => onChange(updatePayload(value, { contact_phone }))}
          />
          <TextField
            id="rnc-client-batch"
            label="Lote do cliente"
            value={payload.client_batch ?? ""}
            onChange={(client_batch) => onChange(updatePayload(value, { client_batch }))}
          />
          <TextField
            id="rnc-supplier-batch"
            label="Lote fornecedor"
            value={value.batch_number ?? ""}
            onChange={(batch_number) => onChange({ ...value, batch_number })}
          />
          <TextField
            id="rnc-batch-qty"
            label="Quantidade lote"
            value={payload.batch_quantity ?? ""}
            onChange={(batch_quantity) => onChange(updatePayload(value, { batch_quantity }))}
          />
          <TextField
            id="rnc-disposition"
            label="Disposição"
            value={payload.disposition ?? ""}
            onChange={(disposition) => onChange(updatePayload(value, { disposition }))}
          />
          <TextField
            id="rnc-rejected-qty"
            label="Quantidade rejeitada"
            value={payload.rejected_quantity ?? ""}
            onChange={(rejected_quantity) => onChange(updatePayload(value, { rejected_quantity }))}
          />
        </div>
      </SectionCard>

      <SectionCard title="1. Descrição da não conformidade">
        <div className="pac-form-grid">
          <TextField
            id="rnc-nc-char"
            label="Característica"
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
            value={nc.specified ?? ""}
            onChange={(specified) =>
              onChange(updatePayload(value, { nc_description: { ...nc, specified } }))
            }
            fullWidth
          />
          <TextAreaField
            id="rnc-nc-verified"
            label="Verificado"
            value={nc.verified ?? value.reported_problem ?? ""}
            onChange={(verified) => {
              onChange({
                ...updatePayload(value, { nc_description: { ...nc, verified } }),
                reported_problem: verified,
              });
            }}
            rows={4}
            fullWidth
          />
          <TextAreaField
            id="rnc-nc-obs"
            label="Observações"
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

      <SectionCard title="Prazo e contato do cliente">
        <div className="pac-form-grid">
          <TextField
            id="rnc-return-by"
            label="Devolver até"
            type="date"
            value={payload.return_by ?? ""}
            onChange={(return_by) => onChange(updatePayload(value, { return_by }))}
          />
          <TextField
            id="rnc-attention"
            label="Atenção para"
            value={payload.attention_to ?? ""}
            onChange={(attention_to) => onChange(updatePayload(value, { attention_to }))}
          />
          <TextField
            id="rnc-email"
            label="E-mail"
            value={payload.attention_email ?? ""}
            onChange={(attention_email) => onChange(updatePayload(value, { attention_email }))}
          />
        </div>
      </SectionCard>

      <SectionCard title="2. Equipe de análise">
        <div className="pac-team-list">
          {team.map((member, index) => (
            <div key={`${member.member_name}-${index}`} className="pac-form-grid pac-team-row">
              <TextField
                id={`rnc-team-name-${index}`}
                label={member.is_leader ? "Líder" : "Membro"}
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
                <span>Líder da equipe</span>
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

      <SectionCard title="3. Ação de contenção">
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

      <SectionCard title="6. Verificação da eficácia">
        <TextAreaField
          id="rnc-effectiveness-resolved"
          label="O problema foi resolvido? Como?"
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

      <SectionCard title="7. Ação preventiva e documentação">
        <TextAreaField
          id="rnc-preventive-how"
          label="Como evitar no futuro?"
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
