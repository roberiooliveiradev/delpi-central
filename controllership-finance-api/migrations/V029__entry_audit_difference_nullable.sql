-- E2/F1: difference is null for code/identification fields (origin, CST, CFOP…).
-- V023 created the column as NOT NULL DEFAULT ''; allow true null without rewriting history.

ALTER TABLE controllership_finance.entry_audit_occurrence
    ALTER COLUMN difference DROP NOT NULL;
