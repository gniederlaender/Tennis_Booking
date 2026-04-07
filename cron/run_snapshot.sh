#!/bin/bash
# Ad-hoc script to run availability snapshot update
# Usage: ./cron/run_snapshot.sh

cd /opt/Tennis_Booking
source venv/bin/activate
python cron/update_snapshots.py
