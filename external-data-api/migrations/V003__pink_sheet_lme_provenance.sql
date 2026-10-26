-- PROC-0076 R1 — provenance refinement for the Pink Sheet feed.
--
-- World Bank datasets are CC BY 4.0, but the official datasets Terms of
-- Use explicitly exclude third-party content
-- (https://www.worldbank.org/ext/en/legal/terms-conditions/datasets):
-- the six metal series ingested are London Metal Exchange (LME)
-- settlement prices republished by the World Bank — Pink Sheet
-- "Description" sheet, Metals and Minerals rows (Aluminum/Copper/Lead/
-- Nickel/Tin/Zinc "(LME) ... settlement price"). CC BY 4.0 covers the
-- WB *publication*, not the underlying LME data, so the recorded scope
-- is narrowed to internal display with dual attribution and no onward
-- redistribution until LME terms are reviewed. Nothing here changes
-- what was collected; it makes the license evidence honest.

UPDATE external_data.market_data_sources
SET attribution = 'World Bank — Commodity Markets "Pink Sheet"; underlying prices: London Metal Exchange (LME) settlement',
    license_reference = 'CC BY 4.0 (WB publication; third-party LME data excluded per WB datasets ToU) — https://www.worldbank.org/ext/en/legal/terms-conditions/datasets',
    allowed_use_scope = 'collect;store;derive;internal_display;no_redistribution_pending_lme_review',
    license_reviewed_at = DATE '2026-10-26'
WHERE source_id = 'world-bank-pink-sheet';

-- The instrument market also names the underlying exchange so consumers
-- never present LME prices as an unrestricted WB dataset.
UPDATE external_data.metal_instruments
SET market = 'lme_via_world_bank_pink_sheet'
WHERE source_id = 'world-bank-pink-sheet';
