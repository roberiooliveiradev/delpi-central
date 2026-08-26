import { Lock, Plus, Trash2 } from "lucide-react";
import type { MouseEvent, ReactNode } from "react";

import {
  MaintenanceActionButton,
  MaintenanceInteractiveDataCard,
  MaintenanceNativeCheckboxControl,
  MaintenanceStatusBadge,
} from "../../app/maintenanceUi";
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
import { EditableCell } from "../EditableCell";
import { CodigoDescricaoCell } from "../data/CodigoDescricaoCell";
import { PendingChangeBadge } from "../data";
import { formatCodigoDescricao } from "../../utils/pecaOptions";

type ListCardInlineActionsProps = {
  onSave?: () => void;
  onDelete?: () => void;
  saveLabel?: string;
  deleteLabel?: ReactNode;
};

function ListCardInlineActions({
  onSave,
  onDelete,
  saveLabel = "Salvar",
  deleteLabel = "Excluir",
}: ListCardInlineActionsProps) {
  if (!onSave && !onDelete) return null;

  function stopActivate(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
  }

  return (
    <div className="dm-row-actions dm-row-actions--inline dm-list-card__actions">
      {onSave ? (
        <MaintenanceActionButton
          variant="ghost"
          onClick={(event) => {
            stopActivate(event);
            onSave();
          }}
        >
          {saveLabel}
        </MaintenanceActionButton>
      ) : null}
      {onDelete ? (
        <MaintenanceActionButton
          variant="ghost"
          className="dm-btn--danger"
          onClick={(event) => {
            stopActivate(event);
            onDelete();
          }}
        >
          {deleteLabel}
        </MaintenanceActionButton>
      ) : null}
    </div>
  );
}

export function FilialListCard({
  filial,
  draft,
  dirty = false,
  onNomeChange,
  onStatusChange,
  onSave,
  onDelete,
}: {
  filial: FilialItem;
  draft?: { nome_filial: string; status_filial: "ativo" | "inativo" };
  dirty?: boolean;
  onNomeChange?: (nome: string) => void;
  onStatusChange?: (status: "ativo" | "inativo") => void;
  onSave?: () => void;
  onDelete?: () => void;
}) {
  const current = draft ?? {
    nome_filial: filial.nome_filial,
    status_filial: filial.status_filial,
  };
  const editable = Boolean(onSave || onDelete);

  return (
    <MaintenanceInteractiveDataCard
      className={editable ? "dm-list-card--editable" : undefined}
      interactive={false}
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
          value: editable ? (
            <EditableCell
              value={current.nome_filial}
              aria-label={`Nome da filial ${filial.codigo_filial}`}
              onChange={(nome_filial) => onNomeChange?.(nome_filial)}
              badge={<PendingChangeBadge visible={dirty} />}
            />
          ) : (
            current.nome_filial
          ),
        },
        {
          id: "status",
          label: "Status",
          value: editable ? (
            <EditableCell
              as="select"
              value={current.status_filial}
              aria-label={`Status da filial ${filial.codigo_filial}`}
              onChange={(status_filial) =>
                onStatusChange?.(status_filial as "ativo" | "inativo")
              }
              options={[
                { value: "ativo", label: "Ativo" },
                { value: "inativo", label: "Inativo" },
              ]}
            />
          ) : (
            <MaintenanceStatusBadge
              variant={current.status_filial === "ativo" ? "success" : "neutral"}
              label={current.status_filial === "ativo" ? "Ativo" : "Inativo"}
            />
          ),
        },
      ]}
      actions={
        editable ? <ListCardInlineActions onSave={onSave} onDelete={onDelete} /> : undefined
      }
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
  onEdit?: () => void;
  onDelete?: () => void;
};

export function ReposicaoListCard({ item, pecaDescricao, onEdit, onDelete }: ReposicaoListCardProps) {
  const editable = Boolean(onEdit || onDelete);

  return (
    <MaintenanceInteractiveDataCard
      interactive={false}
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
      actions={
        editable ? (
          <ListCardInlineActions
            onSave={onEdit}
            saveLabel="Editar"
            onDelete={onDelete}
          />
        ) : undefined
      }
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

export function MotivoListCard({
  item,
  draft,
  dirty = false,
  onDescricaoChange,
  onExcluirPreventivaChange,
  onSave,
  onDelete,
}: {
  item: MotivoItem;
  draft?: { descricao: string; excluir_preventiva: boolean };
  dirty?: boolean;
  onDescricaoChange?: (descricao: string) => void;
  onExcluirPreventivaChange?: (checked: boolean) => void;
  onSave?: () => void;
  onDelete?: () => void;
}) {
  const current = draft ?? {
    descricao: item.descricao,
    excluir_preventiva: Boolean(item.excluir_preventiva),
  };
  const editable = Boolean(onSave || onDelete);

  return (
    <MaintenanceInteractiveDataCard
      className={editable ? "dm-list-card--editable" : undefined}
      interactive={false}
      fields={[
        {
          id: "descricao",
          label: "Descrição",
          valueTone: "title",
          value: editable ? (
            <EditableCell
              value={current.descricao}
              aria-label={`Descrição do motivo ${item.motivo_id}`}
              onChange={(descricao) => onDescricaoChange?.(descricao)}
              badge={<PendingChangeBadge visible={dirty} />}
            />
          ) : (
            item.descricao
          ),
        },
        {
          id: "excluir",
          label: "Ignora preventiva",
          value: editable ? (
            <MaintenanceNativeCheckboxControl
              id={`dm-config-motivo-flag-card-${item.motivo_id}`}
              checked={current.excluir_preventiva}
              aria-label="Não conta no preventivo"
              onChange={(checked) => onExcluirPreventivaChange?.(checked)}
            />
          ) : (
            current.excluir_preventiva ? "Sim" : "Não"
          ),
        },
      ]}
      actions={
        editable ? <ListCardInlineActions onSave={onSave} onDelete={onDelete} /> : undefined
      }
    />
  );
}

const STATUS_OPERATORS = [">=", "<=", ">", "<"] as const;

export function StatusPreventivoListCard({
  item,
  draft,
  dirty = false,
  onDescricaoChange,
  onOperadorChange,
  onPercentualChange,
  onSave,
  onDelete,
}: {
  item: StatusItem;
  draft?: StatusItem;
  dirty?: boolean;
  onDescricaoChange?: (descricao: string) => void;
  onOperadorChange?: (operador: StatusItem["operador"]) => void;
  onPercentualChange?: (percentual: number) => void;
  onSave?: () => void;
  onDelete?: () => void;
}) {
  const current = draft ?? item;
  const editable = Boolean(onSave || onDelete);

  return (
    <MaintenanceInteractiveDataCard
      className={editable ? "dm-list-card--editable" : undefined}
      interactive={false}
      fields={[
        {
          id: "status",
          label: "Status",
          valueTone: "title",
          value: editable ? (
            <EditableCell
              value={current.descricao}
              aria-label={`Descrição do status ${item.status_id}`}
              onChange={(descricao) => onDescricaoChange?.(descricao)}
              badge={<PendingChangeBadge visible={dirty} />}
            />
          ) : (
            item.descricao
          ),
        },
        {
          id: "operador",
          label: "Operador",
          value: editable ? (
            <EditableCell
              as="select"
              value={current.operador}
              aria-label={`Operador do status ${item.status_id}`}
              onChange={(operador) =>
                onOperadorChange?.(operador as StatusItem["operador"])
              }
              options={STATUS_OPERATORS.map((operador) => ({
                value: operador,
                label: operador,
              }))}
            />
          ) : (
            item.operador
          ),
        },
        {
          id: "percentual",
          label: "Percentual",
          value: editable ? (
            <EditableCell
              type="number"
              min={0}
              value={current.percentual}
              aria-label={`Percentual do status ${item.status_id}`}
              onChange={(raw) => onPercentualChange?.(Number(raw))}
            />
          ) : (
            `${item.percentual}%`
          ),
        },
      ]}
      actions={
        editable ? <ListCardInlineActions onSave={onSave} onDelete={onDelete} /> : undefined
      }
    />
  );
}

export function ProgramaRankingListCard({
  row,
  canManage = false,
  adding = false,
  onAdd,
}: {
  row: RankingIntermediarioItem;
  canManage?: boolean;
  adding?: boolean;
  onAdd?: () => void;
}) {
  return (
    <MaintenanceInteractiveDataCard
      interactive={false}
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
      actions={
        canManage ? (
          <MaintenanceActionButton
            variant="ghost"
            disabled={Boolean(row.already_registered) || adding}
            onClick={(event) => {
              event.stopPropagation();
              onAdd?.();
            }}
          >
            <Plus size={16} aria-hidden />{" "}
            {row.already_registered ? "Já cadastrado" : "Adicionar"}
          </MaintenanceActionButton>
        ) : row.already_registered ? (
          <span className="dm-list-card__meta">Cadastrado</span>
        ) : undefined
      }
    />
  );
}

export function ProgramaCadastroListCard({
  row,
  canManage = false,
  onToggleAtivo,
  onDelete,
}: {
  row: ProgramaMaquinaProduto;
  canManage?: boolean;
  onToggleAtivo?: () => void;
  onDelete?: () => void;
}) {
  return (
    <MaintenanceInteractiveDataCard
      interactive={false}
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
      actions={
        canManage ? (
          <div className="dm-row-actions dm-row-actions--inline dm-list-card__actions">
            <MaintenanceActionButton
              variant="ghost"
              onClick={(event) => {
                event.stopPropagation();
                onToggleAtivo?.();
              }}
            >
              {row.ativo ? "Desativar" : "Ativar"}
            </MaintenanceActionButton>
            <MaintenanceActionButton
              variant="ghost"
              className="dm-btn--danger"
              onClick={(event) => {
                event.stopPropagation();
                onDelete?.();
              }}
              aria-label={`Remover ${row.codigo_intermediario}`}
            >
              <Trash2 size={16} />
            </MaintenanceActionButton>
          </div>
        ) : undefined
      }
    />
  );
}
