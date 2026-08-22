import { useEffect, useState } from "react";
import { ActionButton } from "@delpi/plugin-ui/index";
import { Pencil } from "lucide-react";

import { updateReport, type ReportDetail } from "../api/travelExpensesApi";
import { PIX_KEY_TYPES, formatPixKeyDisplay } from "../constants/pixKeyTypes";
import { helpTooltips } from "../content/helpTooltips";
import { TravelFormActions, TravelFormGrid, TravelSectionCard } from "../ui/travelUi";

type Props = {
  report: ReportDetail;
  editable: boolean;
  onChanged: () => Promise<void>;
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
};

export function TravelPixSection({ report, editable, onChanged, onError, onSuccess }: Props) {
  const saved = formatPixKeyDisplay(report.pixKeyType, report.pixKeyValue);
  const [editing, setEditing] = useState(!saved);
  const [keyType, setKeyType] = useState(report.pixKeyType || "cpf");
  const [keyValue, setKeyValue] = useState(report.pixKeyValue || "");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setKeyType(report.pixKeyType || "cpf");
    setKeyValue(report.pixKeyValue || "");
    setEditing(!formatPixKeyDisplay(report.pixKeyType, report.pixKeyValue));
  }, [report.pixKeyType, report.pixKeyValue, report.id]);

  const showForm = editable && (!saved || editing);

  function cancelEdit() {
    setKeyType(report.pixKeyType || "cpf");
    setKeyValue(report.pixKeyValue || "");
    setEditing(false);
  }

  async function onSave() {
    if (!editable) return;
    setBusy(true);
    try {
      await updateReport(report.id, {
        pixKeyType: keyType,
        pixKeyValue: keyValue.trim(),
      });
      await onChanged();
      setEditing(false);
      onSuccess(saved ? "PIX atualizado." : "PIX para ressarcimento salvo.");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Não foi possível salvar o PIX.");
    } finally {
      setBusy(false);
    }
  }

  async function onClear() {
    if (!editable || !saved) return;
    if (!window.confirm("Remover a chave PIX para ressarcimento?")) return;
    setBusy(true);
    try {
      await updateReport(report.id, { pixKeyType: null, pixKeyValue: null });
      await onChanged();
      setKeyType("cpf");
      setKeyValue("");
      setEditing(true);
      onSuccess("PIX removido.");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Não foi possível remover o PIX.");
    } finally {
      setBusy(false);
    }
  }

  const sectionActions =
    editable && saved && !editing ? (
      <button
        type="button"
        className="te-section-edit-btn"
        onClick={() => setEditing(true)}
        aria-label="Editar chave PIX"
      >
        <Pencil size={16} aria-hidden />
      </button>
    ) : null;

  return (
    <TravelSectionCard
      title="PIX para ressarcimento"
      hint={helpTooltips.pix}
      actions={sectionActions}
    >
      {showForm ? (
        <>
          {!saved ? (
            <p className="te-muted">Informe o tipo e a chave PIX para o ressarcimento.</p>
          ) : null}
          <TravelFormGrid className="te-pix-form">
            <label className="te-field">
              Tipo da chave
              <select
                value={keyType}
                onChange={(event) => setKeyType(event.target.value)}
                disabled={busy}
              >
                {PIX_KEY_TYPES.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="te-field">
              Chave PIX
              <input
                value={keyValue}
                onChange={(event) => setKeyValue(event.target.value)}
                disabled={busy}
                placeholder="Digite a chave para ressarcimento"
              />
            </label>
          </TravelFormGrid>
          <TravelFormActions>
            {saved ? (
              <ActionButton variant="ghost" onClick={cancelEdit} disabled={busy}>
                Cancelar
              </ActionButton>
            ) : null}
            {saved ? (
              <ActionButton variant="ghost" onClick={() => void onClear()} disabled={busy}>
                Remover
              </ActionButton>
            ) : null}
            <ActionButton variant="primary" onClick={() => void onSave()} disabled={busy}>
              Salvar PIX
            </ActionButton>
          </TravelFormActions>
        </>
      ) : saved ? (
        <div className="te-pix-display">
          <p className="te-pix-display__row">
            <span>Tipo</span>
            <strong>{saved.label}</strong>
          </p>
          <p className="te-pix-display__row">
            <span>Chave</span>
            <strong>{saved.value}</strong>
          </p>
        </div>
      ) : (
        <p className="te-muted">Nenhuma chave PIX informada.</p>
      )}
    </TravelSectionCard>
  );
}
