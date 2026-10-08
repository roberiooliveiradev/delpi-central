import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Eye, Link2, RefreshCw, Unlink } from "lucide-react";

import type { AppProps } from "../../App";
import {
  bpmnModelUrl,
  bpmnRevisionUrl,
  fetchBpmnModelCandidates,
  fetchBpmnModelRevisions,
  fetchProcessBpmnReference,
  removeProcessBpmnReference,
  setProcessBpmnReference,
  type BpmnModelCandidate,
  type BpmnRevisionCandidate,
  type ProcessBpmnReferencePayload,
} from "../../data/api/bpmnReferenceApi";
import { ConfirmModal } from "../ui/ConfirmModal";
import { Modal } from "../ui/Modal";
import { DS_GHOST_BTN } from "../ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  onError?: (message: string | null) => void;
};

function describeLoadError(err: unknown): string {
  return err instanceof Error && err.message ? err.message : "Falha ao carregar a referência BPMN.";
}

export function ProcessBpmnReferenceCard({ processoId, getAccessToken, onError }: Props) {
  const [loading, setLoading] = useState(true);
  const [payload, setPayload] = useState<ProcessBpmnReferencePayload | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [unlinkOpen, setUnlinkOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLocalError(null);
    try {
      setPayload(await fetchProcessBpmnReference(processoId, getAccessToken));
    } catch (err) {
      const message = describeLoadError(err);
      setLocalError(message);
      onError?.(message);
    } finally {
      setLoading(false);
    }
  }, [processoId, getAccessToken, onError]);

  useEffect(() => {
    let cancelled = false;
    void Promise.resolve().then(async () => {
      try {
        const next = await fetchProcessBpmnReference(processoId, getAccessToken);
        if (!cancelled) setPayload(next);
      } catch (err) {
        if (cancelled) return;
        const message = describeLoadError(err);
        setLocalError(message);
        onError?.(message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [processoId, getAccessToken, onError]);

  const reference = payload?.reference ?? null;
  const resolved = payload?.resolved ?? null;
  const newerAvailable =
    resolved?.state === "resolved" &&
    typeof resolved.latest_revision_number === "number" &&
    reference != null &&
    resolved.latest_revision_number > reference.revision_number;

  async function handleUnlink() {
    setBusy(true);
    try {
      setPayload(await removeProcessBpmnReference(processoId, getAccessToken));
      setUnlinkOpen(false);
    } catch (err) {
      setLocalError(describeLoadError(err));
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando referência BPMN…</p>;
  }

  return (
    <div className="tm-bpmn-reference-card" data-testid="bpmn-reference-card">
      {localError ? <p className="ds-hint">{localError}</p> : null}

      {!reference ? (
        <div>
          <p className="ds-hint">
            Nenhum modelo BPMN vinculado. Vincule uma revisão imutável do Modelador para referenciar
            o fluxo oficial deste processo.
          </p>
          <button type="button" className={DS_GHOST_BTN} onClick={() => setPickerOpen(true)}>
            <Link2 size={14} aria-hidden /> Vincular modelo BPMN
          </button>
        </div>
      ) : (
        <div>
          {resolved?.state === "resolved" ? (
            <p className="ds-hint">
              <strong>{resolved.model_display_name ?? reference.model_id}</strong>
              {" — revisão vinculada: "}
              <strong>R{reference.revision_number}</strong>
              {resolved.revision_name ? ` (${resolved.revision_name})` : ""}
              {resolved.model_archived ? " — modelo arquivado" : ""}
            </p>
          ) : resolved?.state === "unavailable" ? (
            <p className="ds-hint">
              Modelo BPMN temporariamente indisponível. Referência preservada: modelo{" "}
              <code>{reference.model_id}</code>, revisão R{reference.revision_number}.
            </p>
          ) : (
            <p className="ds-hint">
              Referência BPMN sem acesso ou não encontrada. Referência preservada: modelo{" "}
              <code>{reference.model_id}</code>, revisão R{reference.revision_number}.
            </p>
          )}

          {newerAvailable ? (
            <p className="ds-hint" data-testid="bpmn-newer-revision">
              Existe uma revisão BPMN mais recente (R{resolved?.latest_revision_number}). O vínculo
              permanece em R{reference.revision_number} até que você altere explicitamente.
            </p>
          ) : null}

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {resolved?.state === "resolved" ? (
              <a
                className={DS_GHOST_BTN}
                href={bpmnRevisionUrl(reference.model_id, reference.revision_number)}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Eye size={14} aria-hidden /> Visualizar revisão
              </a>
            ) : null}
            <a
              className={DS_GHOST_BTN}
              href={bpmnModelUrl(reference.model_id)}
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink size={14} aria-hidden /> Abrir no Modelador
            </a>
            {resolved?.state !== "unavailable" ? (
              <button
                type="button"
                className={DS_GHOST_BTN}
                onClick={() => setPickerOpen(true)}
              >
                <RefreshCw size={14} aria-hidden /> Alterar vínculo
              </button>
            ) : (
              <button
                type="button"
                className={DS_GHOST_BTN}
                onClick={() => {
                  setLoading(true);
                  void load();
                }}
              >
                <RefreshCw size={14} aria-hidden /> Tentar novamente
              </button>
            )}
            <button
              type="button"
              className={DS_GHOST_BTN}
              onClick={() => setUnlinkOpen(true)}
            >
              <Unlink size={14} aria-hidden /> Desvincular
            </button>
          </div>
        </div>
      )}

      {pickerOpen ? (
        <BpmnLinkPickerModal
          processoId={processoId}
          getAccessToken={getAccessToken}
          current={reference}
          onClose={() => setPickerOpen(false)}
          onLinked={(next) => {
            setPayload(next);
            setPickerOpen(false);
          }}
        />
      ) : null}

      <ConfirmModal
        open={unlinkOpen}
        title="Desvincular modelo BPMN"
        message="Desvincular não excluirá o modelo BPMN no Modelador — apenas remove a referência deste processo."
        confirmLabel="Desvincular"
        variant="danger"
        confirmBusy={busy}
        onConfirm={() => void handleUnlink()}
        onCancel={() => setUnlinkOpen(false)}
      />
    </div>
  );
}

type PickerProps = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  current: ProcessBpmnReferencePayload["reference"];
  onClose: () => void;
  onLinked: (payload: ProcessBpmnReferencePayload) => void;
};

function BpmnLinkPickerModal({
  processoId,
  getAccessToken,
  current,
  onClose,
  onLinked,
}: PickerProps) {
  const [models, setModels] = useState<BpmnModelCandidate[] | null>(null);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<BpmnModelCandidate | null>(null);
  const [revisions, setRevisions] = useState<BpmnRevisionCandidate[] | null>(null);
  const [revisionsError, setRevisionsError] = useState<string | null>(null);
  const [selectedRevision, setSelectedRevision] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchBpmnModelCandidates(processoId, getAccessToken)
      .then((result) => {
        if (!cancelled) setModels(result.items ?? []);
      })
      .catch((err) => {
        if (!cancelled) setModelsError(describeLoadError(err));
      });
    return () => {
      cancelled = true;
    };
  }, [processoId, getAccessToken]);

  function selectModel(model: BpmnModelCandidate) {
    setSelectedModel(model);
    setSelectedRevision(null);
    setRevisions(null);
    setRevisionsError(null);
    fetchBpmnModelRevisions(processoId, model.model_id, getAccessToken)
      .then((result) => setRevisions(result.items ?? []))
      .catch((err) => setRevisionsError(describeLoadError(err)));
  }

  const canConfirm =
    selectedModel != null &&
    selectedRevision != null &&
    !confirming;

  async function handleConfirm() {
    if (!selectedModel || selectedRevision == null) return;
    setConfirming(true);
    setError(null);
    try {
      const result = await setProcessBpmnReference(
        processoId,
        { model_id: selectedModel.model_id, revision_number: selectedRevision },
        getAccessToken
      );
      onLinked(result);
    } catch (err) {
      setError(describeLoadError(err));
    } finally {
      setConfirming(false);
    }
  }

  return (
    <Modal open title="Vincular modelo BPMN" onClose={onClose}>
      <div className="tm-bpmn-picker" data-testid="bpmn-picker">
        {current ? (
          <p className="ds-hint">
            Atual: modelo <code>{current.model_id}</code> / R{current.revision_number}
          </p>
        ) : null}

        {modelsError ? (
          <p className="ds-hint">{modelsError}</p>
        ) : models == null ? (
          <p className="ds-hint">Carregando seus modelos BPMN…</p>
        ) : models.length === 0 ? (
          <p className="ds-hint">
            Nenhum modelo BPMN disponível para o seu usuário. Crie o modelo no Modelador e volte para
            vincular.
          </p>
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 4 }}>
            {models.map((model) => {
              const noRevision = model.latest_revision_number == null;
              const active = selectedModel?.model_id === model.model_id;
              return (
                <li key={model.model_id}>
                  <button
                    type="button"
                    className={DS_GHOST_BTN}
                    disabled={noRevision}
                    aria-pressed={active}
                    onClick={() => selectModel(model)}
                  >
                    {model.display_name ?? model.model_id}
                    {model.archived ? " (arquivado)" : ""}
                    {noRevision ? " — sem revisão" : ""}
                  </button>
                  {noRevision ? (
                    <span className="ds-hint">
                      {" "}
                      Este modelo ainda não possui uma revisão.{" "}
                      <a href={bpmnModelUrl(model.model_id)} target="_blank" rel="noopener noreferrer">
                        Abrir no Modelador
                      </a>
                    </span>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}

        {selectedModel ? (
          <div>
            {revisionsError ? (
              <p className="ds-hint">{revisionsError}</p>
            ) : revisions == null ? (
              <p className="ds-hint">Carregando revisões…</p>
            ) : revisions.length === 0 ? (
              <p className="ds-hint">Este modelo ainda não possui uma revisão.</p>
            ) : (
              <fieldset>
                <legend className="ds-hint">Selecione a revisão imutável a vincular</legend>
                {revisions.map((rev) => (
                  <label key={rev.revision_number} style={{ display: "block" }}>
                    <input
                      type="radio"
                      name="bpmn-revision"
                      checked={selectedRevision === rev.revision_number}
                      onChange={() => setSelectedRevision(rev.revision_number)}
                    />{" "}
                    R{rev.revision_number}
                    {rev.name ? ` — ${rev.name}` : ""}
                    {rev.created_at ? ` — ${rev.created_at}` : ""}
                    {rev.revision_number === selectedModel.latest_revision_number
                      ? " (mais recente)"
                      : ""}
                  </label>
                ))}
              </fieldset>
            )}
          </div>
        ) : null}

        {error ? <p className="ds-hint">{error}</p> : null}

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button type="button" className={DS_GHOST_BTN} onClick={onClose}>
            Cancelar
          </button>
          <button
            type="button"
            className={DS_GHOST_BTN}
            disabled={!canConfirm}
            onClick={() => void handleConfirm()}
          >
            {confirming ? "Vinculando…" : "Confirmar vínculo"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
