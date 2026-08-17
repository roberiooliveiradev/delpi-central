-- Amplia o catálogo compartilhado de transições sem alterar migrations aplicadas.

ALTER TABLE tv_dashboard.playlists
  DROP CONSTRAINT IF EXISTS playlists_transition_style_check;

ALTER TABLE tv_dashboard.playlists
  ADD CONSTRAINT playlists_transition_style_check
  CHECK (
    transition_style IN (
      'fade', 'dissolve', 'slide', 'push', 'wipe', 'zoom', 'none'
    )
  );

ALTER TABLE tv_dashboard.slides
  DROP CONSTRAINT IF EXISTS slides_transition_style_check;

ALTER TABLE tv_dashboard.slides
  ADD CONSTRAINT slides_transition_style_check
  CHECK (
    transition_style IS NULL
    OR transition_style IN (
      'fade', 'dissolve', 'slide', 'push', 'wipe', 'zoom', 'none'
    )
  );

ALTER TABLE tv_dashboard.playlist_sections
  DROP CONSTRAINT IF EXISTS playlist_sections_transition_style_chk;

ALTER TABLE tv_dashboard.playlist_sections
  ADD CONSTRAINT playlist_sections_transition_style_chk
  CHECK (
    transition_style IS NULL
    OR transition_style IN (
      'fade', 'dissolve', 'slide', 'push', 'wipe', 'zoom', 'none'
    )
  );

