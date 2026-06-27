<?php
$db = new mysqli('127.0.0.1', 'fpv', 'fpv_pass_2026', 'fpv_stats');
$db->set_charset('utf8mb4');
$rows = $db->query("SELECT nickname, kills, deaths, assists, score FROM players ORDER BY kills DESC, score DESC");
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FPV STATS — Статистика</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#e0e0e0;font-family:'Segoe UI',Arial,sans-serif;padding:10px}
h1{text-align:center;color:#ff6600;font-size:22px;margin-bottom:6px;text-transform:uppercase;letter-spacing:2px}
.sub{text-align:center;color:#888;font-size:12px;margin-bottom:16px}
.table-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}
table{width:100%;max-width:900px;margin:0 auto;border-collapse:collapse;min-width:360px}
thead th{background:#1a1a1a;color:#ff6600;padding:8px 6px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:1px;border-bottom:2px solid #ff6600;white-space:nowrap}
thead th:nth-child(2){text-align:left}
tbody tr{border-bottom:1px solid #1a1a1a;transition:background 0.2s}
tbody tr:hover{background:#1a1a1a}
tbody tr:nth-child(odd){background:#111}
tbody tr:nth-child(1) td:first-child{color:#ffd700;font-weight:bold}
tbody tr:nth-child(2) td:first-child{color:#c0c0c0;font-weight:bold}
tbody tr:nth-child(3) td:first-child{color:#cd7f32;font-weight:bold}
td{padding:8px 6px;font-size:14px;text-align:center}
td:nth-child(2){text-align:left}
.name{color:#fff;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:120px;display:inline-block;vertical-align:middle}
.pos{color:#666;width:30px}
.kills{color:#4caf50}
.deaths{color:#f44336}
.assists{color:#2196f3}
.score-pos{color:#4caf50;font-weight:bold}
.score-neg{color:#f44336;font-weight:bold}
.score-zero{color:#666}
.footer{text-align:center;color:#444;font-size:11px;margin-top:16px}
@media(min-width:600px){
    body{padding:20px}
    h1{font-size:28px;margin-bottom:8px}
    .sub{font-size:14px;margin-bottom:30px}
    thead th{padding:12px 16px;font-size:14px}
    td{padding:10px 16px;font-size:15px}
    .name{max-width:200px}
    .footer{font-size:12px;margin-top:30px}
}
</style>
</head>
<body>
<h1>FPV STATS</h1>
<div class="sub">СТАТИСТИКА СЕРВЕРА</div>
<div class="table-wrap">
<table>
<thead>
<tr>
<th>N</th>
<th>NICKNAME</th>
<th>KILLS</th>
<th>DEATHS</th>
<th>ASSISTS</th>
<th>SCORE</th>
</tr>
</thead>
<tbody>
<?php
$n=1;
while($r=$rows->fetch_assoc()):
    $sc=$r['score'];
    $scClass=$sc>0?'score-pos':($sc<0?'score-neg':'score-zero');
?>
<tr>
<td class="pos"><?=$n++?></td>
<td><span class="name"><?=htmlspecialchars($r['nickname'])?></span></td>
<td class="kills"><?=$r['kills']?></td>
<td class="deaths"><?=$r['deaths']?></td>
<td class="assists"><?=$r['assists']?></td>
<td class="<?=$scClass?>"><?=$sc?></td>
</tr>
<?php endwhile;?>
</tbody>
</table>
</div>
<div class="footer">Внимание, статистика работает в тестовом режиме, возможны вайпы.<br>Статистика обновлена: <?=date('H:i:s')?></div>
</body>
</html>
