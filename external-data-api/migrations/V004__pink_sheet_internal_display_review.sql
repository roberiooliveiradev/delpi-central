-- PROC-0076 R1.1 — license-evidence refinement for the Pink Sheet feed.
--
-- R1's V003 correctly flagged the underlying LME provenance, but its
-- recorded scope still granted `internal_display` unconditionally and
-- marked only *redistribution* as pending review. The official World
-- Bank datasets Terms of Use
-- (https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets)
-- state that third-party-provided data "may not be redistributed or
-- reused without the consent of the original data provider" and defer
-- to the provider's own terms. The LME licenses display, non-display,
-- derived and distribution uses separately
-- (https://www.lme.com/market-data/market-data-licensing), with only a
-- limited internal business use outside licence scope.
--
-- Evidence therefore supports: collect / store / derive of the
-- WB-published workbook = covered by the WB grant; displaying LME
-- settlement prices inside a corporate application = pending formal
-- rights review; any onward redistribution = prohibited until licensed.
-- This UPDATE narrows the recorded scope so metadata never presents an
-- unproven use as granted. Nothing here removes data or disables the
-- (already opt-in) feed.

UPDATE external_data.market_data_sources
SET license_reference = 'CC BY 4.0 (WB publication; third-party LME data excluded per WB datasets ToU — https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets). LME terms: https://www.lme.com/market-data/market-data-licensing',
    allowed_use_scope = 'collect;store;derive;internal_display_pending_lme_review;no_redistribution_pending_lme_review',
    license_reviewed_at = DATE '2026-10-27'
WHERE source_id = 'world-bank-pink-sheet';
