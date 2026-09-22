import { useEffect, useState } from "react";
import {
  ActionButton,
  InitialsAvatar,
  PageHero,
  initialsAvatarBemClasses,
  pageHeroBemClasses,
} from "@delpi/plugin-ui/index";

import { PortalTopBar } from "../../components/TransformometroNav";
import { lookupDirectoryUsers } from "../../data/api/directoryUsersApi";
import { downloadPersonProfilePhoto } from "../../data/api/transformometroInteractionApi";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

type Props = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  userId: string;
  onNavigate: (path: string) => void;
};

const HERO = pageHeroBemClasses("ds");
const AVATAR = initialsAvatarBemClasses("ds");

/**
 * Perfil do diretório no Portal Transforma+ (próprio e outros).
 * Identidade global editável fica em `/profile` do host Minha DELPI.
 */
export function PersonDirectoryPage({
  getAccessToken,
  pathname,
  userId,
  onNavigate,
}: Props) {
  const [name, setName] = useState<string>("");
  const [email, setEmail] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = userId.trim();
    if (!id) return;

    const controller = new AbortController();
    let objectUrl: string | null = null;
    setLoading(true);
    setError(null);

    void Promise.all([
      lookupDirectoryUsers([id], controller.signal, getAccessToken),
      downloadPersonProfilePhoto(id, getAccessToken).catch(() => null),
    ])
      .then(([users, blob]) => {
        if (controller.signal.aborted) return;
        const hit = users[0];
        setName(hit?.name?.trim() || "Usuário");
        setEmail(hit?.email?.trim() || null);
        if (blob) {
          objectUrl = URL.createObjectURL(blob);
          setPhotoUrl(objectUrl);
        } else {
          setPhotoUrl(null);
        }
        setLoading(false);
      })
      .catch(() => {
        if (controller.signal.aborted) return;
        setError("Não foi possível carregar este perfil.");
        setLoading(false);
      });

    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [getAccessToken, userId]);

  return (
    <div className="tm-page">
      <PortalTopBar
        currentPath={pathname ?? `${TRANSFORMOMETRO_ROUTES.home}/users/${userId}`}
        onNavigate={onNavigate}
      />
      <div className="tm-page__body" style={{ padding: "1rem 1.25rem" }}>
        <ActionButton
          variant="ghost"
          type="button"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.home)}
        >
          ← Voltar
        </ActionButton>
        {loading ? (
          <p>Carregando perfil…</p>
        ) : error ? (
          <p role="alert">{error}</p>
        ) : (
          <>
            <div
              style={{
                display: "flex",
                gap: "1rem",
                alignItems: "center",
                marginTop: "1rem",
              }}
            >
              <InitialsAvatar
                classNames={AVATAR}
                name={name}
                src={photoUrl}
                size="lg"
                alt=""
              />
              <PageHero
                classNames={HERO}
                title={name}
                description="Perfil do diretório neste Portal (somente leitura). Foto, cargo e contatos editam-se no Meu Perfil Minha DELPI."
              />
            </div>
            <dl style={{ marginTop: "1.25rem" }}>
              <div>
                <dt>Nome</dt>
                <dd>{name}</dd>
              </div>
              {email ? (
                <div>
                  <dt>E-mail</dt>
                  <dd>{email}</dd>
                </div>
              ) : null}
            </dl>
          </>
        )}
      </div>
    </div>
  );
}
