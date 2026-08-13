import { EmptyState } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  deleteUserProfilePhoto,
  getUserProfile,
  patchUserProfile,
  uploadUserProfilePhoto,
  userProfilePhotoAbsoluteUrl,
  type UserProfileDto,
} from "../../api/userProfileApi";
import { httpGetBlob } from "../../api/httpClient";
import {
  cmEmptyStateClassNames,
  CommercialActionButton,
  CommercialAvatar,
  CommercialFileDropzone,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialStateBanner,
  CommercialStatusBadge,
  CommercialTextField,
} from "../../app/commercialUi";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { CM_HELP } from "../../content/helpTooltips";
import { buildSellerPortfolioDetailPath } from "../../utils/sellerPortfoliosDeepLink";

type UserProfilePageProps = {
  basePath: string;
  userId: string;
};

export function UserProfilePage({ basePath, userId }: UserProfilePageProps) {
  const { currentUserId, canManagePortfolios } = usePortfolioScope();
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<UserProfileDto | null>(null);
  const [jobTitle, setJobTitle] = useState("");
  const [photoObjectUrl, setPhotoObjectUrl] = useState<string | null>(null);

  const canEdit = useMemo(() => {
    const me = (currentUserId || "").trim();
    const target = userId.trim();
    return Boolean(me && (me === target || canManagePortfolios));
  }, [canManagePortfolios, currentUserId, userId]);

  const reload = useCallback(
    async (signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      try {
        const data = await getUserProfile(userId, signal);
        if (signal?.aborted) return;
        setProfile(data);
        setJobTitle((data.job_title || "").trim());
      } catch (err: unknown) {
        if (signal?.aborted) return;
        setProfile(null);
        setError(err instanceof Error ? err.message : "Falha ao carregar perfil.");
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [userId],
  );

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  useEffect(() => {
    let revoked: string | null = null;
    let cancelled = false;
    if (!profile?.has_photo) {
      setPhotoObjectUrl(null);
      return undefined;
    }
    void httpGetBlob(userProfilePhotoAbsoluteUrl(userId))
      .then((blob) => {
        if (cancelled) return;
        const url = URL.createObjectURL(blob);
        revoked = url;
        setPhotoObjectUrl(url);
      })
      .catch(() => {
        if (!cancelled) setPhotoObjectUrl(null);
      });
    return () => {
      cancelled = true;
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [profile?.has_photo, profile?.updated_at, userId]);

  const onSaveJobTitle = async () => {
    if (!canEdit) return;
    setSaving(true);
    try {
      const data = await patchUserProfile(userId, { job_title: jobTitle.trim() || null });
      setProfile(data);
      setJobTitle((data.job_title || "").trim());
      notifySuccess("Cargo atualizado.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao salvar cargo.");
    } finally {
      setSaving(false);
    }
  };

  const onUploadPhoto = async (files: File[]) => {
    if (!canEdit || files.length === 0) return;
    setSaving(true);
    try {
      const data = await uploadUserProfilePhoto(userId, files[0]!);
      setProfile(data);
      notifySuccess("Foto atualizada.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao enviar foto.");
    } finally {
      setSaving(false);
    }
  };

  const onRemovePhoto = async () => {
    if (!canEdit) return;
    setSaving(true);
    try {
      const data = await deleteUserProfilePhoto(userId);
      setProfile(data);
      notifySuccess("Foto removida.");
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : "Falha ao remover foto.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <CommercialLoadingCard title="Carregando perfil…" />;
  }

  if (error || !profile) {
    return (
      <CommercialStateBanner variant="error">
        {error || "Não foi possível abrir o perfil."}
      </CommercialStateBanner>
    );
  }

  return (
    <div className="cm-user-profile cm-page-stack">
      <CommercialPagePath
        back={{
          label: "Portal Comercial",
          href: basePath,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(basePath);
          },
        }}
        items={[]}
        current={profile.name || profile.user_id}
      />
      <CommercialPageHero
        title={profile.name || profile.user_id}
        description={[profile.email, profile.job_title].filter(Boolean).join(" · ") || undefined}
      />

      <CommercialSectionCard title="Identidade" hint={CM_HELP.users.profile}>
        <div
          style={{
            display: "flex",
            gap: 16,
            alignItems: "flex-start",
            flexWrap: "wrap",
          }}
        >
          <CommercialAvatar
            name={profile.name || profile.user_id}
            colorKey={profile.user_id}
            src={photoObjectUrl}
            size="lg"
          />
          <div style={{ display: "grid", gap: 12, minWidth: 240, flex: 1 }}>
            <p style={{ margin: 0 }}>{profile.email || "Sem e-mail"}</p>
            <CommercialStatusBadge label="Commercial" variant="success" />
            {canEdit ? (
              <>
                <CommercialTextField
                  label="Cargo"
                  value={jobTitle}
                  onChange={setJobTitle}
                  hint={CM_HELP.users.jobTitle}
                />
                <CommercialActionButton
                  variant="primary"
                  disabled={saving}
                  onClick={() => void onSaveJobTitle()}
                >
                  Salvar cargo
                </CommercialActionButton>
                <CommercialFileDropzone
                  multiple={false}
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  fieldLabel="Foto"
                  onFilesSelected={(files) => void onUploadPhoto(files)}
                  labels={{
                    title: "Trocar foto",
                    hint: "JPEG, PNG, WebP ou GIF · máx. 2 MB",
                  }}
                />
                {profile.has_photo ? (
                  <CommercialActionButton
                    variant="ghost"
                    disabled={saving}
                    onClick={() => void onRemovePhoto()}
                  >
                    Remover foto
                  </CommercialActionButton>
                ) : null}
              </>
            ) : (
              <p style={{ margin: 0 }}>
                {(profile.job_title || "").trim() || "Cargo não informado"}
              </p>
            )}
          </div>
        </div>
      </CommercialSectionCard>

      <CommercialSectionCard title="Carteiras" hint={CM_HELP.users.portfolios}>
        {profile.portfolios.length === 0 ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultTitle="Nenhuma carteira"
            defaultMessage="Este usuário ainda não é membro de carteiras ativas."
          />
        ) : (
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 8 }}>
            {profile.portfolios.map((item) => {
              const href = canManagePortfolios
                ? buildSellerPortfolioDetailPath(basePath, item.id)
                : null;
              return (
                <li
                  key={item.id}
                  style={{
                    display: "flex",
                    gap: 12,
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  {href ? (
                    <button
                      type="button"
                      onClick={() => navigatePluginPath(href)}
                      style={{
                        border: 0,
                        background: "transparent",
                        color: "inherit",
                        cursor: "pointer",
                        textDecoration: "underline",
                        padding: 0,
                      }}
                    >
                      {item.name}
                    </button>
                  ) : (
                    <span>{item.name}</span>
                  )}
                  <CommercialStatusBadge
                    label={item.active ? "Ativa" : "Inativa"}
                    variant={item.active ? "success" : "info"}
                  />
                </li>
              );
            })}
          </ul>
        )}
      </CommercialSectionCard>

      <CommercialSectionCard title="Sobre">
        <p style={{ margin: 0 }}>
          Perfil do Portal Comercial. Dados de RH serão integrados em fase futura.
        </p>
      </CommercialSectionCard>
    </div>
  );
}
