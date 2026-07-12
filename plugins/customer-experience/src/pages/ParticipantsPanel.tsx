import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Copy,
  FilterX,
  Pencil,
  Power,
  Printer,
  QrCode,
  Search,
  Trash2,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  activateParticipant,
  createParticipant,
  deactivateParticipant,
  deleteParticipant,
  downloadQr,
  listParticipants,
  updateParticipant,
} from "../api/participantsApi";
import { CompanyField } from "../components/CompanyField";
import { CompanyMultiSelect } from "../components/CompanyMultiSelect";
import { PhotoDropzone } from "../components/PhotoDropzone";
import { CxNativeTextAreaField, CxNativeTextField } from "../components/cxFormFields";
import { printQrLabel } from "../utils/qrLabelPrint";
import { useCxPermissions } from "../context/CxPermissionsContext";
import type { Participant } from "../types";

const EMPTY_FORM = {
  fullName: "",
  companyName: "",
  visitDate: new Date().toISOString().slice(0, 10),
  participantInfo: "",
  thankYouMessage: "",
};

export function ParticipantsPanel() {
  const { canWriteParticipants, canManageParticipants } = useCxPermissions();
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [nameFilter, setNameFilter] = useState("");
  const [companyFilter, setCompanyFilter] = useState<string[]>([]);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingPhotoUrl, setEditingPhotoUrl] = useState<string | null>(null);
  const [formCollapsed, setFormCollapsed] = useState(false);
  const formCardRef = useRef<HTMLElement>(null);

  const loadParticipants = useCallback(async (company?: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await listParticipants({ company, limit: 200 });
      setParticipants(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar participantes.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadParticipants();
  }, [loadParticipants]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => setFeedback(null), 4000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  const handleSelectPhoto = (file: File) => {
    setPhoto(file);
    setPhotoPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return URL.createObjectURL(file);
    });
  };

  const clearPhoto = () => {
    setPhoto(null);
    setPhotoPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
  };

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, visitDate: new Date().toISOString().slice(0, 10) });
    clearPhoto();
    setEditingId(null);
    setEditingPhotoUrl(null);
  };

  const openNewForm = () => {
    resetForm();
    setError(null);
    setFormCollapsed(false);
    formCardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const startEdit = (participant: Participant) => {
    setEditingId(participant.id);
    setEditingPhotoUrl(participant.photoUrl);
    setFormCollapsed(false);
    setError(null);
    setForm({
      fullName: participant.fullName,
      companyName: participant.companyName,
      visitDate: participant.visitDate,
      participantInfo: participant.participantInfo ?? "",
      thankYouMessage: participant.thankYouMessage ?? "",
    });
    clearPhoto();
    formCardRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!editingId && !photo) {
      setError("Selecione uma foto do participante.");
      return;
    }
    setSaving(true);
    try {
      if (editingId) {
        await updateParticipant(editingId, {
          fullName: form.fullName,
          companyName: form.companyName,
          visitDate: form.visitDate,
          participantInfo: form.participantInfo || undefined,
          thankYouMessage: form.thankYouMessage || undefined,
          photo: photo ?? undefined,
        });
        setFeedback("Participante atualizado.");
      } else {
        await createParticipant({
          fullName: form.fullName,
          companyName: form.companyName,
          visitDate: form.visitDate,
          participantInfo: form.participantInfo || undefined,
          thankYouMessage: form.thankYouMessage || undefined,
          photo: photo as File,
        });
        setFeedback("Participante cadastrado e QR code gerado.");
      }
      resetForm();
      await loadParticipants();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar participante.");
    } finally {
      setSaving(false);
    }
  };

  const triggerDownload = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  };

  const slug = (participant: Participant) =>
    participant.fullName.replace(/\s+/g, "-").toLowerCase();

  const handleDownloadQr = async (participant: Participant) => {
    try {
      const blob = await downloadQr(participant.id);
      triggerDownload(blob, `qr-agradecimento-${slug(participant)}.png`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao baixar QR code.");
    }
  };

  const handlePrintLabel = async (participant: Participant) => {
    try {
      const blob = await downloadQr(participant.id);
      const result = await printQrLabel(participant, blob);
      if (!result.success) {
        setError(result.error ?? "Não foi possível imprimir a etiqueta.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar a etiqueta.");
    }
  };

  const handleCopyLink = async (participant: Participant) => {
    if (!participant.publicUrl) return;
    try {
      await navigator.clipboard.writeText(participant.publicUrl);
      setFeedback("Link de agradecimento copiado.");
    } catch {
      setFeedback(participant.publicUrl);
    }
  };

  const handleDeactivate = async (participant: Participant) => {
    try {
      await deactivateParticipant(participant.id);
      setFeedback("Link público desativado.");
      await loadParticipants();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao desativar link.");
    }
  };

  const handleActivate = async (participant: Participant) => {
    try {
      await activateParticipant(participant.id);
      setFeedback("Link público reativado.");
      await loadParticipants();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao reativar link.");
    }
  };

  const handleDelete = async (participant: Participant) => {
    const confirmed = window.confirm(
      `Excluir definitivamente "${participant.fullName}"? Foto e QR code serão removidos.`,
    );
    if (!confirmed) return;
    try {
      await deleteParticipant(participant.id);
      if (editingId === participant.id) resetForm();
      setFeedback("Participante excluído.");
      await loadParticipants();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir participante.");
    }
  };

  const companyOptions = useMemo(() => {
    const names = new Set<string>();
    for (const p of participants) {
      const name = p.companyName.trim();
      if (name) names.add(name);
    }
    return [...names].sort((a, b) => a.localeCompare(b, "pt-BR"));
  }, [participants]);

  const hasActiveFilters =
    nameFilter.trim() !== "" ||
    companyFilter.length > 0 ||
    dateFrom !== "" ||
    dateTo !== "";

  const clearFilters = () => {
    setNameFilter("");
    setCompanyFilter([]);
    setDateFrom("");
    setDateTo("");
  };

  const filtered = useMemo(() => {
    const term = nameFilter.trim().toLowerCase();
    const companySet = new Set(companyFilter);
    return participants.filter((p) => {
      if (term && !p.fullName.toLowerCase().includes(term)) return false;
      if (companySet.size > 0 && !companySet.has(p.companyName.trim())) return false;
      if (dateFrom && p.visitDate < dateFrom) return false;
      if (dateTo && p.visitDate > dateTo) return false;
      return true;
    });
  }, [participants, nameFilter, companyFilter, dateFrom, dateTo]);

  return (
    <>
      {feedback && (
        <div className="cx-banner cx-banner--success" role="status">
          <CheckCircle2 size={18} /> {feedback}
        </div>
      )}
      {error && (
        <div className="cx-banner cx-banner--error" role="alert">
          {error}
        </div>
      )}

      <div
        className={`cx-layout${
          !canWriteParticipants ? " cx-layout--list-only" : formCollapsed ? " cx-layout--form-collapsed" : ""
        }`}
      >
        {canWriteParticipants && (
        <section
          className={`cx-card cx-form-card${formCollapsed ? " cx-form-card--collapsed" : ""}`}
          ref={formCardRef}
        >
          {formCollapsed ? (
            <button
              type="button"
              className="cx-form-card__rail"
              title="Expandir formulário"
              onClick={() => setFormCollapsed(false)}
            >
              <ChevronRight size={18} className="cx-form-card__caret" />
              <span className="cx-card__title">
                {editingId ? <Pencil size={18} /> : <UserPlus size={18} />}
                <span className="cx-form-card__title-text">
                  {editingId ? "Editar participante" : "Novo participante"}
                </span>
              </span>
            </button>
          ) : (
          <>
          <div className="cx-form-card__header">
            <h2 className="cx-card__title">
              {editingId ? <Pencil size={18} /> : <UserPlus size={18} />}
              {editingId ? "Editar participante" : "Novo participante"}
            </h2>
            <button
              type="button"
              className="cx-button cx-button--ghost"
              onClick={() => setFormCollapsed(true)}
              title="Fechar formulário"
            >
              <X size={16} /> Fechar
            </button>
          </div>
          <form className="cx-form" onSubmit={handleSubmit}>
            <CxNativeTextField
              id="cx-participant-full-name"
              label="Nome completo"
              required
              value={form.fullName}
              onChange={(fullName) => setForm({ ...form, fullName })}
              placeholder="Nome do visitante"
            />

            <CompanyField
              value={form.companyName}
              onChange={(companyName) => setForm({ ...form, companyName })}
            />

            <CxNativeTextField
              id="cx-participant-visit-date"
              label="Data da visita"
              type="date"
              required
              value={form.visitDate}
              onChange={(visitDate) => setForm({ ...form, visitDate })}
            />

            <CxNativeTextField
              id="cx-participant-info"
              label="Informações do participante"
              value={form.participantInfo}
              onChange={(participantInfo) => setForm({ ...form, participantInfo })}
              placeholder="Cargo, área ou observação (opcional)"
            />

            <CxNativeTextAreaField
              id="cx-participant-thank-you"
              label="Mensagem de agradecimento (opcional)"
              rows={3}
              value={form.thankYouMessage}
              onChange={(thankYouMessage) => setForm({ ...form, thankYouMessage })}
              placeholder="Se vazio, usamos a mensagem padrão da Delpi."
            />

            <div className="cx-field">
              <span>
                Foto do participante
                {editingId && " (opcional — deixe vazio para manter a atual)"}
              </span>
              <PhotoDropzone
                previewUrl={photoPreview ?? editingPhotoUrl}
                fileName={photo?.name ?? null}
                isExisting={!photoPreview && !!editingPhotoUrl}
                onSelect={handleSelectPhoto}
                onClear={clearPhoto}
              />
            </div>

            <div className="cx-form__actions">
              <button className="cx-button cx-button--primary" type="submit" disabled={saving}>
                {saving
                  ? "Salvando..."
                  : editingId
                    ? "Salvar alterações"
                    : "Cadastrar e gerar QR"}
              </button>
              {editingId && (
                <button
                  className="cx-button cx-button--ghost"
                  type="button"
                  onClick={resetForm}
                  disabled={saving}
                >
                  <X size={16} /> Cancelar
                </button>
              )}
            </div>
          </form>
          </>
          )}
        </section>
        )}

        <section className="cx-card cx-list-card">
          <div className="cx-list-card__head">
            <h2 className="cx-card__title">
              <Users size={18} /> Participantes
              <span className="cx-count">
                {hasActiveFilters ? `${filtered.length}/${total}` : total}
              </span>
            </h2>
            {canWriteParticipants && (
              <button
                className="cx-button cx-button--primary"
                type="button"
                onClick={openNewForm}
              >
                <UserPlus size={16} /> Novo participante
              </button>
            )}
          </div>

          <div className="cx-filters">
            <div className="cx-search">
              <Search size={16} />
              <NativeTextControl
                type="text"
                value={nameFilter}
                onChange={setNameFilter}
                placeholder="Buscar por nome"
              />
            </div>
            <CompanyMultiSelect
              options={companyOptions}
              selected={companyFilter}
              onChange={setCompanyFilter}
            />
            <label className="cx-date-filter">
              <CalendarDays size={15} />
              <span>De</span>
              <NativeTextControl
                type="date"
                value={dateFrom}
                max={dateTo || undefined}
                onChange={setDateFrom}
              />
            </label>
            <label className="cx-date-filter">
              <CalendarDays size={15} />
              <span>Até</span>
              <NativeTextControl
                type="date"
                value={dateTo}
                min={dateFrom || undefined}
                onChange={setDateTo}
              />
            </label>
            {hasActiveFilters && (
              <button
                className="cx-button cx-button--ghost cx-filters__clear"
                type="button"
                onClick={clearFilters}
              >
                <FilterX size={15} /> Limpar filtros
              </button>
            )}
          </div>

          {loading ? (
            <p className="cx-state">Carregando participantes...</p>
          ) : participants.length === 0 ? (
            <p className="cx-state">Nenhum participante cadastrado ainda.</p>
          ) : filtered.length === 0 ? (
            <p className="cx-state">Nenhum participante corresponde aos filtros.</p>
          ) : (
            <ul className="cx-participant-list">
              {filtered.map((participant) => (
                <li key={participant.id} className="cx-participant">
                  <div className="cx-participant__main">
                    <img
                      className="cx-participant__photo"
                      src={participant.photoUrl}
                      alt={participant.fullName}
                      loading="lazy"
                    />
                    <div className="cx-participant__info">
                      <strong>{participant.fullName}</strong>
                      <span>{participant.companyName}</span>
                      <span className="cx-participant__meta">
                        {participant.visitDate}
                        {" · "}
                        {participant.viewCount} acesso(s)
                        {!participant.isActive && " · link inativo"}
                      </span>
                    </div>
                    <span
                      className={`cx-chip ${
                        participant.isActive ? "cx-chip--on" : "cx-chip--off"
                      }`}
                    >
                      {participant.isActive ? "Ativo" : "Inativo"}
                    </span>
                  </div>
                  <div className="cx-participant__actions">
                    <button
                      className="cx-button cx-button--ghost"
                      type="button"
                      onClick={() => handleDownloadQr(participant)}
                      title="Baixar QR de agradecimento"
                    >
                      <QrCode size={16} /> QR agradecimento
                    </button>
                    <button
                      className="cx-button cx-button--ghost"
                      type="button"
                      onClick={() => handlePrintLabel(participant)}
                      title="Imprimir etiqueta para o chicote (frente e verso)"
                    >
                      <Printer size={16} /> Imprimir etiqueta
                    </button>
                    <button
                      className="cx-button cx-button--ghost"
                      type="button"
                      onClick={() => handleCopyLink(participant)}
                      title="Copiar link de agradecimento"
                    >
                      <Copy size={16} /> Link
                    </button>
                    {canWriteParticipants && (
                      <button
                        className="cx-button cx-button--ghost"
                        type="button"
                        onClick={() => startEdit(participant)}
                        title="Editar participante"
                      >
                        <Pencil size={16} /> Editar
                      </button>
                    )}
                    {canManageParticipants &&
                      (participant.isActive ? (
                        <button
                          className="cx-button cx-button--danger-ghost"
                          type="button"
                          onClick={() => handleDeactivate(participant)}
                          title="Desativar link público"
                        >
                          <Power size={16} /> Desativar
                        </button>
                      ) : (
                        <button
                          className="cx-button cx-button--ghost"
                          type="button"
                          onClick={() => handleActivate(participant)}
                          title="Reativar link público"
                        >
                          <Power size={16} /> Ativar
                        </button>
                      ))}
                    {canManageParticipants && (
                      <button
                        className="cx-button cx-button--danger-ghost"
                        type="button"
                        onClick={() => handleDelete(participant)}
                        title="Excluir participante"
                      >
                        <Trash2 size={16} /> Excluir
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
