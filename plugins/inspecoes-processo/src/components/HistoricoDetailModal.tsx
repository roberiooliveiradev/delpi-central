import { useEffect } from "react";
import { X } from "lucide-react";

import { Pagination } from "./Pagination";
import { useInspecoesProcessoHistoricoDetalhe } from "../hooks/useInspecoesProcessoHistoricoDetalhe";
import type {
  InspecoesProcessoHistoricoDetalheItem,
  InspecoesProcessoHistoricoItem,
} from "../types/api";
import { formatIsoDatePt, formatNumber } from "../utils/format";

type HistoricoDetailModalProps = {
  branch: string;
  ordemProducao: string | null;
  onClose: () => void;
};

function textOrDash(value: string | null | undefined): string {
  const normalized = value?.trim();
  return normalized ? normalized : "—";
}

function formatDateTime(
  date: string | null | undefined,
  time: string | null | undefined,
): string {
  const dateLabel = formatIsoDatePt(date);
  const timeLabel = time?.trim();
  if (dateLabel === "—" && !timeLabel) return "—";
  if (dateLabel === "—") return timeLabel || "—";
  return timeLabel ? `${dateLabel} ${timeLabel}` : dateLabel;
}

function formatEspecificacao(item: InspecoesProcessoHistoricoDetalheItem): string {
  const esperada = item.especificacao_esperada?.trim();
  if (esperada) return esperada;

  const textual = item.especificacao_textual?.trim();
  if (textual) return textual;

  const nominal = item.valor_nominal?.trim();
  const inferior = item.limite_inferior_especificacao?.trim();
  const superior = item.limite_superior_especificacao?.trim();
  const unidade = item.unidade_especificacao?.trim();

  const parts: string[] = [];
  if (nominal) parts.push(`Nom. ${nominal}`);
  if (inferior || superior) {
    parts.push(`${inferior || "—"} … ${superior || "—"}`);
  }
  if (unidade) parts.push(unidade);

  return parts.length > 0 ? parts.join(" · ") : "—";
}

function formatMedicao(item: InspecoesProcessoHistoricoDetalheItem): string {
  const numerica = item.medicao_numerica?.trim();
  if (numerica) return numerica;

  const textual = item.medicao_textual?.trim();
  if (textual) return textual;

  if (item.medicao_numerica_a != null && !Number.isNaN(item.medicao_numerica_a)) {
    return formatNumber(item.medicao_numerica_a);
  }

  return "—";
}

function CabecalhoResumo({ cabecalho }: { cabecalho: InspecoesProcessoHistoricoItem }) {
  return (
    <div className="ip-modal__summary">
      <div className="ip-modal__summary-grid">
        <div>
          <p className="ip-modal__summary-label">OP</p>
          <p className="ip-modal__summary-value">{textOrDash(cabecalho.ordem_producao)}</p>
        </div>
        <div>
          <p className="ip-modal__summary-label">Produto</p>
          <p className="ip-modal__summary-value">
            {textOrDash(cabecalho.codigo_produto)}
            {cabecalho.descricao_produto?.trim()
              ? ` · ${cabecalho.descricao_produto.trim()}`
              : ""}
          </p>
        </div>
        <div>
          <p className="ip-modal__summary-label">Resultado</p>
          <p className="ip-modal__summary-value">
            {textOrDash(cabecalho.resultado_inspecao || cabecalho.resultado_inspecao_codigo)}
          </p>
        </div>
        <div>
          <p className="ip-modal__summary-label">Ensaios</p>
          <p className="ip-modal__summary-value">
            {formatNumber(cabecalho.qtde_ensaios)} · {formatNumber(cabecalho.qtde_ensaios_aprovados)}{" "}
            aprov. · {formatNumber(cabecalho.qtde_ensaios_reprovados)} reprov.
          </p>
        </div>
        <div>
          <p className="ip-modal__summary-label">Última medição</p>
          <p className="ip-modal__summary-value">
            {formatDateTime(cabecalho.ultima_data_medicao, cabecalho.ultima_hora_medicao)}
          </p>
        </div>
        <div>
          <p className="ip-modal__summary-label">Último ensaiador</p>
          <p className="ip-modal__summary-value">{textOrDash(cabecalho.nome_ultimo_ensaiador)}</p>
        </div>
      </div>
    </div>
  );
}

export function HistoricoDetailModal({
  branch,
  ordemProducao,
  onClose,
}: HistoricoDetailModalProps) {
  const {
    data,
    loading,
    error,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions,
    reload,
  } = useInspecoesProcessoHistoricoDetalhe(branch, ordemProducao);

  useEffect(() => {
    if (!ordemProducao) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [ordemProducao, onClose]);

  if (!ordemProducao) return null;

  const cabecalho = data?.cabecalho ?? null;
  const items = data?.items ?? [];
  const hasNext = Boolean(data?.has_next);

  return (
    <div className="ip-modal" role="dialog" aria-modal="true" aria-label="Detalhe da OP">
      <button
        type="button"
        className="ip-modal__backdrop"
        onClick={onClose}
        aria-label="Fechar detalhe"
      />
      <div className="ip-modal__panel">
        <header className="ip-modal__header">
          <div>
            <p className="ip-modal__eyebrow">Inspeções de Processo</p>
            <h2 className="ip-modal__title">
              Detalhe da OP {textOrDash(cabecalho?.ordem_producao || ordemProducao)}
            </h2>
          </div>
          <button type="button" className="ip-button" onClick={onClose}>
            <X size={16} aria-hidden="true" />
            Fechar
          </button>
        </header>

        <div className="ip-modal__body">
          {loading && !data ? (
            <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
              <p>Carregando detalhe da OP…</p>
            </div>
          ) : null}

          {error ? (
            <div className="ip-alert ip-alert--error" role="alert">
              <p>{error}</p>
              <button type="button" className="ip-button" onClick={reload}>
                Tentar novamente
              </button>
            </div>
          ) : null}

          {!loading && !error && cabecalho ? <CabecalhoResumo cabecalho={cabecalho} /> : null}

          {!loading && !error && cabecalho && items.length === 0 ? (
            <div className="ip-alert ip-alert--info" role="status">
              <p>Nenhuma medição encontrada para esta OP nesta página.</p>
            </div>
          ) : null}

          {!error && items.length > 0 ? (
            <>
              {loading ? (
                <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
                  <p>Atualizando medições…</p>
                </div>
              ) : null}
              <div className="ip-table-wrap">
                <table className="ip-table">
                  <thead>
                    <tr>
                      <th scope="col">Operação</th>
                      <th scope="col">Ensaio</th>
                      <th scope="col">Especificação</th>
                      <th scope="col">Medição</th>
                      <th scope="col">Resultado</th>
                      <th scope="col">Data/hora</th>
                      <th scope="col">Ensaiador</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item, index) => (
                      <tr
                        key={`${item.inspecao_id}-${item.ensaio_id}-${item.chave_medicao ?? index}`}
                      >
                        <td>
                          {textOrDash(item.operacao)}
                          {item.descricao_operacao?.trim()
                            ? ` · ${item.descricao_operacao.trim()}`
                            : ""}
                        </td>
                        <td className="ip-table__cell--wrap">
                          {textOrDash(item.codigo_ensaio)}
                          {item.nome_ensaio?.trim() ? ` · ${item.nome_ensaio.trim()}` : ""}
                        </td>
                        <td className="ip-table__cell--wrap">{formatEspecificacao(item)}</td>
                        <td>{formatMedicao(item)}</td>
                        <td>{textOrDash(item.resultado || item.resultado_codigo)}</td>
                        <td>{formatDateTime(item.data_medicao, item.hora_medicao)}</td>
                        <td className="ip-table__cell--wrap">
                          {textOrDash(item.nome_ensaiador)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <Pagination
                page={page}
                pageSize={pageSize}
                pageSizeOptions={pageSizeOptions}
                hasNext={hasNext}
                loading={loading}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
                ariaLabel="Paginação do detalhe da OP"
              />
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
