import { ActionButton } from "@delpi/plugin-ui/index";
import { FileText } from "lucide-react";
import { useMemo, useState } from "react";

import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { formatDateTimePtBr } from "../../../content/presentationLabels";
import { PersonIdentity } from "../../../components/PersonIdentity";
import { RequestFilePreviewModal } from "../../../components/RequestFilePreviewModal";
import { DetailFields, MyRequestsSectionCard } from "../../../ui/mrUi";
import {
  formatProcessIssueQty,
  formatProcessIssueSchedule,
  parseProcessIssuePayload,
  type ProcessIssuePayloadView,
} from "../domain/processIssuePayload";

type ProcessIssuePayloadPanelProps = {
  requestId: string;
  payload: Record<string, unknown>;
};

function DrawingIcon() {
  return (
    <FileText
      aria-hidden="true"
      size={14}
      style={{ verticalAlign: "-0.15em", marginRight: "0.3rem" }}
    />
  );
}

function productLabel(
  code: string | null,
  description: string | null,
): string | null {
  if (!code) return null;
  return description ? `${code} · ${description}` : code;
}

function quantitiesFields(view: ProcessIssuePayloadView) {
  const fields: Array<{ label: string; value: string }> = [];
  const planned = formatProcessIssueQty(view.plannedQty);
  const pending = formatProcessIssueQty(view.pendingQty);
  const operationPending = formatProcessIssueQty(view.operationPendingQty);
  if (planned != null) {
    fields.push({ label: "Quantidade planejada", value: planned });
  }
  if (operationPending != null) {
    fields.push({
      label: "Pendente da operação",
      value: operationPending,
    });
  }
  if (pending != null) {
    fields.push({ label: "Pendente da OP", value: pending });
  }
  return fields;
}

function scheduleFields(view: ProcessIssuePayloadView) {
  const fields: Array<{ label: string; value: string }> = [];
  const start = formatProcessIssueSchedule(
    view.scheduledDate,
    view.scheduledStartTime,
  );
  const end = formatProcessIssueSchedule(
    view.scheduledEndDate ?? view.scheduledDate,
    view.scheduledEndTime,
  );
  const due = formatProcessIssueSchedule(view.dueDate, null);
  if (start) fields.push({ label: "Início programado", value: start });
  if (end) fields.push({ label: "Fim programado", value: end });
  if (due) fields.push({ label: "Entrega", value: due });
  return fields;
}

/**
 * Painel do analista de Processos — interpreta o snapshot persistido na
 * solicitação (P2). O desenho do PA é a única consulta em tempo real e só
 * ocorre ao clicar em «Abrir desenho».
 */
export function ProcessIssuePayloadPanel({
  requestId,
  payload,
}: ProcessIssuePayloadPanelProps) {
  const view = useMemo(() => parseProcessIssuePayload(payload), [payload]);
  const [drawingOpen, setDrawingOpen] = useState(false);

  const paCode = view.paProductCode;
  const drawingFileName = paCode ? `${paCode}.pdf` : "desenho.pdf";

  return (
    <div className="my-requests-process-issue" data-help="process-issue-payload">
      <MyRequestsSectionCard
        title="Problema informado"
        hint={MY_REQUESTS_HELP_TOOLTIPS.detail.processIssueReport}
      >
        <p className="my-requests-process-issue__reason">
          <span
            className="my-requests-process-issue__reason-icon"
            aria-hidden="true"
          >
            ⚠
          </span>
          {view.issueLabel}
        </p>
        <DetailFields
          fields={[
            {
              label: "Registrado em",
              value: formatDateTimePtBr(view.reportedAt),
            },
            {
              label: "Operador",
              value: view.operatorCode || view.operatorName ? (
                <PersonIdentity
                  name={view.operatorName || view.operatorCode}
                  userId={view.operatorCode}
                />
              ) : (
                "—"
              ),
            },
            ...(view.reportedToolCode
              ? [
                  {
                    label: "Ferramenta informada pelo operador",
                    value: (
                      <code className="my-requests-process-issue__code">
                        {view.reportedToolCode}
                      </code>
                    ),
                  },
                ]
              : []),
            ...(view.reportedMaterialCode
              ? [
                  {
                    label: "Material informado pelo operador",
                    value: (
                      <code className="my-requests-process-issue__code">
                        {view.reportedMaterialCode}
                      </code>
                    ),
                  },
                ]
              : []),
          ]}
        />
        {view.note ? (
          <div className="my-requests-process-issue__note">
            <p className="my-requests-process-issue__note-label">
              Observação do operador
            </p>
            <p className="my-requests-process-issue__note-text">{view.note}</p>
          </div>
        ) : null}
      </MyRequestsSectionCard>

      <MyRequestsSectionCard
        title="Contexto da produção"
        hint={MY_REQUESTS_HELP_TOOLTIPS.detail.processIssueContext}
      >
        <DetailFields
          fields={[
            { label: "Ordem de produção", value: view.productionOrder ?? "—" },
            {
              label: "Operação",
              value: view.operationCode
                ? view.operationDescription
                  ? `${view.operationCode} · ${view.operationDescription}`
                  : view.operationCode
                : "—",
            },
            {
              label: "Posto de trabalho",
              value: view.reportedWorkCenter
                ? view.workCenterName
                  ? `${view.reportedWorkCenter} · ${view.workCenterName}`
                  : view.reportedWorkCenter
                : "—",
            },
            {
              label: "Produto da operação",
              value:
                productLabel(view.productCode, view.productDescription) ?? "—",
            },
            { label: "Unidade", value: view.unit ?? "—" },
            {
              label: "Produto acabado",
              value: paCode ? (
                <span className="my-requests-process-issue__pa">
                  <span className="my-requests-process-issue__pa-label">
                    {productLabel(paCode, view.paProductDescription)}
                  </span>
                  <ActionButton
                    type="button"
                    variant="ghost"
                    onClick={() => setDrawingOpen(true)}
                    title="Abrir o desenho atual do produto acabado"
                  >
                    <DrawingIcon />
                    Abrir desenho
                  </ActionButton>
                </span>
              ) : (
                "Produto acabado não informado no momento do reporte."
              ),
            },
            ...quantitiesFields(view),
            ...scheduleFields(view),
          ]}
        />
      </MyRequestsSectionCard>

      <MyRequestsSectionCard
        title="Processo no momento do reporte"
        hint={MY_REQUESTS_HELP_TOOLTIPS.detail.processIssueSnapshot}
      >
        <DetailFields
          fields={[
            {
              label: "Ferramenta vinculada na operação",
              value: view.toolSnapshot ? (
                <code className="my-requests-process-issue__code">
                  {view.toolSnapshot}
                </code>
              ) : (
                "Nenhuma informada"
              ),
            },
            { label: "Recurso / máquina", value: view.resource ?? "—" },
          ]}
        />
      </MyRequestsSectionCard>

      <MyRequestsSectionCard
        title="Materiais vinculados no momento do reporte"
        hint={MY_REQUESTS_HELP_TOOLTIPS.detail.processIssueMaterials}
      >
        {!view.materialsSnapshotAvailable ? (
          <p className="my-requests-process-issue__materials-empty">
            Não foi possível consultar os materiais vinculados no momento em
            que a ocorrência foi registrada.
          </p>
        ) : view.materials.length === 0 ? (
          <p className="my-requests-process-issue__materials-empty">
            Nenhum material vinculado foi encontrado no momento do reporte.
          </p>
        ) : (
          <div className="my-requests-process-issue__materials-scroll">
            <table className="my-requests-process-issue__materials">
              <thead>
                <tr>
                  <th scope="col">Material</th>
                  <th scope="col">Un.</th>
                  <th scope="col">Qtd. original</th>
                  <th scope="col">Em aberto</th>
                  <th scope="col">Consumida</th>
                </tr>
              </thead>
              <tbody>
                {view.materials.map((material, index) => (
                  <tr key={material.productCode ?? `material-${index}`}>
                    <td>
                      <span className="my-requests-process-issue__material-code">
                        {material.productCode ?? "—"}
                      </span>
                      {material.description ? (
                        <span className="my-requests-process-issue__material-desc">
                          {material.description}
                        </span>
                      ) : null}
                    </td>
                    <td>{material.unit ?? "—"}</td>
                    <td>{formatProcessIssueQty(material.originalQty) ?? "—"}</td>
                    <td>{formatProcessIssueQty(material.openQty) ?? "—"}</td>
                    <td>{formatProcessIssueQty(material.consumedQty) ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </MyRequestsSectionCard>

      <RequestFilePreviewModal
        open={drawingOpen}
        onClose={() => setDrawingOpen(false)}
        target={
          paCode
            ? {
                kind: "product_drawing",
                requestId,
                fileName: drawingFileName,
                contentType: "application/pdf",
              }
            : null
        }
      />
    </div>
  );
}
