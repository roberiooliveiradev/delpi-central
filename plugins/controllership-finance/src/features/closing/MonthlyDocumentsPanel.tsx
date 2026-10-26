/**
 * Aba «Documentos e interações» — V0.2 (doc 112 §38 / Plano 113 §17).
 *
 * Cartões por documento lógico — nunca tabela: cada exigência do
 * checklist (item esperado) vira um cartão «Exigido»; cada evidência
 * anexada diretamente à competência (`link_kind=competence`) vira um
 * cartão «Adicional». Ações levam à página de detalhe (deep route),
 * nunca a uma quarta aba.
 *
 * «Solicitações que precisam de atenção» consome somente dados reais:
 * decisões de validação `REJECTED` correntes por item
 * (`getItemValidation`) — a solicitação de ajuste é a decisão com
 * motivo/comentário registrados pelo revisor. Não existe contrato de
 * conversa livre por documento; a seção nunca simula mensagens.
 *
 * Sem falso zero: dados ausentes/indisponíveis exibem «—».
 */
import { useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  getItemValidation,
  listCompetenceItems,
  type CompetenceChecklistItem,
  type ItemValidation,
} from "../../api/competencesApi";
import {
  listClosingDocuments,
  type ClosingDocument,
} from "../../api/documentsApi";
import { CfQueryErrorBanner } from "../../app/cfFeedbackUi";
import {
  FilterInputField,
  FiltersRow,
  FilterSelectField,
} from "../../app/cfFiltersUi";
import {
  CfActionButton,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import { REJECTION_REASON_LABELS } from "./ItemValidationPanel";

type PanelError = { status: number; code: string | null; message: string };

const LIST_ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para consultar os documentos.",
  competence_not_opened: "O fechamento deste mês ainda não foi aberto.",
};

function toPanelError(error: unknown, fallback: string): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code,
      message:
        (error.code && LIST_ERROR_MESSAGES[error.code]) || error.message,
    };
  }
  return { status: 0, code: null, message: fallback };
}

const ITEM_STATE_LABELS: Record<string, string> = {
  EXPECTED: "Aguardando documento",
  ACCEPTED: "Conferido",
  NOT_APPLICABLE: "Não se aplica",
  CANCELLED: "Cancelado",
};

const ITEM_STATE_VARIANTS: Record<string, "warning" | "success" | "neutral"> =
  {
    EXPECTED: "warning",
    ACCEPTED: "success",
    NOT_APPLICABLE: "neutral",
    CANCELLED: "neutral",
  };

const DOC_STATE_LABELS: Record<string, string> = {
  ATTACHED: "Arquivo enviado",
  SUPERSEDED: "Substituído",
  CANCELLED: "Cancelado",
};

/** Filtro de situação — apenas estados deriváveis de contratos reais. */
const SITUATION_OPTIONS = [
  { value: "all", label: "Todas as situações" },
  { value: "missing", label: "Aguardando documento" },
  { value: "attention", label: "Com ajuste solicitado" },
  { value: "sent", label: "Com arquivo enviado" },
  { value: "accepted", label: "Conferidos" },
] as const;

export type DocumentCard = {
  ref: string;
  name: string;
  kind: "required" | "additional";
  situation: string;
  stateLabel: string;
  stateVariant: "warning" | "success" | "neutral" | "danger" | "info";
  versionText: string | null;
  updatedAt: string | null;
  pendingRequests: number;
};

function latestDecisionRejected(validation: ItemValidation): number {
  const rejected = validation.decisions.filter(
    (d) => d.decision === "REJECTED" && !d.reverses_decision_id,
  );
  const reversedIds = new Set(
    validation.decisions
      .filter((d) => d.decision === "REVERSED" && d.reverses_decision_id)
      .map((d) => d.reverses_decision_id as string),
  );
  return rejected.filter((d) => !reversedIds.has(d.decision_id)).length;
}

export function MonthlyDocumentsPanel({
  period,
  search,
  stateFilter,
  onFiltersChange,
  onOpenDetail,
}: {
  period: string;
  search: string;
  stateFilter: string;
  onFiltersChange: (next: { search?: string; state?: string }) => void;
  onOpenDetail: (ref: string) => void;
}) {
  const [itemsResult, setItemsResult] = useState<{
    key: string;
    items: CompetenceChecklistItem[];
  } | null>(null);
  const [docsResult, setDocsResult] = useState<{
    key: string;
    documents: ClosingDocument[];
  } | null>(null);
  const [validationsResult, setValidationsResult] = useState<{
    key: string;
    byItem: Record<string, ItemValidation>;
  } | null>(null);
  const [error, setError] = useState<{ key: string; error: PanelError } | null>(
    null,
  );
  const requestId = useRef(0);
  const [retryNonce, setRetryNonce] = useState(0);
  const key = `docs:${period}:${retryNonce}`;

  const items = itemsResult?.key === key ? itemsResult.items : null;
  const documents =
    docsResult?.key === key ? docsResult.documents : null;
  const validations = useMemo(
    () =>
      validationsResult?.key === key ? validationsResult.byItem : {},
    [validationsResult, key],
  );
  const currentError = error?.key === key ? error.error : null;
  const loading = (items === null || documents === null) && !currentError;

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    const guarded =
      <T,>(p: Promise<T>) =>
        p.then((v) => {
          if (!controller.signal.aborted && requestId.current === id) {
            return v;
          }
          return null;
        });
    Promise.all([
      guarded(listCompetenceItems(period, {}, { signal: controller.signal })),
      guarded(
        listClosingDocuments(period, {}, { signal: controller.signal }),
      ),
    ])
      .then(([itemList, docList]) => {
        if (!itemList || !docList) return;
        setItemsResult({ key, items: itemList });
        setDocsResult({ key, documents: docList.documents });
        setError(null);
        // Decisões por item — dados reais das solicitações de ajuste.
        if (itemList.length > 0) {
          Promise.all(
            itemList.map((item) =>
              guarded(
                getItemValidation(period, item.item_key, {
                  signal: controller.signal,
                }),
              ).then((v) => [item.item_key, v] as const),
            ),
          ).then((entries) => {
            if (controller.signal.aborted || requestId.current !== id)
              return;
            const byItem: Record<string, ItemValidation> = {};
            for (const [itemKey, v] of entries) {
              if (v) byItem[itemKey] = v;
            }
            setValidationsResult({ key, byItem });
          });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError({
          key,
          error: toPanelError(err, "Falha ao listar os documentos do mês."),
        });
      });
    return () => controller.abort();
  }, [period, key]);

  const retry = () => setRetryNonce((n) => n + 1);

  const docsByItem = useMemo(() => {
    const map = new Map<string, ClosingDocument[]>();
    for (const doc of documents ?? []) {
      if (doc.state === "CANCELLED" || !doc.snapshot_item_id) continue;
      const list = map.get(doc.snapshot_item_id) ?? [];
      list.push(doc);
      map.set(doc.snapshot_item_id, list);
    }
    return map;
  }, [documents]);

  const additionalDocs = useMemo(
    () =>
      (documents ?? []).filter(
        (d) => d.link_kind === "competence" && d.state !== "CANCELLED",
      ),
    [documents],
  );

  const cards: DocumentCard[] = useMemo(() => {
    const list: DocumentCard[] = [];
    for (const item of items ?? []) {
      const docs = docsByItem.get(item.snapshot_item_id) ?? [];
      const latest = docs.reduce<ClosingDocument | null>(
        (acc, d) =>
          !acc ||
          (d.updated_at ?? d.created_at ?? "") >
            (acc.updated_at ?? acc.created_at ?? "")
            ? d
            : acc,
        null,
      );
      const pending = latestDecisionRejected(
        validations[item.item_key] ?? {
          snapshot_item_id: item.snapshot_item_id,
          item_key: item.item_key,
          state: item.state,
          validation_scope: item.validation_scope,
          applicability: item.applicability,
          documents: [],
          decisions: [],
        },
      );
      const hasFile = docs.length > 0;
      const situation = pending > 0
        ? "attention"
        : item.state === "ACCEPTED"
          ? "accepted"
          : hasFile
            ? "sent"
            : "missing";
      list.push({
        ref: `item:${item.item_key}`,
        name: item.name,
        kind: "required",
        situation,
        stateLabel: ITEM_STATE_LABELS[item.state] ?? item.state,
        stateVariant:
          pending > 0
            ? "danger"
            : (ITEM_STATE_VARIANTS[item.state] ?? "neutral"),
        versionText: latest ? `v${latest.current_version_no}` : null,
        updatedAt: latest
          ? (latest.updated_at ?? latest.created_at)
          : null,
        pendingRequests: pending,
      });
    }
    for (const doc of additionalDocs) {
      list.push({
        ref: doc.document_id,
        name: doc.title ?? doc.original_name ?? "Documento adicional",
        kind: "additional",
        situation: "sent",
        stateLabel: DOC_STATE_LABELS[doc.state] ?? doc.state,
        stateVariant: "info",
        versionText: `v${doc.current_version_no}`,
        updatedAt: doc.updated_at ?? doc.created_at,
        pendingRequests: 0,
      });
    }
    return list;
  }, [items, additionalDocs, docsByItem, validations]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return cards.filter(
      (card) =>
        (q === "" || card.name.toLowerCase().includes(q)) &&
        (stateFilter === "all" ||
          stateFilter === "" ||
          card.situation === stateFilter),
    );
  }, [cards, search, stateFilter]);

  const attentionRequests = useMemo(() => {
    const list: {
      itemKey: string;
      docName: string;
      reason: string;
      comment: string | null;
      decidedBy: string;
      at: string | null;
    }[] = [];
    for (const item of items ?? []) {
      const validation = validations[item.item_key];
      if (!validation) continue;
      const reversed = new Set(
        validation.decisions
          .filter((d) => d.decision === "REVERSED" && d.reverses_decision_id)
          .map((d) => d.reverses_decision_id as string),
      );
      for (const decision of validation.decisions) {
        if (
          decision.decision === "REJECTED" &&
          !reversed.has(decision.decision_id)
        ) {
          list.push({
            itemKey: item.item_key,
            docName: item.name,
            reason:
              REJECTION_REASON_LABELS[
                decision.reason_code ?? "OTHER"
              ] ?? "Ajuste solicitado",
            comment: decision.comment,
            decidedBy: decision.decided_by,
            at: decision.created_at,
          });
        }
      }
    }
    return list;
  }, [items, validations]);

  if (currentError) {
    return (
      <CfQueryErrorBanner
        error={currentError}
        dataset="os documentos do mês"
        onRetry={retry}
      />
    );
  }

  return (
    <div className="cf-monthly-documents">
      <CfSectionCard
        title="Documentos deste mês"
        hint={CF_HELP.monthlyClosing.documentsTab}
      >
        <p className="cf-section-subtitle">
          Acompanhe os documentos do fechamento e as solicitações de ajuste.
        </p>
        <FiltersRow>
          <FilterInputField
            id="cf-documents-search"
            label="Pesquisar documento"
            type="search"
            value={search}
            onChange={(value) => onFiltersChange({ search: value })}
          />
          <FilterSelectField
            id="cf-documents-state"
            label="Situação"
            value={stateFilter || "all"}
            options={SITUATION_OPTIONS.map((o) => ({
              value: o.value,
              label: o.label,
            }))}
            onChange={(value) => onFiltersChange({ state: value })}
          />
        </FiltersRow>
        <div className="cf-settlements-actions">
          <CfActionButton
            variant="ghost"
            onClick={() => onOpenDetail("new")}
          >
            Adicionar documento
          </CfActionButton>
        </div>

        {loading ? (
          <p aria-live="polite">Carregando documentos…</p>
        ) : null}

        {!loading && filtered.length === 0 ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage={
              cards.length === 0
                ? "Nenhum documento exigido para este fechamento."
                : "Nenhum documento corresponde à pesquisa ou ao filtro."
            }
          />
        ) : null}

        {filtered.length > 0 ? (
          <ul className="cf-document-cards" aria-label="Documentos do mês">
            {filtered.map((card) => (
              <li key={card.ref} className="cf-document-card">
                <div className="cf-document-card__head">
                  <strong>{card.name}</strong>
                  <CfStatusBadge
                    variant={card.stateVariant}
                    label={card.stateLabel}
                  />
                </div>
                <p className="cf-document-card__meta">
                  {card.kind === "required" ? "Exigido" : "Adicional"}
                  {card.versionText ? ` · ${card.versionText}` : ""}
                  {card.updatedAt
                    ? ` · ${formatDateTime(card.updatedAt)}`
                    : ""}
                </p>
                {card.pendingRequests > 0 ? (
                  <p className="cf-document-card__attention">
                    {card.pendingRequests} solicitação(ões) aguardando
                    atenção
                  </p>
                ) : null}
                <CfActionButton
                  variant="ghost"
                  onClick={() => onOpenDetail(card.ref)}
                >
                  Ver documento
                </CfActionButton>
              </li>
            ))}
          </ul>
        ) : null}
      </CfSectionCard>

      <CfSectionCard
        title="Solicitações que precisam de atenção"
        hint={CF_HELP.monthlyClosing.requestsSummary}
      >
        {attentionRequests.length === 0 ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhuma solicitação aguardando resposta neste mês."
          />
        ) : (
          <ul
            className="cf-request-list"
            aria-label="Solicitações de ajuste"
          >
            {attentionRequests.map((request) => (
              <li key={`${request.itemKey}:${request.at}`}>
                <strong>{request.docName}</strong> — {request.reason}
                {request.comment ? ` · ${request.comment}` : ""}
                <span className="cf-request-list__meta">
                  {" "}
                  · {request.decidedBy}
                  {request.at ? ` · ${formatDateTime(request.at)}` : ""}
                </span>
                <CfActionButton
                  variant="ghost"
                  onClick={() => onOpenDetail(`item:${request.itemKey}`)}
                >
                  Abrir conversa
                </CfActionButton>
              </li>
            ))}
          </ul>
        )}
      </CfSectionCard>
    </div>
  );
}
