import { NativeTextControl } from "@delpi/plugin-ui/index";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Copy, Link2, QrCode, RefreshCw, Trash2, UserPlus } from "lucide-react";

import { lookupDirectoryUsersByIds, searchDirectoryUsers, type DirectoryUser } from "../api/directoryApi";
import {
  acceptPlaylistEditInvite,
  activatePlaylist,
  createPlaylistEditInvite,
  deactivatePlaylist,
  downloadQrPng,
  getPlaylist,
  listPlaylistShares,
  regeneratePlaylistToken,
  revokePlaylistEditInvites,
  revokePlaylistShare,
  upsertPlaylistShare,
  type Playlist,
  type PlaylistShare,
} from "../api/tvDashboardApi";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { playlistPath } from "../routing";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

type Props = {
  playlistId: string;
  onBack: () => void;
};

type ShareRow = PlaylistShare & { label: string; email?: string };

export function PlaylistSharePage({ playlistId, onBack }: Props) {
  const confirm = useConfirm();
  const [playlist, setPlaylist] = useState<Playlist | null>(null);
  const [shares, setShares] = useState<PlaylistShare[]>([]);
  const [shareLabels, setShareLabels] = useState<Map<string, DirectoryUser>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<DirectoryUser[]>([]);
  const [shareRole, setShareRole] = useState<"viewer" | "editor">("editor");
  const [editInviteUrl, setEditInviteUrl] = useState<string | null>(null);
  const isOwner = playlist?.accessRole === "owner";

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const pl = await getPlaylist(playlistId);
      setPlaylist(pl);
      if (pl.accessRole === "owner") {
        const nextShares = await listPlaylistShares(playlistId);
        setShares(nextShares);
        const labels = await lookupDirectoryUsersByIds(nextShares.map((s) => s.targetUserId));
        setShareLabels(labels);
      } else {
        setShares([]);
        setShareLabels(new Map());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar programação.");
    } finally {
      setLoading(false);
    }
  }, [playlistId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!isOwner) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void searchDirectoryUsers(query, 8, controller.signal)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 250);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [isOwner, query]);

  const presentUrl = playlist?.publicUrl ?? "";

  function copyText(value: string, okMessage: string) {
    if (!value) return;
    void navigator.clipboard.writeText(value);
    tvDashboardNotice(okMessage);
  }

  function openQr() {
    void downloadQrPng(playlistId)
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, "_blank", "noopener,noreferrer");
        window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
      })
      .catch((err) => {
        tvDashboardNotice(err instanceof Error ? err.message : "Erro ao gerar QR.");
      });
  }

  async function handleToggleActive() {
    if (!playlist || !isOwner) return;
    const updated = playlist.isActive
      ? await deactivatePlaylist(playlist.id)
      : await activatePlaylist(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides, accessRole: playlist.accessRole });
  }

  async function handleRegenerateToken() {
    if (!playlist || !isOwner) return;
    const confirmed = await confirm({
      title: "Gerar novo link da TV",
      message:
        "Gerar novo link? TVs com o link atual deixarão de funcionar até usar o novo endereço.",
      confirmLabel: "Gerar novo link",
      variant: "danger",
    });
    if (!confirmed) return;
    const updated = await regeneratePlaylistToken(playlist.id);
    setPlaylist({ ...updated, slides: playlist.slides, accessRole: playlist.accessRole });
    tvDashboardNotice("Novo link da TV gerado.");
  }

  async function shareWithUser(user: DirectoryUser) {
    if (!isOwner) return;
    try {
      await upsertPlaylistShare(playlistId, { targetUserId: user.id, role: shareRole });
      setQuery("");
      setSuggestions([]);
      setShareLabels((prev) => new Map(prev).set(user.id, user));
      setShares(await listPlaylistShares(playlistId));
      tvDashboardNotice(`Compartilhado com ${user.name || user.email}.`);
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao compartilhar.");
    }
  }

  async function removeShare(targetUserId: string) {
    if (!isOwner) return;
    try {
      await revokePlaylistShare(playlistId, targetUserId);
      setShares((prev) => prev.filter((s) => s.targetUserId !== targetUserId));
      setShareLabels((prev) => {
        const next = new Map(prev);
        next.delete(targetUserId);
        return next;
      });
      tvDashboardNotice("Acesso removido.");
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao remover.");
    }
  }

  async function createEditLink() {
    if (!isOwner) return;
    try {
      const invite = await createPlaylistEditInvite(playlistId, "editor");
      const absolute = `${window.location.origin}${invite.redeemPath ?? ""}`;
      setEditInviteUrl(absolute);
      copyText(absolute, "Link de edição copiado.");
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao gerar link.");
    }
  }

  async function revokeEditLinks() {
    if (!isOwner) return;
    const confirmed = await confirm({
      title: "Revogar links de edição",
      message: "Links de edição ativos deixarão de funcionar. Colaboradores já adicionados permanecem.",
      confirmLabel: "Revogar",
      variant: "danger",
    });
    if (!confirmed) return;
    await revokePlaylistEditInvites(playlistId);
    setEditInviteUrl(null);
    tvDashboardNotice("Links de edição revogados.");
  }

  const shareList = useMemo<ShareRow[]>(
    () =>
      shares.map((share) => {
        const user = shareLabels.get(share.targetUserId);
        const label = user?.name || user?.email || share.targetUserId;
        return { ...share, label, email: user?.email };
      }),
    [shares, shareLabels],
  );

  if (loading) return <div className="td-state">Carregando…</div>;
  if (error || !playlist) return <div className="td-state">{error ?? "Programação não encontrada."}</div>;

  return (
    <>
      <div className="td-toolbar">
        <button type="button" className="td-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar ao editor
        </button>
      </div>

      <div className="td-card" style={{ maxWidth: 720, marginBottom: 16 }}>
        <h2 style={{ marginTop: 0 }}>Link da TV (apresentação)</h2>
        <p className="td-subtitle">
          {playlist.viewCount ?? 0} visualizações
          {playlist.isActive ? "" : " · link inativo"} · só exibe, sem edição
        </p>
        <div className="td-link-box">
          <NativeTextControl
            readOnly
            value={presentUrl}
            aria-label="Link público da TV"
            onChange={() => undefined}
          />
        </div>
        <div className="td-toolbar" style={{ marginTop: 16 }}>
          <button type="button" className="td-btn" onClick={() => copyText(presentUrl, "Link da TV copiado.")}>
            <Copy size={16} />
            Copiar link
          </button>
          <button type="button" className="td-btn" onClick={openQr}>
            <QrCode size={16} />
            QR code
          </button>
          {isOwner ? (
            <>
              <button type="button" className="td-btn" onClick={() => void handleRegenerateToken()}>
                <RefreshCw size={16} />
                Novo link
              </button>
              <button type="button" className="td-btn" onClick={() => void handleToggleActive()}>
                <Link2 size={16} />
                {playlist.isActive ? "Desativar link" : "Reativar link"}
              </button>
            </>
          ) : null}
        </div>
      </div>

      {isOwner ? (
        <>
          <div className="td-card" style={{ maxWidth: 720, marginBottom: 16 }}>
            <h2 style={{ marginTop: 0 }}>Colaboradores (edição)</h2>
            <p className="td-subtitle">
              Compartilhe com usuários cadastrados. O acesso fica atrelado ao ID do usuário (não ao e-mail).
            </p>
            <div className="td-toolbar" style={{ gap: 8, flexWrap: "wrap" }}>
              <div style={{ flex: "1 1 220px" }}>
                <NativeTextControl
                  value={query}
                  onChange={(value) => setQuery(value)}
                  placeholder="Buscar por nome ou e-mail…"
                  aria-label="Buscar usuário"
                />
              </div>
              <select
                className="td-select"
                value={shareRole}
                onChange={(event) => setShareRole(event.target.value as "viewer" | "editor")}
                aria-label="Papel"
              >
                <option value="editor">Editor</option>
                <option value="viewer">Somente leitura</option>
              </select>
            </div>
            {suggestions.length > 0 ? (
              <ul className="td-share-suggestions" style={{ listStyle: "none", padding: 0, marginTop: 8 }}>
                {suggestions.map((user) => (
                  <li key={user.id} style={{ marginBottom: 6 }}>
                    <button
                      type="button"
                      className="td-btn"
                      onClick={() => void shareWithUser(user)}
                    >
                      <UserPlus size={14} />
                      {user.name || user.email} · {user.email}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
            <ul style={{ listStyle: "none", padding: 0, marginTop: 16 }}>
              {shareList.length === 0 ? (
                <li className="td-subtitle">Nenhum colaborador ainda.</li>
              ) : (
                shareList.map((share) => (
                  <li
                    key={share.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 8,
                      marginBottom: 8,
                    }}
                  >
                    <span>
                      <strong>{share.label}</strong>
                      {share.email && share.email !== share.label ? (
                        <span className="td-subtitle"> · {share.email}</span>
                      ) : null}
                      <span className="td-subtitle"> · {share.role}</span>
                    </span>
                    <button
                      type="button"
                      className="td-btn"
                      onClick={() => void removeShare(share.targetUserId)}
                      aria-label="Remover colaborador"
                    >
                      <Trash2 size={14} />
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>

          <div className="td-card" style={{ maxWidth: 720 }}>
            <h2 style={{ marginTop: 0 }}>Link de edição</h2>
            <p className="td-subtitle">
              Quem abrir o link (já autenticado na Minha DELPI) ganha acesso de editor nesta programação.
            </p>
            {editInviteUrl ? (
              <div className="td-link-box" style={{ marginBottom: 12 }}>
                <NativeTextControl
                  readOnly
                  value={editInviteUrl}
                  aria-label="Link de edição"
                  onChange={() => undefined}
                />
              </div>
            ) : null}
            <div className="td-toolbar">
              <button type="button" className="td-btn" onClick={() => void createEditLink()}>
                <Copy size={16} />
                Gerar e copiar link de edição
              </button>
              <button type="button" className="td-btn" onClick={() => void revokeEditLinks()}>
                Revogar links de edição
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="td-card" style={{ maxWidth: 720 }}>
          <p className="td-subtitle">
            Você acessa esta programação como <strong>{playlist.accessRole ?? "colaborador"}</strong>.
            Apenas o dono gerencia compartilhamentos.
          </p>
        </div>
      )}
    </>
  );
}

export function AcceptPlaylistInvitePage({
  playlistId,
  token,
  onDone,
}: {
  playlistId: string;
  token: string;
  onDone: (id: string) => void;
}) {
  const [status, setStatus] = useState<"loading" | "error" | "ok">("loading");
  const [message, setMessage] = useState("Aceitando convite…");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Convite inválido.");
      return;
    }
    void acceptPlaylistEditInvite(token)
      .then((result) => {
        setStatus("ok");
        setMessage("Acesso concedido. Abrindo o editor…");
        window.setTimeout(() => onDone(result.playlistId || playlistId), 600);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Não foi possível aceitar o convite.");
      });
  }, [onDone, playlistId, token]);

  return (
    <div className="td-state">
      {status === "loading" ? "Aceitando convite…" : null}
      {status !== "loading" ? message : null}
    </div>
  );
}

export function editorPathForShare(playlistId: string) {
  return playlistPath(playlistId);
}
