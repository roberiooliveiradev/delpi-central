import { useEffect, useState } from "react";
import {
  createStrategicIndicatorsChangeRequest,
  fetchStrategicIndicatorsChangeRequests,
} from "../../data/api/strategicIndicatorsSettingsAuditApi";
import type { StrategicIndicatorsChangeRequest } from "../../data/types/settingsAudit";
import {
  getAuditEntityKeyLabel,
  getChangeRequestStatusLabel,
} from "../presentation/labels";
import "./ChangeRequestsWorkspacePanel.css";
import { SiSelectControl } from "./siFiltersUi";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";

type ChangeRequestsWorkspacePanelProps = {
  getAccessToken?: () => string | undefined;
};

export function ChangeRequestsWorkspacePanel({
  getAccessToken,
}: ChangeRequestsWorkspacePanelProps) {
  const [items, setItems] = useState<StrategicIndicatorsChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [targetBlock, setTargetBlock] = useState("parameters.global");
  const [payloadText, setPayloadText] = useState('{"items": []}');
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetchStrategicIndicatorsChangeRequests(getAccessToken);
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar solicitações.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleCreate() {
    setSaving(true);
    setError(null);

    try {
      await createStrategicIndicatorsChangeRequest(
        {
          title,
          description,
          target_block: targetBlock,
          proposed_payload: JSON.parse(payloadText),
        },
        getAccessToken,
      );

      setTitle("");
      setDescription("");
      setPayloadText('{"items": []}');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar solicitação.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="si-change-requests">
      <div className="si-change-requests__grid">
        <div className="si-change-requests__panel">
          <h3 className="si-change-requests__title">Nova solicitação</h3>

          {error ? <div className="si-change-requests__error">{error}</div> : null}

          <label className="si-change-requests__field">
            <span>Título</span>
            <SiNativeTextControl value={title} onChange={setTitle} />
          </label>

          <label className="si-change-requests__field">
            <span>Descrição</span>
            <SiNativeTextAreaControl
              value={description}
              aria-label="Descrição"
              onChange={setDescription}
            />
          </label>

          <label className="si-change-requests__field">
            <span>Bloco alvo</span>
            <SiSelectControl
              value={targetBlock}
              onChange={setTargetBlock}
              options={[
                {
                  value: "weights.departments",
                  label: getAuditEntityKeyLabel("weights.departments"),
                },
                {
                  value: "goals.summary",
                  label: getAuditEntityKeyLabel("goals.summary"),
                },
                {
                  value: "parameters.global",
                  label: getAuditEntityKeyLabel("parameters.global"),
                },
                {
                  value: "governance.notes",
                  label: getAuditEntityKeyLabel("governance.notes"),
                },
              ]}
            />
          </label>

          <label className="si-change-requests__field">
            <span>Payload proposto</span>
            <SiNativeTextAreaControl
              value={payloadText}
              spellCheck={false}
              aria-label="Payload proposto"
              onChange={setPayloadText}
            />
          </label>

          <button
            type="button"
            className="si-change-requests__button"
            onClick={() => void handleCreate()}
            disabled={saving}
          >
            {saving ? "Criando..." : "Criar solicitação"}
          </button>
        </div>

        <div className="si-change-requests__panel">
          <h3 className="si-change-requests__title">Fila administrativa</h3>

          {loading ? (
            <div>Carregando solicitações...</div>
          ) : !items.length ? (
            <div>Nenhuma solicitação criada ainda.</div>
          ) : (
            <div className="si-change-requests__list">
              {items.map((item) => (
                <article key={item.id} className="si-change-requests__card">
                  <div className="si-change-requests__card-top">
                    <strong>{item.request_code}</strong>
                    <span>{getChangeRequestStatusLabel(item.status)}</span>
                  </div>
                  <div className="si-change-requests__card-title">{item.title}</div>
                  <div className="si-change-requests__card-meta">
                    <span>Bloco: {getAuditEntityKeyLabel(item.target_block)}</span>
                    <span>Criado em: {new Date(item.created_at).toLocaleString("pt-BR")}</span>
                  </div>
                  <p className="si-change-requests__card-description">
                    {item.description}
                  </p>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}