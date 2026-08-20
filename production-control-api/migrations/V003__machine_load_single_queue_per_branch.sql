-- Uma fila viva por filial.
--
-- Antes a chave era (filial, start_date, end_date): como a janela padrão era
-- "hoje até hoje + N", ela girava sozinha na virada do dia e o PCP começava o
-- turno com uma fila resemeada — perdendo ordem manual, conjuntos retirados e
-- transferências. A carga máquina nem sempre é processada todos os dias, então
-- a fila só pode mudar quando o PCP clicar em «Atualizar».
--
-- start_date / end_date passam a ser **dado** (a janela de entrega puxada no
-- último refresh), não identidade.

-- Mantém só o snapshot mais recente de cada filial; o resto era histórico de
-- janelas antigas que ninguém mais lê.
DELETE FROM production_control.machine_load_snapshots s
WHERE EXISTS (
    SELECT 1
    FROM production_control.machine_load_snapshots newer
    WHERE newer.branch = s.branch
      AND (newer.refreshed_at, newer.id) > (s.refreshed_at, s.id)
);

ALTER TABLE production_control.machine_load_snapshots
    DROP CONSTRAINT IF EXISTS uq_pc_machine_load_snapshots_scope;

ALTER TABLE production_control.machine_load_snapshots
    ADD CONSTRAINT uq_pc_machine_load_snapshots_branch UNIQUE (branch);

COMMENT ON TABLE production_control.machine_load_snapshots IS
    'Fila de carga máquina congelada pelo PCP: uma por filial, regenerada só via POST /machine-load/refresh.';

COMMENT ON COLUMN production_control.machine_load_snapshots.start_date IS
    'Início da janela de entrega do PA puxada no último refresh (vazio = aberto vira a entrega mais antiga).';

COMMENT ON COLUMN production_control.machine_load_snapshots.end_date IS
    'Fim da janela de entrega do PA puxada no último refresh (default: hoje + 14 dias).';
