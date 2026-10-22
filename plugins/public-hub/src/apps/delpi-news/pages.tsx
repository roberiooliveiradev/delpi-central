import type { AppPublicPages } from "../../shell/types";
import { loadPublicNewsBoard } from "./loadBoard";
import { NewsBoardView } from "./NewsBoardView";
import type { PublicNewsBoard } from "./types";

export const delpiNewsPages: AppPublicPages = {
  board: {
    documentTitle: "DELPI News — DELPI",
    chrome: "kiosk",
    notFoundTitle: "Board indisponível",
    notFoundMessage: "Este board de notícias não está disponível ou foi desativado.",
    load: ({ token }) => loadPublicNewsBoard(token),
    render: (data) => <NewsBoardView board={data as PublicNewsBoard} />,
  },
};
