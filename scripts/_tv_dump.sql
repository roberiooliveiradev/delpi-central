\t on
SELECT json_build_object('src','slides','id',id::text,'name',title,'pl',playlist_id::text,'doc',native_config)::text FROM tv_dashboard.slides WHERE native_config IS NOT NULL;
SELECT json_build_object('src','playlists.master','id',id::text,'name',name,'pl',NULL,'doc',master_config)::text FROM tv_dashboard.playlists WHERE master_config IS NOT NULL;
SELECT json_build_object('src','playlists.defaults','id',id::text,'name',name,'pl',NULL,'doc',data_defaults)::text FROM tv_dashboard.playlists WHERE data_defaults IS NOT NULL;
SELECT json_build_object('src','playlist_sections','id',id::text,'name',name,'pl',playlist_id::text,'doc',master_config)::text FROM tv_dashboard.playlist_sections WHERE master_config IS NOT NULL;
SELECT json_build_object('src','slide_templates','id',id::text,'name',label,'pl',NULL,'doc',native_config)::text FROM tv_dashboard.slide_templates WHERE native_config IS NOT NULL;
SELECT json_build_object('src','playlist_history','id',id::text,'name',NULL,'pl',playlist_id::text,'doc',snapshot)::text FROM tv_dashboard.playlist_history WHERE snapshot IS NOT NULL;
SELECT json_build_object('src','gpt_actions_idem','id',id::text,'name',operation,'pl',NULL,'doc',response_snapshot)::text FROM tv_dashboard.gpt_actions_idempotency_keys WHERE response_snapshot IS NOT NULL;
