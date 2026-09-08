import { useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from "react";
import { Camera, Trash2 } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient, HttpError } from "../../data/apiClient";
import {
  CoreApi,
  type PersonProfileResponse,
} from "../../data/coreApi";
import { HelpTooltip } from "../../components/HelpTooltip";
import {
  resolveWhatsappE164,
  resolveWhatsappSource,
  type WhatsappSource,
} from "./personProfileWhatsapp";

const PERSON_PROFILE_HINTS = {
  photo:
    "Envie JPEG, PNG, WebP ou GIF até 2 MB. A foto aparece no menu e no Meu Perfil. Não sincroniza com o Keycloak.",
  jobTitle:
    "Cargo informado por você no portal. Não sincroniza com RH ou Keycloak nesta fase.",
  contacts:
    "Telefone e celular no formato internacional (+55…). Marque qual número também é WhatsApp.",
};

type PersonProfileEditorProps = {
  userName?: string;
  onPhotoChanged?: () => void;
};

export function PersonProfileEditor({
  userName,
  onPhotoChanged,
}: PersonProfileEditorProps) {
  const { getAccessToken, refreshToken } = useContext(AuthContext);
  const fileInputId = useId();
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
      onPhotoChanged?.();
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
      onPhotoChanged?.();
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

      <div className="profile-person__photo-row" data-tour="profile-person-photo">
        <div className="profile-person__avatar" aria-hidden={!previewUrl}>
          {previewUrl ? (
            <img src={previewUrl} alt="" className="profile-person__avatar-img" />
          ) : (
            <span className="profile-person__avatar-initials">{initials}</span>
          )}
        </div>
        <div className="profile-person__photo-actions">
          <div className="profile-person__label-row">
            <span className="profile-person__section-label">Foto</span>
            <HelpTooltip content={PERSON_PROFILE_HINTS.photo} />
          </div>
          <div className="profile-person__btn-row">
            <button
              type="button"
              className="profile-person__btn"
              onClick={onPickPhoto}
              disabled={photoBusy}
            >
              <Camera size={16} aria-hidden="true" />
              {profile?.has_photo ? "Alterar foto" : "Enviar foto"}
            </button>
            {profile?.has_photo ? (
              <button
                type="button"
                className="profile-person__btn profile-person__btn--danger"
                onClick={() => void onRemovePhoto()}
                disabled={photoBusy}
              >
                <Trash2 size={16} aria-hidden="true" />
                Remover
              </button>
            ) : null}
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
      </div>

      <div className="profile-person__fields" data-tour="profile-person-contacts">
        <label className="profile-person__field">
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
    </div>
  );
}
