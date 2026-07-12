ALTER TABLE tv_dashboard.media_assets
  DROP CONSTRAINT IF EXISTS media_assets_kind_check;

ALTER TABLE tv_dashboard.media_assets
  ADD CONSTRAINT media_assets_kind_check
  CHECK (media_kind IN ('image', 'video', 'font'));
