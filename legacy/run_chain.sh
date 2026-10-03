#!/bin/bash
cd "C:/Users/Saaket Vedarth/Valence_backup"
echo "=== WAIT optimizer ==="
while pgrep -f optimize_clusters >/dev/null 2>&1 || ps -W 2>/dev/null | grep -i "python.*optimize" >/dev/null; do sleep 5; done
echo "=== OPTIMIZER DONE ==="
cat optimize_run.log | tail -30
echo "=== NAME archetypes ==="
python -W ignore name_archetypes.py 2>&1 | tail -30
echo "=== VERIFY archetypes ==="
python -W ignore verify_archetypes.py 2>&1 | tail -50
echo "=== GRAND AUDIT ==="
python -W ignore grand_audit.py 2>&1 | tail -80
echo "=== DONE ==="
