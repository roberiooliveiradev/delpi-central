import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  HOST_SELF_PROFILE_PATH,
  InitialsAvatar,
  PageHero,
  SectionCard,
  initialsAvatarBemClasses,
  navigateHostPath,
  pageHeroBemClasses,
  sectionCardPacBemClasses,
} from "@delpi/plugin-ui/index";
import {
  CheckSquare,
  Home,
  MessagesSquare,
  Pencil,
  Workflow,
} from "lucide-react";

import { PortalTopBar } from "../../components/TransformometroNav";
import { lookupDirectoryUsers } from "../../data/api/directoryUsersApi";
import { downloadPersonProfilePhoto } from "../../data/api/transformometroInteractionApi";
import { fetchMeProfile } from "../../data/api/meApi";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";

type Props = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  userId: string;
  onNavigate: (path: string) => void;
};

const HERO = pageHeroBemClasses("ds");
const AVATAR = initialsAvatarBemClasses("ds");
const SECTION = sectionCardPacBemClasses("ds");
const SECTION_LABELS = {
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

type Shortcut = {
  id: string;
  label: string;
  path: string;
  icon: typeof Home;
};

/**
 * Perfil do diretório no Portal Transforma+.
 * Modo leitura: identidade + atalhos do portal.
 * Editar (próprio): abre Meu Perfil Minha DELPI (`/profile`) para foto/cargo/contatos.
 */
export function PersonDirectoryPage({
  getAccessToken,
  pathname,
  userId,
  onNavigate,
}: Props) {
  const [meId, setMeId] = useState<string | null>(null);
  const [meLoading, setMeLoading] = useState(true);
  const [name, setName] = useState<string>("");
  const [email, setEmail] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setMeLoading(true);
    void fetchMeProfile(getAccessToken, controller.signal)
      .then((profile) => {
        if (!controller.signal.aborted) {
          setMeId((profile.id || "").trim() || null);
          setMeLoading(false);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setMeId(null);
          setMeLoading(false);
        }
      });
    return () => controller.abort();
  }, [getAccessToken]);

  const isSelf = useMemo((): boolean | null => {
    if (meLoading) return null;
    const me = (meId || "").trim();
    if (!me) return null;
    return me === userId.trim();
  }, [meId, meLoading, userId]);

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

  const shortcuts = useMemo<Shortcut[]>(
    () => [
      {
        id: "home",
        label: "Início",
        path: TRANSFORMOMETRO_ROUTES.home,
        icon: Home,
      },
      {
        id: "tasks",
        label: "Minhas tarefas",
        path: TRANSFORMOMETRO_ROUTES.myTasks,
        icon: CheckSquare,
      },
      {
        id: "rooms",
        label: "Sala de interação",
        path: TRANSFORMOMETRO_ROUTES.interactionRooms,
        icon: MessagesSquare,
      },
      {
        id: "processes",
        label: "Meus processos",
        path: TRANSFORMOMETRO_ROUTES.processes,
        icon: Workflow,
      },
    ],
    [],
  );

  const showBody = !loading && !meLoading && !error;

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
        {loading || meLoading ? (
          <p>Carregando perfil…</p>
        ) : error ? (
          <p role="alert">{error}</p>
        ) : showBody ? (
          <>
            <div
              style={{
                display: "flex",
                gap: "1rem",
                alignItems: "flex-start",
                justifyContent: "space-between",
                marginTop: "1rem",
                flexWrap: "wrap",
              }}
            >
              <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
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
                  description={
                    isSelf === true
                      ? "Seu perfil neste Portal. Foto, cargo e contatos editam-se no Meu Perfil Minha DELPI."
                      : "Perfil do diretório neste Portal (somente leitura)."
                  }
                />
              </div>
              {isSelf === true ? (
                <ActionButton
                  variant="primary"
                  type="button"
                  onClick={() => navigateHostPath(HOST_SELF_PROFILE_PATH)}
                >
                  <Pencil size={16} aria-hidden />
                  Editar perfil
                </ActionButton>
              ) : null}
            </div>

            <div
              style={{
                display: "grid",
                gap: "1rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(16rem, 1fr))",
                marginTop: "1.25rem",
              }}
            >
              <SectionCard classNames={SECTION} labels={SECTION_LABELS} title="Identidade">
                <dl>
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
              </SectionCard>

              <SectionCard
                classNames={SECTION}
                labels={SECTION_LABELS}
                title="Atalhos"
                subtitle="Áreas do Portal Transforma+."
              >
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {shortcuts.map((item) => {
                    const Icon = item.icon;
                    return (
                      <ActionButton
                        key={item.id}
                        variant="secondary"
                        type="button"
                        onClick={() => onNavigate(item.path)}
                      >
                        <Icon size={16} aria-hidden />
                        {item.label}
                      </ActionButton>
                    );
                  })}
                </div>
              </SectionCard>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
