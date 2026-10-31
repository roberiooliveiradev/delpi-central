#!/bin/bash
while true; do
  OUT=$(docker exec delia-t21-main sh -c 'cd /app/.battery/task21 2>/dev/null && for f in *_run*.log; do printf "%s=%s " "$f" "$(grep -c "\"s\"" "$f" 2>/dev/null)"; done; tail -1 driver.log' 2>/dev/null | tr '\n' ' ')
  echo "$(date +%H:%M) $OUT" >> /tmp/t21_progress.txt
  sleep 300
done
