/**
 * Página do usuário — deep route `/profile` self-only (F5).
 *
 * Dados corporativos vêm do Core via `/me/profile` (read-through,
 * Bearer do usuário, sem cache nem cadastro paralelo). A foto vem do
 * read-through `/viewer-photo`. Permissões e grupos são exibidos
 * apenas ao próprio usuário — privacidade por contrato self-only.
 * Não há edição aqui: identidade pertence ao Core.
 */
import { useEffect, useState } from "react";

import { UserRound } from "lucide-react";

import {
  ApiError,
  cfApiUrl,
  httpGetImageBlob,
} from "../../api/httpClient";
import { getMyProfile, type MyProfile } from "../../api/meApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  CfLoadingCard,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { ClosingHero } from "../../app/ClosingHero";
import { useViewerContext } from "../../app/ViewerContext";
import { CF_HELP } from "../../content/helpTooltips";

type PanelError = { status: number; code: string | null; message: string };

const ERROR_MESSAGES: Record<string, string> = {
  unauthorized: "Sessão expirada — autentique-se novamente.",
  forbidden: "Você não tem acesso a esta área.",
};

const PERMISSION_LABELS: Record<string, string> = {
  "controllership-finance.access": "Acesso ao portal",
  "controllership-finance.manage": "Gestão da Central de Fechamento",
};

function mapError(error: unknown): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code ?? null,
      message: ERROR_MESSAGES[error.code ?? ""] ?? error.message,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação com a API.",
  };
}

function personField(
  profile: Record<string, unknown> | null,
  key: string,
): string | null {
  const value = profile?.[key];
  return typeof value === "string" && value.trim() ? value : null;
}

export function ProfilePage() {
  const { viewer } = useViewerContext();
  const [profile, setProfile] = useState<MyProfile | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<PanelError | null>(null);

  const reload = () => {
    setLoading(true);
    setError(null);
    void getMyProfile()
      .then(setProfile)
      .catch((err) => setError(mapError(err)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!viewer?.capabilities.access) {
      setPhotoUrl(null);
      return;
    }
    const controller = new AbortController();
    let objectUrl: string | null = null;
    void httpGetImageBlob(
      cfApiUrl("/viewer-photo"),
      controller.signal,
    )
      .then((blob) => {
        if (controller.signal.aborted || !blob) return;
        objectUrl = URL.createObjectURL(blob);
        setPhotoUrl(objectUrl);
      })
      .catch(() => {
        if (!controller.signal.aborted) setPhotoUrl(null);
      });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [viewer?.capabilities.access]);

  const person = profile?.personProfile ?? null;
  const corporateName =
    personField(person, "fullName") ??
    personField(person, "name") ??
    profile?.displayName ??
    "—";
  const corporateEmail =
    personField(person, "email") ?? profile?.email ?? "—";
  const corporateId =
    personField(person, "registration") ??
    personField(person, "employeeId") ??
    personField(person, "registrationNumber") ??
    null;
  const department =
    personField(person, "department") ??
    personField(person, "area") ??
    null;
  const jobTitle =
    personField(person, "jobTitle") ??
    personField(person, "role") ??
    null;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Perfil do usuário"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Meu perfil"
            hint={CF_HELP.profile.identity}
          />
        }
        subtitle="Seus dados corporativos e permissões neste portal — somente você os vê."
        filters={null}
        updatedAt={null}
        onRefresh={reload}
        refreshing={loading}
        onClearFilters={() => {}}
      />
      <div className="cf-page-stack" aria-busy={loading}>
        {loading ? (
          <CfLoadingCard
            title="Carregando perfil…"
            variant="panel"
          />
        ) : null}
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="seu perfil"
            onRetry={reload}
          />
        ) : null}

        {!loading && !error && profile ? (
          <>
            <CfSectionCard
              title="Identidade"
              hint={CF_HELP.profile.identity}
            >
              <div className="cf-profile-identity">
                {photoUrl ? (
                  <img
                    className="cf-profile-photo"
                    src={photoUrl}
                    alt={`Foto de ${corporateName}`}
                  />
                ) : (
                  <span
                    className="cf-profile-photo cf-profile-photo--placeholder"
                    aria-hidden="true"
                  >
                    <UserRound size={32} strokeWidth={1.5} />
                  </span>
                )}
                <div>
                  <h2>{corporateName}</h2>
                  <p>{corporateEmail}</p>
                  {jobTitle ? <p>{jobTitle}</p> : null}
                  {department ? <p>{department}</p> : null}
                  {corporateId ? (
                    <p>Matrícula: {corporateId}</p>
                  ) : null}
                </div>
              </div>
              {person === null ? (
                <CfFeedbackMessage
                  intent="info"
                  title="Dados corporativos indisponíveis"
                >
                  O Core não retornou perfil corporativo nesta sessão —
                  exibidos apenas os dados básicos de identidade.
                </CfFeedbackMessage>
              ) : null}
            </CfSectionCard>

            <CfSectionCard
              title="Vínculos corporativos"
              hint={CF_HELP.profile.groups}
            >
              {profile.groups.length === 0 ? (
                <CfEmptyState
                  classNames={cfEmptyStateClassNames}
                  defaultMessage="Nenhum grupo corporativo associado."
                />
              ) : (
                <ul className="cf-tag-list" aria-label="Grupos">
                  {profile.groups.map((group) => (
                    <li key={group}>
                      <CfStatusBadge label={group} variant="info" />
                    </li>
                  ))}
                </ul>
              )}
            </CfSectionCard>

            <CfSectionCard
              title="Permissões neste portal"
              hint={CF_HELP.profile.permissions}
            >
              {profile.permissions.length === 0 ? (
                <CfEmptyState
                  classNames={cfEmptyStateClassNames}
                  defaultMessage="Nenhuma permissão efetiva registrada."
                />
              ) : (
                <ul className="cf-tag-list" aria-label="Permissões">
                  {profile.permissions.map((permission) => (
                    <li key={permission}>
                      <CfStatusBadge
                        label={
                          PERMISSION_LABELS[permission] ?? permission
                        }
                        variant="neutral"
                      />
                    </li>
                  ))}
                </ul>
              )}
              {viewer ? (
                <p className="cf-cell-secondary">
                  Capacidades efetivas nesta sessão:{" "}
                  {viewer.capabilities.access ? "acesso" : "sem acesso"}
                  {viewer.capabilities.manage ? " · gestão" : ""}
                </p>
              ) : null}
            </CfSectionCard>
          </>
        ) : null}
      </div>
    </section>
  );
}
