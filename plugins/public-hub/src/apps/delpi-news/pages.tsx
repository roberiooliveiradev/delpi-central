import type { AppPublicPages } from "../../shell/types";
import { loadPublicNewsBoard } from "./loadBoard";
import { NewsBoardView } from "./NewsBoardView";
import type { PublicNewsBoard } from "./types";

export const delpiNewsPages: AppPublicPages = {
  board: {
    documentTitle: "DELPI News (demonstração) — DELPI",
    chrome: "kiosk",
    notFoundTitle: "Demonstração indisponível",
    notFoundMessage:
      "A prova visual do DELPI News não está habilitada neste ambiente. Em produção o mock fica desligado por padrão.",
    load: ({ token }) => loadPublicNewsBoard(token),
    render: (data) => <NewsBoardView board={data as PublicNewsBoard} />,
  },
};
