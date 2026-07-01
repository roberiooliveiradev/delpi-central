import {
  ACTION_STATUSES,
  EFFECTIVENESS_STATUSES,
  PAC_BRANCH_OPTIONS,
  PAC_NONCONFORMITY_SCOPES,
  PAC_SOURCE_TYPES,
  PLAN_SEVERITIES,
  PLAN_STATUSES,
  actionTypeLabel,
  branchLabel,
} from "../../constants/actionPlans";
import { RNC8D_SHARED_FIELD_LABELS } from "../../constants/rnc8dSharedFields";
import { DELPI_CONTACT_AREA_OPTIONS } from "../../utils/contactRoles";
import type { PlanAction } from "../../types/actionPlan";
import type { Rnc8dReportPayload, Rnc8dTemplatePayload, TeamMember } from "../../types/rnc8d";
import { emptyRnc8dPayload } from "../../types/rnc8d";
import type { PlanIdentificationFormState } from "../PlanProblemSection";
import { ScopeBadge, SeverityBadge, StatusBadge } from "../StatusBadge";
import { StatusPipeline } from "../ui/StatusPipeline";
import { ReadOnlyField } from "../ui/ReadOnlyField";
import { ReadOnlyGrid } from "../ui/ReadOnlyGrid";
import type { FiveWhysForm } from "../../utils/fiveWhys";
import { isFilledWhyStep } from "../../utils/fiveWhys";
import type { IshikawaCausesForm } from "../../utils/ishikawaCauses";
import { ISHIKAWA_CATEGORY_KEYS } from "../../utils/ishikawaCauses";
import { ActionResponsiblesChips } from "../ActionResponsiblesChips";
import { formatDate } from "../../utils/format";
import type { PlanStatus } from "../../types/actionPlan";

const CONTAINMENT_AREA_LABELS: Record<string, string> = {
  end_customer: "Cliente final",
  client_plant: "Cliente (planta)",
  supplier: "Fornecedor",
};

const ISHIKAWA_LABELS: Record<string, string> = {
  method_process: "Método",
  machine: "Máquina",
  manpower: "Mão de obra",
  material: "Material",
  measurement: "Medição",
  environment: "Meio ambiente",
};

const CONFIDENCE_LABELS: Record<string, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
};

function optionLabel(
  options: ReadonlyArray<{ value: string; label: string }>,
  value: string,
): string {
  return options.find((item) => item.value === value)?.label ?? (value || "—");
}

function joinList(values: string[] | undefined): string {
  if (!values?.length) return "—";
  const items = values.map((item) => item.trim()).filter(Boolean);
  return items.length ? items.join(", ") : "—";
}

function payloadOf(form: Rnc8dReportPayload): Rnc8dTemplatePayload {
  return form.template_payload ?? emptyRnc8dPayload();
}

type StatusReadProps = {
  planStatus: PlanStatus;
  planBranchCode?: string | null;
  planScope?: string | null;
  planSeverity?: string | null;
};

export function PlanStatusReadContent({
  planStatus,
  planBranchCode,
  planScope,
  planSeverity,
}: StatusReadProps) {
  return (
    <div className="pac-ficha">
      <StatusPipeline
        currentStatus={planStatus}
        hint={PAC_HELP_TOOLTIPS.detail.statusPipeline}
      />
      <section className="pac-ficha-section">
        <h3 className="pac-subsection-title">Resumo</h3>
        <dl className="pac-dl pac-dl--compact pac-dl--read">
          <div>
            <dt>Status</dt>
            <dd>
              <StatusBadge status={planStatus} />
            </dd>
          </div>
          <div>
            <dt>Filial</dt>
            <dd>{branchLabel(planBranchCode)}</dd>
          </div>
          <div>
            <dt>Escopo</dt>
            <dd>
              <ScopeBadge scope={planScope} />
            </dd>
          </div>
          <div>
            <dt>Severidade</dt>
            <dd>
              <SeverityBadge severity={planSeverity ?? "medium"} />
            </dd>
          </div>
        </dl>
      </section>
    </div>
  );
}

type ProblemReadProps = {
  showRnc8dFlow: boolean;
  identification: PlanIdentificationFormState;
  rnc8dForm: Rnc8dReportPayload;
};

export function PlanProblemReadContent({
  showRnc8dFlow,
  identification,
  rnc8dForm,
}: ProblemReadProps) {
  const payload = payloadOf(rnc8dForm);

  return (
    <div className="pac-ficha">
      <h3 className="pac-subsection-title">Identificação geral</h3>
      <ReadOnlyGrid>
        <ReadOnlyField
          label="Título"
          hint={PAC_HELP_TOOLTIPS.detail.title}
          value={identification.title}
          fullWidth
        />
        <ReadOnlyField
          label="Filial"
          hint={PAC_HELP_TOOLTIPS.filters.branch}
          value={optionLabel(PAC_BRANCH_OPTIONS, identification.branch_code)}
        />
        <ReadOnlyField
          label="Escopo NC"
          hint={PAC_HELP_TOOLTIPS.filters.scope}
          value={optionLabel(PAC_NONCONFORMITY_SCOPES, identification.nonconformity_scope)}
        />
        <ReadOnlyField
          label="Severidade"
          hint={PAC_HELP_TOOLTIPS.filters.severity}
          value={optionLabel(PLAN_SEVERITIES, identification.severity)}
        />
      </ReadOnlyGrid>

      <h3 className="pac-subsection-title">Cliente</h3>
      <ReadOnlyGrid>
        <ReadOnlyField
          label="Código do cliente (Delpi)"
          hint={PAC_HELP_TOOLTIPS.detail.customer}
          value={identification.customer_code}
        />
        <ReadOnlyField label="Loja" value={identification.customer_store} />
        <ReadOnlyField
          label="Nome do cliente"
          hint={PAC_HELP_TOOLTIPS.detail.customer}
          value={identification.customer_name}
        />
      </ReadOnlyGrid>

      <h3 className="pac-subsection-title">Material</h3>
      <ReadOnlyGrid>
        <ReadOnlyField
          label={showRnc8dFlow ? RNC8D_SHARED_FIELD_LABELS.productCode : "Código produto"}
          hint={PAC_HELP_TOOLTIPS.detail.productCode}
          value={identification.product_code}
        />
        <ReadOnlyField
          label={
            showRnc8dFlow
              ? RNC8D_SHARED_FIELD_LABELS.customerProductReference
              : "Referência do cliente"
          }
          hint={PAC_HELP_TOOLTIPS.detail.customerProductReference}
          value={identification.customer_product_reference}
        />
        <ReadOnlyField
          label={
            showRnc8dFlow
              ? RNC8D_SHARED_FIELD_LABELS.productDescription
              : "Descrição produto"
          }
          hint={PAC_HELP_TOOLTIPS.detail.productDescription}
          value={identification.product_description}
        />
        <ReadOnlyField
          label={showRnc8dFlow ? RNC8D_SHARED_FIELD_LABELS.supplierBatch : "Lote"}
          hint={PAC_HELP_TOOLTIPS.detail.supplierBatch}
          value={identification.batch_number}
        />
        <ReadOnlyField
          label="Área"
          hint={PAC_HELP_TOOLTIPS.detail.department}
          value={identification.department}
        />
      </ReadOnlyGrid>

      <h3 className="pac-subsection-title">Classificação do problema</h3>
      <ReadOnlyGrid>
        <ReadOnlyField
          label="Modo de falha"
          hint={PAC_HELP_TOOLTIPS.detail.failureMode}
          value={joinList(identification.failure_modes)}
        />
        <ReadOnlyField
          label="Categoria do problema"
          hint={PAC_HELP_TOOLTIPS.detail.problemCategory}
          value={joinList(identification.problem_categories)}
        />
        <ReadOnlyField
          label="Tags de sintoma"
          hint={PAC_HELP_TOOLTIPS.detail.symptomTags}
          value={joinList(identification.symptom_tags)}
        />
      </ReadOnlyGrid>

      <h3 className="pac-subsection-title">Origem e registro</h3>
      <ReadOnlyGrid>
        <ReadOnlyField
          label="Canal (source_type)"
          hint={PAC_HELP_TOOLTIPS.form.source}
          value={
            identification.source_type
              ? optionLabel(PAC_SOURCE_TYPES, identification.source_type)
              : undefined
          }
        />
        <ReadOnlyField
          label="Referência do canal"
          hint={PAC_HELP_TOOLTIPS.detail.sourceReference}
          value={identification.source_reference}
        />
        {showRnc8dFlow ? (
          <ReadOnlyField
            label={RNC8D_SHARED_FIELD_LABELS.clientNcRegistry}
            hint={PAC_HELP_TOOLTIPS.detail.clientNcRegistry}
            value={identification.client_nc_registry}
          />
        ) : null}
      </ReadOnlyGrid>

      {showRnc8dFlow ? (
        <>
          <h3 className="pac-subsection-title">Material e nota fiscal</h3>
          <ReadOnlyGrid>
            <ReadOnlyField
              label="Contato no cliente"
              hint={PAC_HELP_TOOLTIPS.rnc8d.contact}
              value={rnc8dForm.customer_contact}
            />
            <ReadOnlyField
              label="E-mail do cliente"
              hint={PAC_HELP_TOOLTIPS.rnc8d.customerEmail}
              value={rnc8dForm.customer_contact_email}
            />
            <ReadOnlyField
              label="Telefone do cliente"
              hint={PAC_HELP_TOOLTIPS.rnc8d.customerPhone}
              value={rnc8dForm.customer_contact_phone}
            />
            <ReadOnlyField
              label="Contato DELPI"
              hint={PAC_HELP_TOOLTIPS.rnc8d.delpiContact}
              value={rnc8dForm.delpi_contact_name}
            />
            <ReadOnlyField
              label="Área DELPI"
              hint={PAC_HELP_TOOLTIPS.rnc8d.delpiContactArea}
              value={
                DELPI_CONTACT_AREA_OPTIONS.find(
                  (option) => option.value === rnc8dForm.delpi_contact_area,
                )?.label ?? rnc8dForm.delpi_contact_area
              }
            />
            <ReadOnlyField
              label="Vendedor DELPI"
              hint={PAC_HELP_TOOLTIPS.rnc8d.delpiSalesRep}
              value={rnc8dForm.delpi_sales_rep}
            />
            <ReadOnlyField
              label="Qualidade DELPI"
              hint={PAC_HELP_TOOLTIPS.rnc8d.delpiQualityContact}
              value={rnc8dForm.delpi_quality_contact}
            />
            <ReadOnlyField label="Telefone DELPI" hint={PAC_HELP_TOOLTIPS.rnc8d.phone} value={payload.contact_phone} />
            <ReadOnlyField
              label="Ordem compra / posição"
              hint={PAC_HELP_TOOLTIPS.rnc8d.purchaseOrder}
              value={payload.purchase_order}
            />
            <ReadOnlyField label="Nota fiscal" hint={PAC_HELP_TOOLTIPS.rnc8d.invoice} value={payload.invoice_number} />
            <ReadOnlyField
              label="Data digitação NF"
              hint={PAC_HELP_TOOLTIPS.rnc8d.invoiceDate}
              value={payload.invoice_date}
            />
            <ReadOnlyField
              label="Quantidade defeituosa"
              hint={PAC_HELP_TOOLTIPS.rnc8d.defectiveQty}
              value={payload.defective_quantity}
            />
            <ReadOnlyField
              label="Lote do cliente"
              hint={PAC_HELP_TOOLTIPS.rnc8d.clientBatch}
              value={payload.client_batch}
            />
            <ReadOnlyField
              label="Quantidade lote"
              hint={PAC_HELP_TOOLTIPS.rnc8d.batchQty}
              value={payload.batch_quantity}
            />
            <ReadOnlyField
              label="Disposição"
              hint={PAC_HELP_TOOLTIPS.rnc8d.disposition}
              value={payload.disposition}
            />
            <ReadOnlyField
              label="Quantidade rejeitada"
              hint={PAC_HELP_TOOLTIPS.rnc8d.rejectedQty}
              value={payload.rejected_quantity}
            />
            <ReadOnlyField
              label="Devolver relatório até"
              hint={PAC_HELP_TOOLTIPS.rnc8d.returnBy}
              value={payload.return_by}
            />
          </ReadOnlyGrid>
        </>
      ) : null}

      <section className="pac-ficha-section pac-ficha-section--separated">
        <ReadOnlyField
          label={RNC8D_SHARED_FIELD_LABELS.reportedProblem}
          hint={PAC_HELP_TOOLTIPS.form.description}
          value={identification.reported_problem}
          fullWidth
          multiline
        />
      </section>
    </div>
  );
}

export function Rnc8dNcDescriptionRead({ value }: { value: Rnc8dReportPayload }) {
  const payload = payloadOf(value);
  const nc = payload.nc_description ?? {};

  return (
    <div className="pac-ficha">
      <ReadOnlyGrid>
        <ReadOnlyField label="Característica" hint={PAC_HELP_TOOLTIPS.rnc8d.characteristic} value={nc.characteristic} />
        <ReadOnlyField label="Especificado" hint={PAC_HELP_TOOLTIPS.rnc8d.specified} value={nc.specified} />
        <ReadOnlyField
          label="Observações"
          hint={PAC_HELP_TOOLTIPS.rnc8d.observations}
          value={nc.observations ?? payload.observations}
          fullWidth
          multiline
        />
      </ReadOnlyGrid>
    </div>
  );
}

export function Rnc8dTeamRead({ members }: { members: TeamMember[] | undefined }) {
  const team = members ?? [];

  if (!team.some((m) => m.member_name?.trim())) {
    return <p className="pac-muted">Nenhum membro cadastrado.</p>;
  }

  return (
    <ul className="pac-readonly-list pac-readonly-list--team">
      {team.map((member, index) => {
        const name = member.member_name?.trim();
        if (!name) return null;
        return (
          <li key={`member-read-${index}`} className="pac-readonly-list__item">
            <span className="pac-readonly-list__primary">
              {name}
              {member.is_leader ? <span className="pac-team-card__leader-badge">Líder</span> : null}
            </span>
            <span className="pac-readonly-list__meta">
              {member.department?.trim() ? `Área: ${member.department.trim()}` : null}
              {member.member_user_id ? " · Delpi vinculado" : " · Sem vínculo Delpi"}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export function Rnc8dContainmentRead({ value }: { value: Rnc8dReportPayload }) {
  const rows = payloadOf(value).containment ?? [];

  if (!rows.length) {
    return <p className="pac-muted">Nenhuma linha de contenção.</p>;
  }

  return (
    <div className="pac-table-wrap">
      <table className="pac-table pac-table--compact-read">
        <thead>
          <tr>
            <th>Área</th>
            <th>Qtd.</th>
            <th>Plano</th>
            <th>Responsável</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`containment-read-${index}`}>
              <td>{CONTAINMENT_AREA_LABELS[row.area] ?? row.area}</td>
              <td>{row.quantity?.trim() || "—"}</td>
              <td>{row.action_plan?.trim() || "—"}</td>
              <td>{row.responsible?.trim() || "—"}</td>
              <td>{row.date?.trim() || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function FiveWhysReadContent({ form }: { form: FiveWhysForm }) {
  function renderTrack(title: string, steps: FiveWhysForm["occurrence"]) {
    const filled = steps.filter((step) => isFilledWhyStep(step));

    return (
      <section className="pac-ficha-section">
        <h3 className="pac-subsection-title">{title}</h3>
        {!filled.length ? (
          <p className="pac-ficha-text pac-muted">—</p>
        ) : (
          <ol className="pac-ficha-list">
            {filled.map((step, index) => (
              <li key={`${title}-${index}`}>
                {step.question.trim() ? <strong>{step.question.trim()}</strong> : null}
                {step.question.trim() && step.answer.trim() ? " — " : null}
                {step.answer.trim() || (step.question.trim() ? "" : "—")}
              </li>
            ))}
          </ol>
        )}
      </section>
    );
  }

  return (
    <div className="pac-ficha">
      {renderTrack("Ocorrência", form.occurrence)}
      {renderTrack("Detecção", form.detection)}
      <section className="pac-ficha-section">
        <h3 className="pac-subsection-title">Causa raiz e confiança</h3>
        <ReadOnlyGrid>
          <ReadOnlyField label="Causa raiz" value={form.root_cause} multiline fullWidth />
          <ReadOnlyField
            label="Confiança"
            value={CONFIDENCE_LABELS[form.confidence_level] ?? form.confidence_level}
          />
        </ReadOnlyGrid>
      </section>
    </div>
  );
}

export function IshikawaReadContent({
  causes,
  notes,
}: {
  causes: IshikawaCausesForm;
  notes: string;
}) {
  return (
    <div className="pac-ficha">
      <div className="pac-readonly-ishikawa-grid">
        {ISHIKAWA_CATEGORY_KEYS.map((key) => {
          const items = causes[key].map((item) => item.trim()).filter(Boolean);
          return (
            <section key={key} className="pac-ficha-section">
              <h3 className="pac-subsection-title">{ISHIKAWA_LABELS[key] ?? key}</h3>
              {items.length ? (
                <ul className="pac-ficha-list pac-ficha-list--pre-wrap">
                  {items.map((item, index) => (
                    <li key={`${key}-${index}`}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="pac-ficha-text pac-muted">—</p>
              )}
            </section>
          );
        })}
      </div>
      <section className="pac-ficha-section">
        <h3 className="pac-subsection-title">Observações</h3>
        <p className="pac-ficha-text">{notes.trim() ? notes : <span className="pac-muted">—</span>}</p>
      </section>
    </div>
  );
}

export function PlanActionsReadContent({ actions }: { actions: PlanAction[] }) {
  if (!actions.length) {
    return <p className="pac-muted">Nenhuma ação cadastrada.</p>;
  }

  return (
    <div className="pac-table-wrap">
      <table className="pac-table pac-table--compact-read">
        <thead>
          <tr>
            <th>Tipo</th>
            <th>Descrição</th>
            <th>Responsável</th>
            <th>Prazo</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {actions.map((action) => (
            <tr key={action.id}>
              <td>{actionTypeLabel(action.action_type)}</td>
              <td>{action.description}</td>
              <td>
                <ActionResponsiblesChips action={action} layout="stack" />
              </td>
              <td>{formatDate(action.due_date)}</td>
              <td>{ACTION_STATUSES[action.status] ?? action.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Rnc8dEffectivenessRead({ value }: { value: Rnc8dReportPayload }) {
  const eff = payloadOf(value).effectiveness ?? {};

  return (
    <div className="pac-ficha">
      <ReadOnlyGrid>
        <ReadOnlyField
          label="O problema foi resolvido? Como?"
          value={eff.resolved_how}
          fullWidth
          multiline
        />
        <ReadOnlyField label="Data material OK" value={eff.ok_material_date} />
        <ReadOnlyField label="Identificação peças novas" value={eff.new_parts_identification} />
        <ReadOnlyField label="Responsável verificação" value={eff.verification_responsible} />
        <ReadOnlyField label="Data verificação" value={eff.verification_date} />
      </ReadOnlyGrid>
    </div>
  );
}

export function Rnc8dPreventiveRead({ value }: { value: Rnc8dReportPayload }) {
  const payload = payloadOf(value);
  const preventive = payload.preventive ?? {};
  const docs = payload.documentation_updates ?? [];

  return (
    <div className="pac-ficha">
      <ReadOnlyGrid>
        <ReadOnlyField label="Como evitar no futuro?" value={preventive.how_avoid_future} fullWidth multiline />
        <ReadOnlyField
          label="Outros processos/produtos"
          value={preventive.other_processes_products}
          fullWidth
          multiline
        />
        <ReadOnlyField label="Responsável avaliação" value={preventive.evaluation_responsible} />
        <ReadOnlyField label="Data conclusão avaliação" value={preventive.evaluation_completion_date} />
      </ReadOnlyGrid>
      <section className="pac-ficha-section">
        <h3 className="pac-subsection-title">Atualização de documentos</h3>
        {docs.some((doc) => doc.document?.trim() || doc.responsible?.trim()) ? (
          <div className="pac-table-wrap">
            <table className="pac-table pac-table--compact-read">
              <thead>
                <tr>
                  <th>Documento</th>
                  <th>Responsável</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((doc, index) => (
                  <tr key={`doc-read-${index}`}>
                    <td>{doc.document?.trim() || "—"}</td>
                    <td>{doc.responsible?.trim() || "—"}</td>
                    <td>{doc.date?.trim() || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="pac-ficha-text pac-muted">Nenhum documento listado.</p>
        )}
      </section>
    </div>
  );
}

export function Rnc8dClosureRead({ value }: { value: Rnc8dReportPayload }) {
  return (
    <div className="pac-ficha">
      <ReadOnlyField
        label="Fechamento 8D (uso do cliente)"
        hint={PAC_HELP_TOOLTIPS.rnc8d.clientClosure}
        value={payloadOf(value).client_closure_note}
        fullWidth
        multiline
      />
    </div>
  );
}

export function EffectivenessPacReadContent({
  status,
  notes,
  proposedStatus,
  rejectionReason,
}: {
  status: string;
  notes: string;
  proposedStatus?: string | null;
  rejectionReason?: string | null;
}) {
  return (
    <div className="pac-ficha">
      <ReadOnlyGrid>
        <ReadOnlyField
          label="Resultado"
          hint={PAC_HELP_TOOLTIPS.detail.effectivenessResult}
          value={
            EFFECTIVENESS_STATUSES.find((item) => item.value === status)?.label ?? status
          }
        />
        {proposedStatus ? (
          <ReadOnlyField
            label="Proposta (aguardando aprovação)"
            value={
              EFFECTIVENESS_STATUSES.find((item) => item.value === proposedStatus)?.label
              ?? proposedStatus
            }
          />
        ) : null}
        <ReadOnlyField
          label="Observações"
          hint={PAC_HELP_TOOLTIPS.detail.effectivenessNotes}
          value={notes}
          fullWidth
          multiline
        />
        {rejectionReason ? (
          <ReadOnlyField label="Motivo rejeição" value={rejectionReason} fullWidth multiline />
        ) : null}
      </ReadOnlyGrid>
    </div>
  );
}

// Helper de rótulo reutilizado no cabeçalho do detalhe.
// eslint-disable-next-line react-refresh/only-export-components
export function labelForPlanStatus(value: string): string {
  return PLAN_STATUSES.find((item) => item.value === value)?.label ?? value;
}
