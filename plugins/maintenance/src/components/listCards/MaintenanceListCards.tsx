import { Lock } from "lucide-react";

import { MaintenanceInteractiveDataCard, MaintenanceStatusBadge } from "../../app/maintenanceUi";
import type {
  FerramentaItem,
  FilialItem,
  MotivoItem,
  OndeUsadoItem,
  PecaReposicaoItem,
  ProgramaMaquinaProduto,
  RankingIntermediarioItem,
  ReposicaoItem,
  StatusItem,
} from "../../data/api/maintenanceApi";
import { CodigoDescricaoCell } from "../data/CodigoDescricaoCell";
import { formatCodigoDescricao } from "../../utils/pecaOptions";

export function FilialListCard({ filial }: { filial: FilialItem }) {
  return (
    <MaintenanceInteractiveDataCard
      fields={[
        {
          id: "codigo",
          label: "Código",
          valueTone: "title",
          value: filial.codigo_filial,
        },
        {
          id: "nome",
          label: "Nome",
          value: filial.nome_filial,
        },
        {
          id: "status",
          label: "Status",
          value: (
            <MaintenanceStatusBadge
              variant={filial.status_filial === "ativo" ? "success" : "neutral"}
              label={filial.status_filial === "ativo" ? "Ativo" : "Inativo"}
            />
          ),
        },
      ]}
    />
  );
}

type FerramentaListCardProps = {
  item: FerramentaItem;
  onActivate?: () => void;
};

export function FerramentaListCard({ item, onActivate }: FerramentaListCardProps) {
  return (
    <MaintenanceInteractiveDataCard
      onActivate={onActivate}
      openHint="Abrir detalhe da ferramenta"
      ariaLabel={`Ferramenta ${item.codigo}`}
      fields={[
        {
          id: "codigo",
          label: "Código",
          valueTone: "title",
          value: (
            <span className="dm-ferramenta-codigo">
              {item.bloqueado ? (
                <Lock size={14} className="dm-ferramenta-codigo__lock" aria-hidden="true" />
              ) : null}
              <span>{item.codigo}</span>
            </span>
          ),
        },
        {
          id: "descricao",
          label: "Descrição",
          value: item.descricao,
        },
      ]}
    />
  );
}

type ReposicaoListCardProps = {
  item: ReposicaoItem;
  pecaDescricao?: string;
  onActivate?: () => void;
};

export function ReposicaoListCard({ item, pecaDescricao, onActivate }: ReposicaoListCardProps) {
  return (
    <MaintenanceInteractiveDataCard
      onActivate={onActivate}
      openHint="Editar reposição"
      ariaLabel={`Reposição ${item.reposicao_id}`}
      fields={[
        {
          id: "data",
          label: "Data",
          valueTone: "title",
          value: new Date(item.data_reposicao).toLocaleString("pt-BR"),
        },
        {
          id: "peca",
          label: "Peça",
          value: (
            <CodigoDescricaoCell
              codigo={item.codigo_peca}
              descricao={pecaDescricao ?? item.codigo_peca}
            />
          ),
        },
        {
          id: "golpes",
          label: "Golpes",
          value: String(item.golpes),
        },
        {
          id: "motivo",
          label: "Motivo",
          value: item.motivo_descricao ?? String(item.motivo_id),
        },
      ]}
    />
  );
}

export function PecaAmarradaListCard({
  item,
  onActivate,
}: {
  item: PecaReposicaoItem;
  onActivate?: () => void;
}) {
  return (
    <MaintenanceInteractiveDataCard
      onActivate={onActivate}
      openHint="Selecionar peça"
      ariaLabel={`Peça ${item.codigo}`}
      fields={[
        {
          id: "codigo",
          label: "Código",
          valueTone: "title",
          value: item.codigo,
        },
        {
          id: "descricao",
          label: "Descrição",
          value: item.descricao || "—",
        },
      ]}
    />
  );
}

export function OndeUsadoListCard({ item }: { item: OndeUsadoItem }) {
  return (
    <MaintenanceInteractiveDataCard
      fields={[
        {
          id: "codigo",
          label: "Produto",
          valueTone: "title",
          value: formatCodigoDescricao(item.codigo, item.descricao),
        },
        {
          id: "nivel",
          label: "Nível",
          value: String(item.nivel),
        },
      ]}
    />
  );
}

export function MotivoListCard({ item }: { item: MotivoItem }) {
  return (
    <MaintenanceInteractiveDataCard
      fields={[
        {
          id: "descricao",
          label: "Descrição",
          valueTone: "title",
          value: item.descricao,
        },
        {
          id: "excluir",
          label: "Ignora preventiva",
          value: item.excluir_preventiva ? "Sim" : "Não",
        },
      ]}
    />
  );
}

export function StatusPreventivoListCard({ item }: { item: StatusItem }) {
  return (
    <MaintenanceInteractiveDataCard
      fields={[
        {
          id: "status",
          label: "Status",
          valueTone: "title",
          value: item.descricao,
        },
        {
          id: "operador",
          label: "Operador",
          value: item.operador,
        },
        {
          id: "percentual",
          label: "Percentual",
          value: `${item.percentual}%`,
        },
      ]}
    />
  );
}

export function ProgramaRankingListCard({ row }: { row: RankingIntermediarioItem }) {
  return (
    <MaintenanceInteractiveDataCard
      fields={[
        {
          id: "pi",
          label: "Intermediário",
          valueTone: "title",
          value: row.intermediate_code,
        },
        {
          id: "pa",
          label: "PA",
          value: row.finished_product_code || "—",
        },
        {
          id: "ct",
          label: "CT corte",
          value: row.cutting_work_center || "—",
        },
        {
          id: "op",
          label: "OP aberta",
          value: row.has_open_production_order ? "Sim" : "Não",
        },
        {
          id: "qty",
          label: "Qtd produzida",
          value: (row.qty_produced ?? 0).toLocaleString("pt-BR"),
        },
      ]}
    />
  );
}

export function ProgramaCadastroListCard({ row }: { row: ProgramaMaquinaProduto }) {
  return (
    <MaintenanceInteractiveDataCard
      fields={[
        {
          id: "pi",
          label: "Intermediário",
          valueTone: "title",
          value: row.codigo_intermediario,
        },
        {
          id: "descricao",
          label: "Descrição",
          value: row.descricao_intermediario || "—",
        },
        {
          id: "pa",
          label: "PA",
          value: row.codigo_produto_acabado || "—",
        },
        {
          id: "ativo",
          label: "Ativo",
          value: row.ativo ? "Sim" : "Não",
        },
      ]}
    />
  );
}
