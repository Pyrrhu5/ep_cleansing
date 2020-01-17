-- Path
~/.kodi/userdata/Database/MyVideos116.db

-- TvShows list
SELECT 
	ep.idShow 				AS id,
	DISTINCT(ep.strTitle) 	AS title
FROM episode_view 			ep

-- WhiteList
SELECT
	ep.c18 AS file_path
FROM
	episode_view ep 
WHERE 
		ep.playCount >= 1
	AND ep.idShow NOT IN (5, 8, 11, 16) -- insert white list
