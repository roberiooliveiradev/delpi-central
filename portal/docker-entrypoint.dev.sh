#!/bin/sh
set -e

cd /app

# Volume anônimo /app/node_modules persiste entre rebuilds; sincroniza deps novas.
npm install

exec npm run dev -- --host
