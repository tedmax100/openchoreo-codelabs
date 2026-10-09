summary: 理解 Environment、DeploymentPipeline 與 ReleaseBinding,為每個環境設定不同的副本數與環境變數,並把同一個 Release 從 development 晉升到 staging、production
id: openchoreo-05-environments-promotion
categories: openchoreo,kubernetes,ci-cd
environments: Web
status: Published
feedback link: https://github.com/openchoreo/openchoreo/issues
author: 雷N

# OpenChoreo 實戰 05:多環境與 Promotion

## 概覽
Duration: 2

「建置一次,到處部署」是交付的基本原則。OpenChoreo 用**不可變的 Release** 加上**每個環境一個 ReleaseBinding** 實現它:同一份產物在各環境以相同方式執行,只有環境專屬設定不同。

### 先決條件

* 已完成第 1 到 3 課(第 4 課不是必要)
* 叢集有 `development`、`staging`、`production` 三個環境(Quick Start 預設就有)

### 你會學到

* Environment、DeploymentPipeline 與 Project 的關係
* ReleaseBinding 的結構:釘選 Release、環境覆寫
* 為 staging、production 手動建立 ReleaseBinding
* 觀察「dev 自動更新、其他環境維持釘選」
* 晉升(promotion)與回滾,本質上只是修改 `releaseName`

## 先備知識:環境、不可變制品與晉升
Duration: 8

### 為什麼需要多個環境?

| 環境 | 目的 | 典型特徵 |
|---|---|---|
| development | 開發者快速試錯 | 資源少、容許不穩定 |
| staging | 上線前的完整演練 | 盡量和 production 相似 |
| production | 真正服務使用者 | 高可用、嚴格管控 |

變更先在較低風險的環境驗證,再往前推,這個過程叫**晉升(promotion)**。

### 設定與程式碼分離

業界著名的 **Twelve-Factor App** 方法論有一條原則:**把設定放在環境裡,不要寫死在程式碼中**。理由是同一份程式碼會在不同環境執行,只有「資料庫位址、日誌等級、副本數」這類設定不同。

OpenChoreo 把這個原則做成制度:

| 內容 | 放哪裡 | 為什麼 |
|---|---|---|
| 跨環境一致的(映像、埠、元件類型) | Component / Workload | 每個環境都一樣,才有可比性 |
| 每個環境不同的(副本數、環境變數) | ReleaseBinding | 只改這裡,不動程式碼 |

### 不可變(Immutable)制品

**不可變**的意思是:一旦產生,內容就永遠不變。想改,就產生一個**新的**。

好處:

* **可重現**:「production 跑的 Release A」就是一個確定的東西
* **可回滾**:舊版本還在,切回去就好
* **可審計**:可以回答「那天到底部署了什麼」

OpenChoreo 的 ComponentRelease 就是這樣的不可變快照,它的名稱尾碼是內容雜湊,內容一變雜湊就變。

### Release 與 ReleaseBinding 的比喻

可以想像成**書與書店**:

| OpenChoreo | 比喻 |
|---|---|
| ComponentRelease | 一本書的某個「版次」(第一版、第二版),印出來就不改 |
| Environment | 不同的書店(實體店、網路書店、直營店) |
| ReleaseBinding | 「這家書店目前上架第幾版」的紀錄 |
| 晉升 | 把某家書店的上架版次,改成較新的一版 |
| 回滾 | 改回舊版次 |

這樣你就能理解:**晉升不是重新建置、重新打包,只是改變指標**。所以非常快、非常安全。

### DeploymentPipeline:有向圖

DeploymentPipeline 規定了「環境之間可以怎麼走」,本質上是一張**有向圖**:

```
development ──▶ staging ──▶ production
```

它的價值是**強制流程**:例如規定 production 只能從 staging 來,不能從 development 直接跳過去。Project 透過 `deploymentPipelineRef` 選擇使用哪一條管線,所以同一個 Project 的所有元件遵守同一套流程。

### 兩種「自動」

* `autoDeploy`:新 Release 自動套用到**第一個環境**
* 之後的環境:需要**明確的晉升動作**(人或自動化流程決定)

這個設計讓「快速迭代」與「謹慎上線」並存。

Positive
: 接下來你會親手驗證這些概念:建立三個環境的綁定、讓 development 前進而其他環境不動、再做晉升與回滾。

## 環境與部署管線
Duration: 5

### 看看你的環境

```bash
kubectl get environment -n default
kubectl get deploymentpipeline -n default default -o yaml
```

預設會有三個 Environment,其中 `production` 標記為 `isProduction: true`。DeploymentPipeline 的重點是 `promotionPaths`:

```yaml
spec:
  promotionPaths:
  - sourceEnvironmentRef:
      kind: Environment
      name: development
    targetEnvironmentRefs:
    - kind: Environment
      name: staging
  - sourceEnvironmentRef:
      kind: Environment
      name: staging
    targetEnvironmentRefs:
    - kind: Environment
      name: production
```

這就是一張「有向圖」:development → staging → production。

### Project 如何選擇管線

```bash
kubectl get project default -n default -o jsonpath='{.spec}'
```

你會看到 `deploymentPipelineRef: {kind: DeploymentPipeline, name: default}`。**同一個 Project 內的所有 Component 共用同一條管線**。

| 資源 | 誰維護 | 作用 |
|---|---|---|
| Environment | 平台工程師 | 一個部署階段,綁定一個 DataPlane |
| DeploymentPipeline | 平台工程師 | 定義環境間可以怎麼晉升 |
| ReleaseBinding | 開發者/自動化 | 把某個 Release 釘在某個環境,並帶環境覆寫 |

## 部署到 development
Duration: 4

沿用第 3 課的映像,建立 `promo-demo.yaml`:

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: Component
metadata:
  name: promo-demo
  namespace: default
spec:
  owner:
    projectName: default
  autoDeploy: true
  componentType:
    kind: ClusterComponentType
    name: deployment/service
---
apiVersion: openchoreo.dev/v1alpha1
kind: Workload
metadata:
  name: promo-demo-workload
  namespace: default
spec:
  owner:
    componentName: promo-demo
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

```bash
kubectl apply -f promo-demo.yaml
kubectl wait --for=condition=Ready component/promo-demo -n default --timeout=60s
kubectl get releasebinding -n default | grep promo
```

只有 `promo-demo-development` 被自動建立。因為 `autoDeploy: true` 只會部署到管線的**第一個環境**。

記下目前的 Release 名稱:

```bash
kubectl get component promo-demo -n default -o jsonpath='{.status.latestRelease.name}{"\n"}'
```

下面以 `RELEASE1` 代表它。

## 認識 ReleaseBinding
Duration: 4

看看 development 自動產生的 ReleaseBinding:

```bash
kubectl get releasebinding promo-demo-development -n default -o yaml
```

重要欄位:

| 欄位 | 意義 |
|---|---|
| `spec.environment` | 綁定的環境 |
| `spec.owner` | 屬於哪個 Component |
| `spec.releaseName` | **釘選**的 ComponentRelease |
| `spec.state` | `Active` 表示部署中 |
| `spec.componentTypeEnvironmentConfigs` | 覆寫 ComponentType 的環境參數(例如 `replicas`) |
| `spec.workloadOverrides.container.env` | 覆寫容器環境變數 |

Positive
: 第 2 課說過:跨環境一致的值放 Component 的 Parameters,**環境專屬的值放 ReleaseBinding**。這就是為什麼同一個 Release 可以在 staging 跑 2 個副本、在 production 跑 1 個,卻不用改 Component。

## 建立 staging 與 production
Duration: 6

建立 `promo-staging.yaml`,把 `RELEASE1` 換成你的 Release 名稱:

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: ReleaseBinding
metadata:
  name: promo-demo-staging
  namespace: default
spec:
  environment: staging
  owner:
    componentName: promo-demo
    projectName: default
  releaseName: RELEASE1
  state: Active
  componentTypeEnvironmentConfigs:
    replicas: 2
  workloadOverrides:
    container:
      env:
        - key: LOG_LEVEL
          value: warn
```

再建立 `promo-prod.yaml`,環境改成 `production`,名稱改成 `promo-demo-production`,`replicas: 1`,`LOG_LEVEL` 設為 `error`。然後套用:

```bash
kubectl apply -f promo-staging.yaml -f promo-prod.yaml
kubectl wait --for=condition=Available deploy -A -l openchoreo.dev/component=promo-demo --timeout=200s
```

### 驗證三個環境

```bash
kubectl get deploy -A | grep promo
```

預期 staging 是 `2/2`,development 與 production 是 `1/1`。

環境變數被放進各環境的 ConfigMap:

```bash
for ns in development staging production; do
  kubectl get cm -A -o jsonpath='{range .items[*]}{.metadata.namespace}{" "}{.metadata.name}{" "}{.data}{"\n"}{end}' \
    | grep "promo-demo-$ns-env-configs"
done
```

預期分別看到 `{"LOG_LEVEL":"debug"}`(若尚未改動則是 `info`)、`warn`、`error`。

呼叫三個環境(主機名稱格式 `{環境}-default.openchoreoapis.localhost`):

```bash
for e in development staging production; do
  curl -s http://$e-default.openchoreoapis.localhost:19080/promo-demo-http/greeter/greet; echo " <- $e"
done
```

Negative
: 本課是手寫 ReleaseBinding,為了讓你看清楚結構,所以 `kubectl apply` 不會檢查是否符合 DeploymentPipeline 的晉升路徑。實務上建議用 `occ component deploy --to` 或 GitOps 流程,讓管線規則發揮作用(見最後一節)。

## 新版本:dev 前進,其他環境不動
Duration: 5

修改程式的設定,產生新的 Release:

```bash
sed -i 's/value: "info"/value: "debug"/' promo-demo.yaml
kubectl apply -f promo-demo.yaml
sleep 10
kubectl get component promo-demo -n default -o jsonpath='{.status.latestRelease.name}{"\n"}'
kubectl get releasebinding -n default \
  -o custom-columns=NAME:.metadata.name,ENV:.spec.environment,RELEASE:.spec.releaseName | grep -E 'NAME|promo'
```

預期結果:

| ReleaseBinding | Release |
|---|---|
| promo-demo-development | **新的** `RELEASE2` |
| promo-demo-staging | 仍是 `RELEASE1` |
| promo-demo-production | 仍是 `RELEASE1` |

Positive
: 這就是「釘選」的價值:你可以在 development 反覆迭代,staging 與 production 不受影響,直到你明確決定晉升。

## 晉升與回滾
Duration: 5

**晉升 = 把下一個環境的 `releaseName` 指向新的 Release。** 把 `RELEASE2` 換成上一節看到的新名稱:

```bash
kubectl patch releasebinding promo-demo-staging -n default \
  --type merge -p '{"spec":{"releaseName":"RELEASE2"}}'
sleep 15
kubectl get releasebinding -n default \
  -o custom-columns=NAME:.metadata.name,RELEASE:.spec.releaseName | grep -E 'NAME|promo'
```

staging 現在跟 development 同版本,但**環境覆寫沒有消失**:staging 仍然是 2 個副本、`LOG_LEVEL=warn`。

### 回滾

回滾只是把釘選改回去:

```bash
kubectl patch releasebinding promo-demo-staging -n default \
  --type merge -p '{"spec":{"releaseName":"RELEASE1"}}'
kubectl get releasebinding promo-demo-staging -n default \
  -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}{"\n"}'
```

預期看到 `ReleaseBinding is ready`。因為 Release 不可變,回滾得到的和當初部署的**完全一樣**。

### 用 occ 晉升

`occ` 也提供晉升指令(依 `occ component deploy --help`):

```bash
# 部署最新 Release 到管線的第一個環境
occ component deploy promo-demo --namespace default --project default

# 晉升到下一個環境
occ component deploy promo-demo --namespace default --project default --to staging
```

Negative
: `occ` 需要先 `occ login`(會開瀏覽器)。本課的 `occ` 指令是依 `--help` 說明整理,沒有實際執行。還有 `occ releasebinding generate` 可以產生 ReleaseBinding 的 YAML,適合搭配 GitOps(第 6 課)。

## 清理
Duration: 1

```bash
kubectl delete releasebinding promo-demo-staging promo-demo-production -n default
kubectl delete -f promo-demo.yaml --ignore-not-found
```

## 自我檢核
Duration: 4

試著不看上文回答下面的問題;答不出來的,回頭看對應的章節。

1. 為什麼說「晉升不是重新建置」?

2. `autoDeploy` 會把新 Release 部署到哪些環境?

3. 跨環境一致的內容與每環境不同的內容,各放在哪?

4. production 出問題,想回到上一版怎麼做?

### 參考答案

1. Release 是不可變快照,晉升只是把下一個環境的 `releaseName` 指向它,所以快速、可重現、可回滾。

2. 只會部署到管線的第一個環境;之後的環境需要明確的晉升。

3. 一致的放 Component / Workload;每環境不同的(副本數、環境變數)放 ReleaseBinding。

4. 把 production 的 ReleaseBinding 的 `releaseName` 改回舊的 Release 名稱。

## 恭喜與下一步
Duration: 1

你已經:

* ✅ 看懂 Environment → DeploymentPipeline → Project 的關係
* ✅ 為每個環境手寫 ReleaseBinding 並設定不同的副本數與環境變數
* ✅ 驗證了 Release 釘選:dev 前進,其他環境不動
* ✅ 完成晉升與回滾

### 重點整理

| 概念 | 一句話 |
|---|---|
| Release | 不可變的版本,建置一次 |
| ReleaseBinding | 把 Release 釘在環境,並帶環境覆寫 |
| 晉升 | 修改下一個環境的 `releaseName` |
| 回滾 | 把 `releaseName` 改回舊值 |

### 下一課

**06:GitOps** — 不再手動 `kubectl patch`,把 ReleaseBinding 放進 Git,由 Argo CD 同步。
