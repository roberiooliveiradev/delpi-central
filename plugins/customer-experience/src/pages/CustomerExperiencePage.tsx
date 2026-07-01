import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Copy,
  MessageSquare,
  QrCode,
  Search,
  UserPlus,
  Users,
} from "lucide-react";
import {
  createParticipant,
  deactivateParticipant,
  downloadFeedbackQr,
  downloadQr,
  listParticipants,
} from "../api/participantsApi";
import type { Participant } from "../types";

const EMPTY_FORM = {
  fullName: "",
  companyName: "",
  visitDate: new Date().toISOString().slice(0, 10),
  participantInfo: "",
  thankYouMessage: "",
};

export function CustomerExperiencePage() {
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [photo, setPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadParticipants = useCallback(async (company?: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await listParticipants({ company, limit: 100 });
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

  const onPhotoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setPhoto(file);
    setPhotoPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return file ? URL.createObjectURL(file) : null;
    });
  };

  const resetForm = () => {
    setForm({ ...EMPTY_FORM, visitDate: new Date().toISOString().slice(0, 10) });
    setPhoto(null);
    setPhotoPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!photo) {
      setError("Selecione uma foto do participante.");
      return;
    }
    setSaving(true);
    try {
      await createParticipant({
        fullName: form.fullName,
        companyName: form.companyName,
        visitDate: form.visitDate,
        participantInfo: form.participantInfo || undefined,
        thankYouMessage: form.thankYouMessage || undefined,
        photo,
      });
      setFeedback("Participante cadastrado e QR code gerado.");
      resetForm();
      await loadParticipants();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cadastrar participante.");
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

  const handleDownloadFeedbackQr = async (participant: Participant) => {
    try {
      const blob = await downloadFeedbackQr(participant.id);
      triggerDownload(blob, `qr-feedback-${slug(participant)}.png`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao baixar QR de feedback.");
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

  const handleCopyFeedbackLink = async (participant: Participant) => {
    if (!participant.feedbackPublicUrl) return;
    try {
      await navigator.clipboard.writeText(participant.feedbackPublicUrl);
      setFeedback("Link de feedback copiado.");
    } catch {
      setFeedback(participant.feedbackPublicUrl);
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

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return participants;
    return participants.filter(
      (p) =>
        p.fullName.toLowerCase().includes(term) ||
        p.companyName.toLowerCase().includes(term),
    );
  }, [participants, search]);

  return (
    <div className="cx-page">
      <header className="cx-header">
        <div className="cx-header__icon" aria-hidden="true">
          <QrCode size={28} strokeWidth={1.75} />
        </div>
        <div>
          <h1 className="cx-header__title">Experiência do Cliente</h1>
          <p className="cx-header__subtitle">
            Cadastre visitantes de empresas clientes e gere o QR code de agradecimento.
          </p>
        </div>
      </header>

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

      <div className="cx-layout">
        <section className="cx-card cx-form-card">
          <h2 className="cx-card__title">
            <UserPlus size={18} /> Novo participante
          </h2>
          <form className="cx-form" onSubmit={handleSubmit}>
            <label className="cx-field">
              <span>Nome completo</span>
              <input
                type="text"
                required
                value={form.fullName}
                onChange={(e) => setForm({ ...form, fullName: e.target.value })}
                placeholder="Nome do visitante"
              />
            </label>

            <label className="cx-field">
              <span>Empresa</span>
              <input
                type="text"
                required
                value={form.companyName}
                onChange={(e) => setForm({ ...form, companyName: e.target.value })}
                placeholder="Empresa do visitante"
              />
            </label>

            <label className="cx-field">
              <span>Data da visita</span>
              <input
                type="date"
                required
                value={form.visitDate}
                onChange={(e) => setForm({ ...form, visitDate: e.target.value })}
              />
            </label>

            <label className="cx-field">
              <span>Informações do participante</span>
              <input
                type="text"
                value={form.participantInfo}
                onChange={(e) => setForm({ ...form, participantInfo: e.target.value })}
                placeholder="Cargo, área ou observação (opcional)"
              />
            </label>

            <label className="cx-field">
              <span>Mensagem de agradecimento (opcional)</span>
              <textarea
                rows={3}
                value={form.thankYouMessage}
                onChange={(e) => setForm({ ...form, thankYouMessage: e.target.value })}
                placeholder="Se vazio, usamos a mensagem padrão da Delpi."
              />
            </label>

            <label className="cx-field">
              <span>Foto do participante</span>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={onPhotoChange}
              />
            </label>

            {photoPreview && (
              <img className="cx-photo-preview" src={photoPreview} alt="Prévia da foto" />
            )}

            <button className="cx-button cx-button--primary" type="submit" disabled={saving}>
              {saving ? "Cadastrando..." : "Cadastrar e gerar QR"}
            </button>
          </form>
        </section>

        <section className="cx-card cx-list-card">
          <div className="cx-list-card__head">
            <h2 className="cx-card__title">
              <Users size={18} /> Participantes
              <span className="cx-count">{total}</span>
            </h2>
            <div className="cx-search">
              <Search size={16} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por nome ou empresa"
              />
            </div>
          </div>

          {loading ? (
            <p className="cx-state">Carregando participantes...</p>
          ) : filtered.length === 0 ? (
            <p className="cx-state">Nenhum participante cadastrado ainda.</p>
          ) : (
            <ul className="cx-participant-list">
              {filtered.map((participant) => (
                <li key={participant.id} className="cx-participant">
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
                      onClick={() => handleCopyLink(participant)}
                      title="Copiar link de agradecimento"
                    >
                      <Copy size={16} /> Link
                    </button>
                    <button
                      className="cx-button cx-button--ghost"
                      type="button"
                      onClick={() => handleDownloadFeedbackQr(participant)}
                      title="Baixar QR do formulário de feedback"
                    >
                      <MessageSquare size={16} /> QR feedback
                    </button>
                    <button
                      className="cx-button cx-button--ghost"
                      type="button"
                      onClick={() => handleCopyFeedbackLink(participant)}
                      title="Copiar link do formulário de feedback"
                    >
                      <Copy size={16} /> Link
                    </button>
                    {participant.isActive && (
                      <button
                        className="cx-button cx-button--danger-ghost"
                        type="button"
                        onClick={() => handleDeactivate(participant)}
                        title="Desativar link público"
                      >
                        Desativar
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
