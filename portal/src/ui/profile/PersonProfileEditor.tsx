import { useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from "react";
import { Camera, Maximize2, Trash2, X } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient, HttpError } from "../../data/apiClient";
import {
  CoreApi,
  type PersonProfileResponse,
} from "../../data/coreApi";
import { HelpTooltip } from "../../components/HelpTooltip";
import {
  notifyPersonProfileChanged,
  notifyPersonProfilePhotoChanged,
} from "./personProfilePhotoEvents";
import {
  resolveWhatsappE164,
  resolveWhatsappSource,
  type WhatsappSource,
} from "./personProfileWhatsapp";

const PERSON_PROFILE_HINTS = {
  photo:
    "Clique na foto para ampliar. No modal, use Trocar foto para enviar outra. Sem foto, clique para adicionar. JPEG, PNG, WebP ou GIF até 2 MB.",
  jobTitle:
    "Cargo informado por você no portal. Não sincroniza com RH ou Keycloak nesta fase.",
  contacts:
    "Telefone e celular no formato internacional (+55…). Marque qual número também é WhatsApp.",
};

type PersonProfileEditorProps = {
  userName?: string;
};

export function PersonProfileEditor({ userName }: PersonProfileEditorProps) {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const fileInputId = useId();
  const lightboxTitleId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        }),
      ),
    [getAccessToken, refreshToken],
  );

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [photoBusy, setPhotoBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [profile, setProfile] = useState<PersonProfileResponse | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const [jobTitle, setJobTitle] = useState("");
  const [phoneE164, setPhoneE164] = useState("");
  const [mobileE164, setMobileE164] = useState("");
  const [whatsappSource, setWhatsappSource] = useState<WhatsappSource>(null);

  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const previewRef = useRef<string | null>(null);

  const revokePreview = useCallback(() => {
    if (previewRef.current) {
      URL.revokeObjectURL(previewRef.current);
      previewRef.current = null;
    }
    setPreviewUrl(null);
  }, []);

  const applyProfile = useCallback(
    async (data: PersonProfileResponse) => {
      setProfile(data);
      setJobTitle((data.job_title || "").trim());
      setPhoneE164((data.phone_e164 || "").trim());
      setMobileE164((data.mobile_e164 || "").trim());
      setWhatsappSource(resolveWhatsappSource(data));
      revokePreview();
      if (data.has_photo) {
        try {
          const blob = await coreApi.getMyPersonProfilePhotoBlob();
          const url = URL.createObjectURL(blob);
          previewRef.current = url;
          setPreviewUrl(url);
        } catch {
          setPreviewUrl(null);
        }
      } else {
        setLightboxOpen(false);
      }
    },
    [coreApi, revokePreview],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await coreApi.getMyPersonProfile();
      await applyProfile(data);
    } catch (err) {
      const message =
        err instanceof HttpError ? err.message : "Não foi possível carregar o perfil.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [applyProfile, coreApi]);

  useEffect(() => {
    void load();
    return () => revokePreview();
  }, [load, revokePreview]);

  useEffect(() => {
    if (whatsappSource === "phone" && !phoneE164.trim()) {
      setWhatsappSource(null);
    }
  }, [phoneE164, whatsappSource]);

  useEffect(() => {
    if (whatsappSource === "mobile" && !mobileE164.trim()) {
      setWhatsappSource(null);
    }
  }, [mobileE164, whatsappSource]);

  useEffect(() => {
    if (!lightboxOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setLightboxOpen(false);
    };
    window.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [lightboxOpen]);

  const initials = useMemo(() => {
    if (!userName) return "?";
    const parts = userName.trim().split(/\s+/).filter(Boolean);
    const first = parts[0]?.[0] ?? "";
    const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
    return (first + last).toUpperCase() || "?";
  }, [userName]);

  const onSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await coreApi.patchMyPersonProfile({
        job_title: jobTitle.trim() || null,
        phone_e164: phoneE164.trim() || null,
        mobile_e164: mobileE164.trim() || null,
        whatsapp_e164: resolveWhatsappE164(whatsappSource, phoneE164, mobileE164),
      });
      await applyProfile(data);
      notifyPersonProfileChanged();
      setSuccess("Cargo e contatos salvos.");
    } catch (err) {
      const message =
        err instanceof HttpError ? err.message : "Não foi possível salvar o perfil.";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const onPickPhoto = () => {
    fileInputRef.current?.click();
  };

  const onPhotoSelected = async (file: File | null) => {
    if (!file) return;
    setPhotoBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await coreApi.uploadMyPersonProfilePhoto(file);
      await applyProfile(data);
      setSuccess("Foto atualizada.");
      notifyPersonProfilePhotoChanged();
    } catch (err) {
      const message =
        err instanceof HttpError ? err.message : "Não foi possível enviar a foto.";
      setError(message);
    } finally {
      setPhotoBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const onRemovePhoto = async () => {
    setPhotoBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const data = await coreApi.deleteMyPersonProfilePhoto();
      await applyProfile(data);
      setSuccess("Foto removida.");
      notifyPersonProfilePhotoChanged();
    } catch (err) {
      const message =
        err instanceof HttpError ? err.message : "Não foi possível remover a foto.";
      setError(message);
    } finally {
      setPhotoBusy(false);
    }
  };

  if (loading) {
    return <p className="profile-person__state">Carregando foto, cargo e contatos…</p>;
  }

  const hasPhoto = Boolean(profile?.has_photo && previewUrl);

  return (
    <div className="profile-person" data-tour="profile-person">
      {error ? (
        <div className="profile-person__banner profile-person__banner--error" role="alert">
          {error}
          <button type="button" className="profile-person__link-btn" onClick={() => void load()}>
            Tentar novamente
          </button>
        </div>
      ) : null}
      {success ? (
        <div className="profile-person__banner profile-person__banner--ok" role="status">
          {success}
        </div>
      ) : null}

      <div className="profile-person__photo-block" data-tour="profile-person-photo">
        <div className="profile-person__label-row profile-person__photo-heading">
          <span className="profile-person__section-label">Foto do perfil</span>
          <HelpTooltip content={PERSON_PROFILE_HINTS.photo} />
        </div>

        <div className="profile-person__photo-stack">
          <div className="profile-person__avatar-wrap">
            <button
              type="button"
              className={
                hasPhoto
                  ? "profile-person__avatar profile-person__avatar--expandable"
                  : "profile-person__avatar"
              }
              onClick={() => {
                if (hasPhoto) {
                  setLightboxOpen(true);
                  return;
                }
                onPickPhoto();
              }}
              disabled={photoBusy}
              aria-label={
                hasPhoto ? "Ampliar foto do perfil" : "Adicionar foto do perfil"
              }
            >
              {hasPhoto ? (
                <img
                  src={previewUrl!}
                  alt=""
                  className="profile-person__avatar-img"
                />
              ) : (
                <span className="profile-person__avatar-initials">{initials}</span>
              )}
              {hasPhoto ? (
                <span className="profile-person__expand-badge" aria-hidden="true">
                  <Maximize2 size={14} strokeWidth={2.25} />
                </span>
              ) : (
                <span className="profile-person__avatar-overlay" aria-hidden="true">
                  <Camera size={22} strokeWidth={1.75} />
                  <span>Adicionar</span>
                </span>
              )}
            </button>
          </div>

          {hasPhoto ? (
            <button
              type="button"
              className="profile-person__btn profile-person__btn--danger profile-person__btn--remove"
              onClick={() => void onRemovePhoto()}
              disabled={photoBusy}
            >
              <Trash2 size={15} aria-hidden="true" />
              Remover imagem
            </button>
          ) : (
            <p className="profile-person__photo-hint">Clique na área da foto para enviar</p>
          )}
        </div>

        <input
          id={fileInputId}
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          className="profile-person__file"
          onChange={(e) => void onPhotoSelected(e.target.files?.[0] ?? null)}
        />
      </div>

      <div className="profile-person__fields" data-tour="profile-person-contacts">
        <label className="profile-person__field profile-person__field--wide">
          <span className="profile-person__label-row">
            <span>Cargo</span>
            <HelpTooltip content={PERSON_PROFILE_HINTS.jobTitle} />
          </span>
          <input
            type="text"
            maxLength={200}
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="Ex.: Analista comercial"
            autoComplete="organization-title"
          />
        </label>

        <label className="profile-person__field">
          <span className="profile-person__label-row">
            <span>Telefone</span>
            <HelpTooltip content={PERSON_PROFILE_HINTS.contacts} />
          </span>
          <input
            type="tel"
            value={phoneE164}
            onChange={(e) => setPhoneE164(e.target.value)}
            placeholder="+5511333333333"
            autoComplete="tel"
          />
        </label>

        <label className="profile-person__field">
          <span>Celular</span>
          <input
            type="tel"
            value={mobileE164}
            onChange={(e) => setMobileE164(e.target.value)}
            placeholder="+5511999999999"
            autoComplete="tel"
          />
        </label>

        <div className="profile-person__checks">
          <label className="profile-person__check">
            <input
              type="checkbox"
              checked={whatsappSource === "phone"}
              disabled={!phoneE164.trim()}
              onChange={(e) =>
                setWhatsappSource(e.target.checked ? "phone" : null)
              }
            />
            Telefone também é WhatsApp
          </label>
          <label className="profile-person__check">
            <input
              type="checkbox"
              checked={whatsappSource === "mobile"}
              disabled={!mobileE164.trim()}
              onChange={(e) =>
                setWhatsappSource(e.target.checked ? "mobile" : null)
              }
            />
            Celular também é WhatsApp
          </label>
        </div>
      </div>

      <div className="profile-person__footer">
        <p className="profile-person__hint">
          Nome e e-mail vêm da conta corporativa e não são editáveis aqui.
        </p>
        <button
          type="button"
          className="profile-person__btn profile-person__btn--primary"
          onClick={() => void onSave()}
          disabled={saving || photoBusy}
        >
          {saving ? "Salvando…" : "Salvar contatos e cargo"}
        </button>
      </div>

      {lightboxOpen && hasPhoto ? (
        <div
          className="profile-person__lightbox"
          role="dialog"
          aria-modal="true"
          aria-labelledby={lightboxTitleId}
          onClick={() => setLightboxOpen(false)}
        >
          <div
            className="profile-person__lightbox-panel"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="profile-person__lightbox-toolbar">
              <h3 id={lightboxTitleId} className="profile-person__lightbox-title">
                Foto do perfil
              </h3>
              <button
                type="button"
                className="profile-person__lightbox-close"
                onClick={() => setLightboxOpen(false)}
                aria-label="Fechar"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <img
              src={previewUrl!}
              alt={userName ? `Foto de ${userName}` : "Foto do perfil"}
              className="profile-person__lightbox-img"
            />
            <div className="profile-person__lightbox-actions">
              <button
                type="button"
                className="profile-person__btn"
                onClick={onPickPhoto}
                disabled={photoBusy}
              >
                <Camera size={16} aria-hidden="true" />
                Trocar foto
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
