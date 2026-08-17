import { MonitorPlay } from "lucide-react";

import type { Playlist, Slide } from "../api/tvDashboardApi";
import { SlideCardThumbnail } from "./SlideCardThumbnail";

type Props = {
  playlist: Pick<
    Playlist,
    | "id"
    | "viewportProfile"
    | "viewportWidth"
    | "viewportHeight"
    | "masterConfig"
    | "publicToken"
    | "coverSlide"
  >;
};

/** Miniatura da capa na home — mesmo pipeline do filmstrip / biblioteca de templates. */
export function PlaylistHomeThumb({ playlist }: Props) {
  const cover = playlist.coverSlide as Slide | null | undefined;
  if (!cover) {
    return (
      <span className="td-library-card-thumb-fallback" aria-hidden="true">
        <MonitorPlay size={28} strokeWidth={1.6} />
      </span>
    );
  }

  return (
    <SlideCardThumbnail
      slide={cover}
      playlistId={playlist.id}
      viewportProfile={playlist.viewportProfile || "1080p"}
      viewportWidth={playlist.viewportWidth}
      viewportHeight={playlist.viewportHeight}
      masterConfig={playlist.masterConfig}
      publicToken={playlist.publicToken}
      fillContainer
    />
  );
}
