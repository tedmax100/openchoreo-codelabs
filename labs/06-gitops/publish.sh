#!/usr/bin/env bash
# 把 ./repo 推到叢集內的 git-server(http://git-server.codelab-git.svc.cluster.local/codelab-gitops.git)
set -euo pipefail
CTX=${CTX:-k3d-openchoreo}
cd "$(dirname "$0")"
# 第一次執行時,從範本複製出可 commit 的工作目錄 ./repo
[ -d repo ] || cp -r repo-template repo
[ -e repo/.git ] || git -C repo init -q -b main
git -C repo add -A
git -C repo -c user.name=lab -c user.email=lab@example.com commit -q -m "${1:-update}" || echo "nothing to commit"
rm -rf /tmp/codelab-gitops.git && git clone -q --bare repo /tmp/codelab-gitops.git
git -C /tmp/codelab-gitops.git update-server-info
POD=$(kubectl --context $CTX -n codelab-git get pod -l app=git-server -o jsonpath='{.items[0].metadata.name}')
kubectl --context $CTX -n codelab-git exec "$POD" -- rm -rf /srv/git/codelab-gitops.git
kubectl --context $CTX -n codelab-git cp /tmp/codelab-gitops.git "$POD":/srv/git/codelab-gitops.git
echo "published $(git -C repo rev-parse --short HEAD)"
