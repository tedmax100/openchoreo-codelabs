#!/usr/bin/env bash
# 重建所有教學:檢查 callout 格式 → 匯出 HTML → 套用主題 → 產生首頁
# 需要 claat(go install github.com/googlecodelabs/tools/claat@latest)
set -euo pipefail
cd "$(dirname "$0")"
CLAAT=${CLAAT:-$(command -v claat || echo "$HOME/go/bin/claat")}
python3 lint_callouts.py tutorials/*.md
mkdir -p generated
cp -r claat-public generated/
for f in tutorials/*.md; do "$CLAAT" export -o generated "$f" | tail -1; done
python3 apply_devsite_theme.py > /dev/null
python3 build_index.py
