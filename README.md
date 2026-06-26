# FPV Kamikaze Drone — Server Stats

Real-time player statistics reader for FPV Kamikaze Drone dedicated server (Unreal Engine).

Reads player data (Kills, Deaths, Assists, Score, Nickname, EOS User ID) directly from server process memory and stores cumulative stats in MariaDB/MySQL. Includes a PHP web interface for displaying the leaderboard.

## How it works

The Python script reads `/proc/PID/mem` of the game server process, finds `BP_PlayerState` objects by scanning for FString pointer patterns, and extracts player statistics from known offsets.

### Memory layout (BP_PlayerState)

| Offset | Type | Field |
|--------|------|-------|
| 0x000 | int32 | Kills |
| 0x004 | int32 | Deaths |
| 0x008 | int32 | Assists |
| 0x00C | int32 | Score |
| 0x148 | FString | PlayerName |
| 0x158 | FString | UserId (EOS) |

### Detection method

1. Auto-detects game process PID by scanning `/proc/*/comm` and `/proc/*/cmdline`
2. Auto-detects memory address range from `/proc/PID/maps`
3. Scans memory for FString pointer pattern (two consecutive FString headers at offsets 0x148 and 0x158)
4. Validates objects: checks K/D/A/S ranges, name regex, EOS UID format
5. Deduplicates multiple copies by selecting the object with highest activity
6. Caches last known values to smooth out transient memory states
7. Sends delta updates to MariaDB

## Requirements

- Ubuntu 22.04+ / Debian 12+
- Python 3.10+
- MariaDB / MySQL
- Nginx + PHP-FPM
- pymysql (`pip install pymysql`)
- Root access (for `/proc/PID/mem`)

## Installation

```bash
git clone https://github.com/your-repo/fpv-stats.git
cd fpv-stats
chmod +x install.sh
sudo ./install.sh
```

Configure Nginx to serve PHP from `/var/www/html/`.

## Configuration

Edit `fpv_live.py`:

- `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME` — database credentials
- `INTERVAL` — update interval in seconds (default: 3.0)
- `CACHE_FILE` — path to UID cache JSON

Edit `index.php`:

- Database credentials in `new mysqli(...)` call

## Usage

```bash
python3 /opt/fpv_live.py              # auto-detect PID
python3 /opt/fpv_live.py 444          # manual PID
python3 /opt/fpv_live.py 444 5        # manual PID + 5s interval
```

### Systemd service

```bash
systemctl start fpv-stats
systemctl stop fpv-stats
systemctl status fpv-stats
journalctl -u fpv-stats -f            # live logs
```

## Files

| File | Description |
|------|-------------|
| `fpv_live.py` | Main stats reader script |
| `index.php` | Web leaderboard page |
| `fpv-stats.service` | Systemd service unit |
| `setup.sql` | Database schema and user setup |
| `install.sh` | Automated installer |

## License

MIT
