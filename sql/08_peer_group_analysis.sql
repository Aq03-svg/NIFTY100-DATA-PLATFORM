SELECT
    peer_group_name,
    COUNT(*) AS companies
FROM peer_groups
GROUP BY peer_group_name
ORDER BY companies DESC;