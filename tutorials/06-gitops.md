summary: 把 OpenChoreo 的 Component 與 Workload 放進 Git,由 Argo CD 自動同步,體驗修改即部署與漂移自動還原
id: openchoreo-06-gitops
categories: openchoreo,kubernetes,gitops
environments: Web
status: Published
feedback link: https://github.com/openchoreo/openchoreo/issues
author: 雷N

# OpenChoreo 實戰 06:GitOps

## 概覽
Duration: 2

前幾課我們都用 `kubectl apply` 手動部署。這一課把「期望狀態」放進 Git,讓 Argo CD 持續把叢集調和成 Git 的樣子。

### 為什麼 OpenChoreo 很適合 GitOps?

OpenChoreo 的所有資源(Project、Component、Workload…)都是 Kubernetes CRD,所以任何 GitOps 工具都能直接同步它們,不需要特別的整合。

### 先決條件

* 已完成第 1 到 3 課
* 叢集已安裝 Argo CD(`argocd` namespace)。第 1 課的 k3d 環境若沒有,請參考 [Argo CD 安裝文件](https://argo-cd.readthedocs.io/en/stable/getting_started/)
* 本機有 `git`

### 你會學到

* 在叢集內架一個簡易 Git 伺服器
* 建立 Argo CD Application 指向 Git repo
* 修改 Git → 自動部署
* 手動改叢集 → 被 selfHeal 還原

## 先備知識:GitOps 是什麼?
Duration: 8

### 從「手動部署」說起

到目前為止,我們都是自己在終端機執行 `kubectl apply`。這在實驗時很方便,但在團隊裡會遇到問題:

* 誰在什麼時候改了什麼?不知道
* 有人偷偷 `kubectl edit` 了線上環境,和文件不一致(**設定漂移**,configuration drift)
* 壞掉了想回到昨天的狀態?要靠記憶
* 部署權限要發給每一個人的電腦

### GitOps 的四個原則

GitOps(OpenGitOps 社群定義的原則)主張:

| 原則 | 意思 |
|---|---|
| **宣告式** | 系統的期望狀態用宣告方式描述 |
| **版本化且不可變** | 期望狀態存在 Git,有完整歷史,不能偷改 |
| **自動拉取** | 軟體代理人自動從 Git 取得最新期望狀態 |
| **持續調和** | 代理人持續比對實際與期望,發現差異就修正 |

一句話:**Git 是唯一的真實來源(single source of truth)**,叢集只是 Git 的反映。

### 推送式 vs 拉取式部署

| | 推送式(傳統 CI/CD) | 拉取式(GitOps) |
|---|---|---|
| 誰動手 | CI 系統執行 `kubectl apply` | 叢集內的代理人自己去 Git 拉 |
| 叢集憑證 | 必須交給 CI 系統 | 留在叢集內,不外流 |
| 發現漂移 | 通常不會 | 持續比對,自動發現 |
| 回滾 | 重跑舊的流水線 | `git revert`,代理人自動套用 |

### Argo CD 的核心名詞

| 名詞 | 說明 |
|---|---|
| **Application** | 一個「Git 的某個目錄 → 叢集的某個 namespace」的對應關係 |
| **Sync(同步)** | 把叢集調整成 Git 的樣子 |
| **Synced / OutOfSync** | 叢集和 Git 一致 / 不一致 |
| **Health** | 資源本身是否健康(例如 Deployment 是否就緒) |
| **selfHeal** | 叢集被手動改了,自動還原 |
| **prune** | Git 裡刪掉的檔案,叢集裡的資源也刪掉 |

注意 **Sync 與 Health 是兩件事**:Synced 只代表「和 Git 一致」,不代表應用正常運作。

### 兩層調和迴圈

這一課很有趣,因為有**兩個**調和迴圈疊在一起:

```
Git ──(Argo CD 調和)──▶ 叢集裡的 Component/Workload ──(OpenChoreo 控制器調和)──▶ Deployment/Service …
```

* Argo CD 負責「Git → OpenChoreo 資源」
* OpenChoreo 控制器負責「OpenChoreo 資源 → Kubernetes 資源」

兩者都是第 2 課說的「宣告期望狀態、持續調和」,所以能無縫銜接。

### 為什麼 ReleaseBinding 不好放進 Git?

ReleaseBinding 的 `releaseName` 帶有內容雜湊(如 `hello-gitops-65f6b7d6b6`),是控制器**在 Git 之外**產生的,你無法事先寫在檔案裡。完整的 GitOps 流程需要工具先把這類檔案產生出來再提交,這也是 OpenChoreo 提供 `occ releasebinding generate` 的原因。本課聚焦在 Component 與 Workload。

準備好實驗檔案吧。

## 準備實驗檔案
Duration: 3

本課的檔案放在 `codelabs/labs/06-gitops/`:

```
06-gitops/
├── git-server.yaml     # 叢集內的 Git 伺服器
├── publish.sh          # 把 ./repo 推到 Git 伺服器
├── application.yaml    # Argo CD Application
├── repo-template/apps/hello-gitops/   # 範本
│   ├── component.yaml
│   └── workload.yaml
└── repo/                              # 第一次執行 publish.sh 時由範本複製,並初始化為 git repo
```

### Git 裡放什麼?

`repo/apps/hello-gitops/component.yaml`:

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: Component
metadata:
  name: hello-gitops
  namespace: default
spec:
  owner:
    projectName: default
  autoDeploy: true
  componentType:
    kind: ClusterComponentType
    name: deployment/service
```

`repo/apps/hello-gitops/workload.yaml`:

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: Workload
metadata:
  name: hello-gitops-workload
  namespace: default
spec:
  owner:
    componentName: hello-gitops
    projectName: default
  endpoints:
    http:
      type: HTTP
      port: 9090
      visibility: [external]
  container:
    image: "ghcr.io/openchoreo/samples/greeter-service:latest"
    command:
      - ./go-greeter
    args:
      - --port
      - "9090"
    env:
      - key: LOG_LEVEL
        value: "info"
```

這和第 3 課的 YAML 幾乎一樣,差別只是它現在住在 Git 裡。

Positive
: 為什麼不把 ReleaseBinding 也放進 Git?因為 ReleaseBinding 的 `releaseName` 是控制器依內容雜湊產生的(例如 `hello-gitops-65f6b7d6b6`),事先寫不出來。OpenChoreo 另外提供 `occ releasebinding generate` 來產生這類檔案,適合搭配完整的 GitOps 目錄結構,本課不涵蓋。

## 架設 Git 伺服器
Duration: 5

為了讓實驗不依賴外部服務,我們在叢集內用 nginx + `git-http-backend` 架一個簡易 Git 伺服器(`git-server.yaml`)。核心是它的啟動腳本:

```bash
apk add --no-cache git git-daemon fcgiwrap spawn-fcgi
test -x /usr/libexec/git-core/git-http-backend
```

Negative
: **注意套件名稱。** `git-daemon` 這個套件很關鍵:新版 Alpine 把 `git-http-backend` 拆到 `git-daemon`,只裝 `git` 的話 nginx 會對所有請求回 `403 Forbidden`,Argo CD 就會報 `failed to list refs: authorization failed: 403 Forbidden`。我們的啟動腳本用 `test -x` 在缺少時直接讓 Pod 失敗,比靜默出錯更容易發現。

另一個陷阱:這個伺服器用 `emptyDir` 存放 repo,**Pod 一重建 repo 就消失**,Argo CD 會報同樣的 403。僅供實驗,不要用於正式環境。

套用:

```bash
cd codelabs/labs/06-gitops
kubectl apply -f git-server.yaml
kubectl wait --for=condition=Available deploy/git-server -n codelab-git --timeout=180s
```

## 發佈 repo 並建立 Application
Duration: 5

`publish.sh` 會初始化 `./repo` 為 Git repo、commit,再打包成 bare repo 複製進 Git 伺服器:

```bash
./publish.sh "add hello-gitops"
```

查看 `application.yaml`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: hello-gitops
  namespace: argocd
spec:
  project: default
  source:
    repoURL: http://git-server.codelab-git.svc.cluster.local/codelab-gitops.git
    targetRevision: main
    path: apps/hello-gitops
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

| 欄位 | 意義 |
|---|---|
| `source.repoURL / path` | 從哪個 repo、哪個目錄讀取期望狀態 |
| `destination.namespace` | 套用到哪個 namespace |
| `automated` | 偵測到差異就自動同步,不用手動按 Sync |
| `prune: true` | Git 裡刪掉的資源,叢集也刪 |
| `selfHeal: true` | 叢集被手動改動時,自動還原成 Git 的樣子 |

套用並觀察:

```bash
kubectl apply -f application.yaml
sleep 30
kubectl get application hello-gitops -n argocd
kubectl get component,workload -n default | grep hello
```

預期 `Synced` 與 `Healthy`,並看到由 Git 建立的 Component 和 Workload。

Positive
: 你沒有執行任何 `kubectl apply` 去建立 Component。它是 Argo CD 從 Git 讀出來、套用到叢集的。

## 改 Git,觸發部署
Duration: 5

先記下目前的 Release:

```bash
kubectl get component hello-gitops -n default -o jsonpath='{.status.latestRelease.name}{"\n"}'
```

把 `LOG_LEVEL` 改成 `debug`,commit 並發佈:

```bash
sed -i 's/value: "info"/value: "debug"/' repo/apps/hello-gitops/workload.yaml
./publish.sh "set LOG_LEVEL=debug"
```

Argo CD 預設每 3 分鐘輪詢一次 Git。為了不等,手動要求重新整理:

```bash
kubectl annotate application hello-gitops -n argocd argocd.argoproj.io/refresh=hard --overwrite
sleep 20
kubectl get workload hello-gitops-workload -n default -o jsonpath='{.spec.container.env}{"\n"}'
kubectl get component hello-gitops -n default -o jsonpath='{.status.latestRelease.name}{"\n"}'
```

預期 `LOG_LEVEL` 變成 `debug`,而且 `latestRelease` 變成新的名稱:Git 的變更 → Workload 更新 → OpenChoreo 產生新的 ComponentRelease → 自動部署到 development。

Positive
: 整條鏈是 **Git commit → Argo CD → OpenChoreo 控制器 → Release → Data Plane**。你只做了最前面的一步。

## 漂移與 selfHeal
Duration: 4

模擬有人直接動叢集(俗稱 configuration drift):

```bash
kubectl patch workload hello-gitops-workload -n default --type json \
  -p '[{"op":"replace","path":"/spec/container/env/0/value","value":"error"}]'
kubectl get workload hello-gitops-workload -n default -o jsonpath='{.spec.container.env[0].value}{"\n"}'
```

這時會看到 `error`。等 20 秒再看:

```bash
sleep 20
kubectl get workload hello-gitops-workload -n default -o jsonpath='{.spec.container.env[0].value}{"\n"}'
kubectl get application hello-gitops -n argocd
```

預期值被還原成 `debug`(Git 裡的值),Application 仍是 `Synced`。

Positive
: 這就是 GitOps 的好處:**Git 是唯一的真實來源**。任何未經 Git 的手動修改都會被撤銷,也留下了完整、可審計、可回溯的變更歷史。

## 刪除與 prune
Duration: 3

`prune: true` 的意思是:從 Git 刪掉檔案,Argo CD 會把對應資源從叢集刪掉。

```bash
git -C repo rm -r apps/hello-gitops
./publish.sh "remove hello-gitops"
kubectl annotate application hello-gitops -n argocd argocd.argoproj.io/refresh=hard --overwrite
sleep 20
kubectl get component,workload -n default | grep hello || echo "pruned"
```

Negative
: 這一段是依 Argo CD 的 `prune` 語意撰寫,作者實測環境中沒有執行這個步驟。如果你的結果不同,請檢查 Application 的 `syncPolicy.automated.prune`,以及 Argo CD 是否因為「刪除所有資源」而停止自動 prune。

## 清理
Duration: 2

先刪 Application,否則 selfHeal 會把資源重建:

```bash
kubectl delete application hello-gitops -n argocd
kubectl delete component hello-gitops -n default --ignore-not-found
kubectl delete namespace codelab-git
```

## 自我檢核
Duration: 4

試著不看上文回答下面的問題;答不出來的,回頭看對應的章節。

1. GitOps 的「拉取式」相比「推送式」有什麼好處?

2. `selfHeal` 與 `prune` 分別做什麼?

3. Synced 且 Healthy 就代表應用一定正常嗎?

4. 本課為什麼不把 ReleaseBinding 放進 Git?

### 參考答案

1. 叢集憑證不必交給外部 CI;代理人持續比對能發現漂移;回滾可用 `git revert`。

2. selfHeal:叢集被手動修改時自動還原成 Git 的狀態。prune:Git 中刪除的檔案,叢集裡對應資源也刪除。

3. 不一定。Synced 只代表與 Git 一致,Health 是資源本身狀態,兩者是不同的事。

4. 它的 `releaseName` 含內容雜湊,由控制器在 Git 之外產生,無法事先寫入檔案。

## 恭喜與下一步
Duration: 1

你已經:

* ✅ 把 OpenChoreo 資源放進 Git,由 Argo CD 同步
* ✅ 體驗了「改 Git 就部署」
* ✅ 驗證了 selfHeal 會還原手動漂移
* ✅ 認識了自架 Git 伺服器的兩個陷阱

### 延伸閱讀

* [Argo CD Automated Sync Policy](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/)
* [OpenChoreo 文件](https://openchoreo.dev/docs/)

### 下一課

**07:可觀測性** — 啟用 Observability Plane,查看日誌、指標與追蹤。
