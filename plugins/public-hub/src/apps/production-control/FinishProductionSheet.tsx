import { useEffect, useRef } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { ArrowRight, Loader2, Square } from "lucide-react";
import type { MachineLoadOperation, ProductionRunSnapshot } from "./api.ts";
import type { useRunHandoff } from "./useRunHandoff.ts";
import { formatQty } from "./cockpitShared";

type Props = {
  /** Controlador único da troca guiada — mesmo objeto no card e no detalhe. */
  handoff: ReturnType<typeof useRunHandoff>;
  /** Operação da fila exibida (rótulos/descrição canônicos). */
  operation: MachineLoadOperation;
  /** Run oficial no contador deste posto (dados exibidos no modal). */
  run: ProductionRunSnapshot | null;
  /** Contagem corrente já na unidade do operador. */
  countedLabel: string;
  /** busy do useProductionRun — Stop em voo desabilita as opções. */
  busy: boolean;
  /** Falha do último Stop tradicional — ação continua recuperável. */
  stopError?: string | null;
  /** Opção A: encerramento tradicional — executa o stop() vigente. */
  onStop: () => Promise<void>;
  /** Código pending_classification: abre o fluxo de classificação existente. */
  onRequestClassify: () => void;
};

/**
 * Modal de decisão do Encerrar (E2): duas opções claras + Cancelar.
 * "Ir para a próxima OP" confirma na hora — sem segunda etapa e sem
 * Play: o novo run nasce running na transação atômica da E1.
 */
export function FinishProductionSheet({
  handoff,
  operation,
  run,
  countedLabel,
  busy,
  stopError = null,
  onStop,
  onRequestClassify,
}: Props) {
  const stopRef = useRef<HTMLButtonElement | null>(null);
  const {
    isOpen,
    phase,
    preview,
    previewError,
    previewing,
    submitting,
    uncertain,
    conflict,
    notice,
    uncertainMessage,
    refreshPreview,
    close,
    confirmNext,
  } = handoff;

  // Foco inicial: a decisão mais conservadora (encerramento tradicional).
  useEffect(() => {
    if (isOpen) stopRef.current?.focus();
  }, [isOpen]);

  if (!isOpen) return null;

  const next = preview?.nextOperation ?? null;
  const nextBlocked = preview != null && !preview.available;
  const blockMessage = nextBlocked ? preview.block?.message ?? null : null;
  // Troca travada também por conflito impeditivo do último POST e por
  // resultado incerto — a única escrita válida nesse estado é o retry
  // do mesmo requestId (confirmNext valida internamente além do atributo).
  const nextDisabled =
    busy ||
    submitting ||
    uncertain ||
    previewing ||
    Boolean(previewError) ||
    Boolean(conflict?.blocksNext) ||
    next == null ||
    nextBlocked;
  // Resultado incerto: nenhuma escrita contraditória (Stop, nova troca)
  // pode sair antes da reconciliação segura.
  const stopDisabled = busy || submitting || uncertain;
  const closingSafe = !submitting;
  const operationLabel = run
    ? `${run.productionOrder} · ${run.operationCode}`
    : "";

  const handleKeyDown = (event: ReactKeyboardEvent) => {
    if (event.key === "Escape" && closingSafe) close();
  };

  return (
    <div
      className="pcp-pub-modal pcp-pub-finish"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-finish-title"
      onKeyDown={handleKeyDown}
    >
      <button
        type="button"
        className="pcp-pub-modal__backdrop"
        aria-label="Fechar"
        onClick={closingSafe ? close : undefined}
        disabled={!closingSafe}
      />
      <div className="pcp-pub-modal__panel pcp-pub-finish__panel">
        <h3 id="pcp-finish-title" className="pcp-pub__run-title">
          Finalizar operação
        </h3>
        <p className="pcp-pub__run-note">
          O que deseja fazer com a produção atual?
        </p>

        <div className="pcp-pub-finish__current" aria-label="Produção atual">
          <span className="pcp-pub-finish__current-op">{operationLabel}</span>
          <span className="pcp-pub-finish__current-desc">
            {operation.operation_description}
            {operation.product_description
              ? ` · ${operation.product_description}`
              : ""}
          </span>
          <span className="pcp-pub-finish__current-count">
            {countedLabel} contadas
          </span>
        </div>

        <div className="pcp-pub-finish__options">
          <button
            ref={stopRef}
            type="button"
            className="pcp-pub-finish__option"
            onClick={() => void onStop()}
            disabled={stopDisabled}
          >
            <span className="pcp-pub-finish__option-icon" aria-hidden="true">
              {busy ? <Loader2 size={20} className="pcp-pub-finish__spin" /> : <Square size={20} />}
            </span>
            <span className="pcp-pub-finish__option-text">
              <strong>{busy ? "Encerrando…" : "Encerrar produção"}</strong>
              <span>Finalizar esta OP sem iniciar outra.</span>
            </span>
          </button>

          <button
            type="button"
            className="pcp-pub-finish__option pcp-pub-finish__option--next"
            onClick={() => void confirmNext()}
            disabled={nextDisabled}
            aria-disabled={nextDisabled}
          >
            <span className="pcp-pub-finish__option-icon" aria-hidden="true">
              {submitting ? (
                <Loader2 size={20} className="pcp-pub-finish__spin" />
              ) : (
                <ArrowRight size={20} />
              )}
            </span>
            <span className="pcp-pub-finish__option-text">
              <strong>
                {submitting ? "Trocando de OP…" : "Ir para a próxima OP"}
              </strong>
              <span>Finalizar a OP atual e iniciar automaticamente a contagem da próxima.</span>
              {previewing ? (
                <span className="pcp-pub-finish__next-detail">
                  Consultando a próxima OP…
                </span>
              ) : null}
              {next && !nextBlocked ? (
                <span className="pcp-pub-finish__next-detail">
                  {next.productionOrder} · {next.operationCode}
                  {next.operationDescription ? ` — ${next.operationDescription}` : ""}
                  {next.productDescription ? ` · ${next.productDescription}` : ""}
                  {next.pendingQty != null
                    ? ` · saldo ${formatQty(next.pendingQty)}`
                    : ""}
                  {next.queuePosition != null && next.queueSize != null
                    ? ` · posição ${next.queuePosition}/${next.queueSize}`
                    : ""}
                </span>
              ) : null}
            </span>
          </button>
        </div>

        {stopError ? (
          <p className="pcp-pub__run-error" role="alert">
            {stopError}
          </p>
        ) : null}

        {previewing ? null : previewError ? (
          <p className="pcp-pub__run-error" role="alert">
            Troca indisponível: {previewError}{" "}
            <button
              type="button"
              className="pcp-pub__link-btn"
              onClick={refreshPreview}
            >
              Tentar novamente
            </button>
          </p>
        ) : null}

        {!previewing && preview && nextBlocked ? (
          <div className="pcp-pub-finish__block" role="status">
            <p className="pcp-pub__run-note">
              {blockMessage ?? "Não há próxima OP disponível para este posto."}
            </p>
            {preview.block?.code === "pending_classification" ? (
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--ghost"
                onClick={onRequestClassify}
                disabled={busy || submitting}
              >
                Informar motivo
              </button>
            ) : (
              <button
                type="button"
                className="pcp-pub__link-btn"
                onClick={refreshPreview}
              >
                Tentar novamente
              </button>
            )}
          </div>
        ) : null}

        {notice ? (
          <p className="pcp-pub__run-note pcp-pub-finish__notice" role="status">
            {notice}
          </p>
        ) : null}

        {conflict ? (
          <div className="pcp-pub-finish__conflict" role="alert">
            <p className="pcp-pub-finish__conflict-title">{conflict.title}</p>
            <p className="pcp-pub__run-note">{conflict.message}</p>
            {conflict.action === "classify" ? (
              <button
                type="button"
                className="pcp-pub__btn pcp-pub__btn--ghost"
                onClick={onRequestClassify}
                disabled={busy || submitting}
              >
                Informar motivo
              </button>
            ) : null}
          </div>
        ) : null}

        {phase === "uncertain" ? (
          <div className="pcp-pub-finish__conflict" role="alert">
            <p className="pcp-pub-finish__conflict-title">
              Confirmação pendente
            </p>
            <p className="pcp-pub__run-note">{uncertainMessage}</p>
            <button
              type="button"
              className="pcp-pub__btn pcp-pub__btn--ghost"
              onClick={() => void confirmNext()}
              disabled={submitting}
            >
              Tentar novamente
            </button>
          </div>
        ) : null}

        <div className="pcp-pub__run-actions">
          <button
            type="button"
            className="pcp-pub__btn pcp-pub__btn--ghost"
            onClick={close}
            disabled={submitting}
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
