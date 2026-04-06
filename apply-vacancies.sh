#!/bin/bash
set -euo pipefail

/usr/local/bin/python -m hh_applicant_tool apply-vacancies \
  -L /app/letter.txt \
  -f \
  --send-email \
  --excluded-filter 'junior|стажировк|bitrix|ddd|web3|crypto|blockchain|дружн\w+коллектив|полиграф|open\s*space|опенспейс|хакатон|конкурс|тестов\w+ задан|soft skill'
