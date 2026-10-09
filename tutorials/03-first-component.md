summary: 安裝 occ CLI,撰寫 Component 與 Workload YAML,部署預建映像並追蹤 Release、ReleaseBinding 與路由
id: openchoreo-03-first-component
categories: openchoreo,kubernetes,deployment
environments: Web
status: Published
feedback link: https://github.com/openchoreo/openchoreo/issues
author: 雷N

# OpenChoreo 實戰 03:部署你的第一個 Component

## 概覽
Duration: 2

### 先決條件

* 已完成第 1、2 課,OpenChoreo 運行中
* `kubectl` 能連到叢集
* 本機有 `curl`

### 你會學到

* 安裝並登入 `occ` CLI
* 撰寫 Component 與 Workload 的 YAML
* 部署一個預建映像(不需要建置)
* 沿著 Component → ComponentRelease → ReleaseBinding → Kubernetes 資源追蹤部署
* 透過閘道呼叫服務

## 先備知識:從 Workload 到 Kubernetes 資源
Duration: 8

寫 YAML 之前,先搞清楚「我寫的東西」和「叢集裡真正跑的東西」是什麼關係。

### YAML 的基本結構

所有 Kubernetes 風格的資源,都有相同的四個頂層欄位:

```yaml
apiVersion: openchoreo.dev/v1alpha1   # 這個資源屬於哪個 API 與版本
kind: Component                       # 資源的種類
metadata:                             # 名稱、namespace、標籤等識別資訊
  name: my-greeter
spec:                                 # 你「期望」的內容
  ...
```

`status` 欄位則是控制器寫回來的**實際狀態**(你不用寫)。看到 `.status.conditions` 就是在讀它。

### 為什麼把 Component 和 Workload 分開?

這是 OpenChoreo 的核心設計之一:

| 資源 | 回答的問題 | 誰關心 |
|---|---|---|
| **Component** | 「這是什麼類型的東西?要怎麼被平台管理?」(what / how) | 平台與開發者共同 |
| **Workload** | 「我的程式需要什麼才能跑?」(要什麼映像、開哪個埠、依賴誰) | 開發者 |

Workload 只描述**需求**,不描述 Kubernetes 怎麼滿足。同一份 Workload,平台可以用不同的 ComponentType(模板)翻譯成不同的 Kubernetes 資源。

### 平台怎麼把它變成真正的資源

```
Workload(你寫的需求)  ┐
Component 的參數       ├──▶ ComponentType(平台寫的模板) ──▶ Deployment
環境設定(ReleaseBinding)┘                                   Service
                                                            HTTPRoute …
```

**ComponentType 像是一個「食譜」**:你提供食材(映像、埠、參數),食譜決定怎麼烹調(產生哪些資源、用什麼預設值)。所以你寫 30 行,平台能產生上百行的 Kubernetes 設定。這就是第 8 課要自己動手寫的東西。

### 流量怎麼進來:Gateway API

要讓外部連到服務,Kubernetes 需要「路由」。`Ingress` 是舊的標準,**Gateway API** 是新一代標準,OpenChoreo 用的是它。你會看到:

| 資源 | 角色 |
|---|---|
| **Gateway** | 流量入口(像大樓大門),由平台管理 |
| **HTTPRoute** | 路由規則:「某個主機名稱與路徑,轉到哪個 Service」 |

所以呼叫網址 `http://development-default.openchoreoapis.localhost:19080/my-greeter-http/greeter/greet` 可以拆成:

| 片段 | 意義 |
|---|---|
| `development-default` | 環境名稱 + namespace(用來區分主機名) |
| `.openchoreoapis.localhost` | 閘道的網域 |
| `:19080` | 本機閘道對外的 port |
| `/my-greeter-http` | 路徑前綴:元件名 + 端點名,HTTPRoute 依此比對 |
| `/greeter/greet` | 真正送給你應用程式的路徑(前綴會被剝掉) |

### 端點的可見度(visibility)

Workload 的每個端點都要宣告誰看得到它:

| 值 | 意義 |
|---|---|
| `external` | 經閘道對叢集外開放 |
| `project`(第 9 課實測) | 只有同一個 Project 內的元件能連 |

**預設不對外**是比較安全的設計,你必須明確寫出 `external` 才會產生對外路由。

### `autoDeploy` 的意思

`autoDeploy: true` 表示:Component 一建立或變更,平台就自動產生 Release 並部署到管線的**第一個環境**。第 5 課會說明 Release 是什麼。

### kubectl 與 occ 的分工

| 工具 | 定位 |
|---|---|
| `kubectl` | 通用:所有 Kubernetes 資源都能操作,本系列主要用它,因為最透明 |
| `occ` | OpenChoreo 專用:語意更高階(例如 `component deploy --to staging`),需要登入 |

下面開始動手。

## 安裝 occ CLI
Duration: 4

Linux x64(其他平台請見[官方頁面](https://openchoreo.dev/docs/getting-started/cli-installation/)):

```bash
curl -L https://github.com/openchoreo/openchoreo/releases/download/v1.3.1/occ_v1.3.1_linux_amd64.tar.gz | tar -xz && sudo mv occ /usr/local/bin/
occ version
```

### 設定 Control Plane 位址

本機 k3d 的位址是 `http://api.openchoreo.localhost:8080`:

```bash
occ config controlplane update default --url http://api.openchoreo.localhost:8080
```

在 `/etc/hosts` 加入(若主機尚未解析 `*.localhost`):

```
127.0.0.1       api.openchoreo.localhost
127.0.0.1       thunder.openchoreo.localhost
127.0.0.1       observer.openchoreo.localhost
```

### 登入

```bash
occ login
```

會開啟瀏覽器,使用 `admin@openchoreo.dev` / `Admin@123`。成功後試試:

```bash
occ namespace list
occ project list -n default
occ component list -n default
```

Negative
: 若你的叢集用自簽 TLS 憑證(非本機 k3d 預設),需先信任 CA,步驟見官方 CLI 安裝頁。

## 撰寫 YAML
Duration: 6

建立 `my-greeter.yaml`,內含 Component 與 Workload 兩個文件:

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: Component
metadata:
  name: my-greeter
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
  name: my-greeter-workload
  namespace: default
spec:
  owner:
    componentName: my-greeter
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

### 逐欄解讀

| 欄位 | 意義 |
|---|---|
| `spec.owner.projectName` | Component 屬於哪個 Project |
| `autoDeploy: true` | 建立後自動部署到第一個環境 |
| `componentType` | 用平台提供的 `deployment/service` 模板;`kind` 預設是 `ComponentType`,內建類型要明確寫 `ClusterComponentType` |
| `Workload.spec.owner` | 這個 Workload 屬於哪個 Component |
| `endpoints.http` | 宣告一個 HTTP 端點,port 9090,`visibility: [external]` 代表經閘道對外 |
| `container` | 映像、指令、參數與環境變數 |

Positive
: 官方範例 `greeter-service.yaml` 另外包含一個 `SecretReference`,用來注入 `GITHUB_TOKEN`。本課為了不依賴外部密鑰庫,刻意拿掉它。若服務啟動失敗,請先對照官方範例。

## 部署並追蹤
Duration: 8

### 套用

```bash
kubectl apply -f my-greeter.yaml
kubectl wait --for=condition=Ready component/my-greeter -n default --timeout=120s
```

也可以用 `occ` 確認:

```bash
occ component list --namespace default --project default
occ component get my-greeter --namespace default
```

### 追蹤 Release

Component 的變更會產生不可變的 ComponentRelease:

```bash
kubectl get component my-greeter -n default -o jsonpath='{.status.latestRelease.name}'
kubectl get componentrelease -n default
```

名稱尾碼是 Release spec 的雜湊值,你的結果會不同。

### 查看 development 環境的 ReleaseBinding

```bash
kubectl get releasebinding my-greeter-development -n default
```

這就是第 2 課說的「把 Release 釘在某個環境」。

### 查看 Data Plane 上真正的資源

```bash
kubectl get deployment,svc,httproute -A -l openchoreo.dev/component=my-greeter
```

這些資源位於類似 `dp-default-default-development-*` 的 namespace,而不是 `default`。

Positive
: 你只寫了約 30 行 YAML,平台根據 `deployment/service` 這個 ComponentType 幫你生出 Deployment、Service 與 HTTPRoute。

## 呼叫服務
Duration: 3

閘道網址格式:

```
http://{environment}-{namespace}.{gateway-host}/{endpoint-name}/{path}
```

本機 Dev Container 的閘道在 19080:

```bash
curl http://development-default.openchoreoapis.localhost:19080/my-greeter-http/greeter/greet
curl "http://development-default.openchoreoapis.localhost:19080/my-greeter-http/greeter/greet?name=OpenChoreo"
```

預期輸出:

```
Hello, Stranger!
Hello, OpenChoreo!
```

Positive
: 端點路徑前綴是 `/{component}-{endpoint 名稱}`,所以這裡是 `/my-greeter-http`。可用 `kubectl get httproute -A -l openchoreo.dev/component=my-greeter -o yaml` 確認。

### 排錯清單

| 症狀 | 檢查 |
|---|---|
| Component 一直不 Ready | `kubectl describe component my-greeter -n default` 看 conditions |
| Pod 起不來 | 在 `dp-*` namespace 用 `kubectl describe pod` |
| 404 | 檢查 HTTPRoute 的 path 與主機名 |
| 連不上 | 確認閘道 port 是 19080(Dev Container) |

## 修改並觀察新 Release
Duration: 4

把 `LOG_LEVEL` 改成 `debug`,重新套用:

```bash
sed -i 's/value: "info"/value: "debug"/' my-greeter.yaml
kubectl apply -f my-greeter.yaml
kubectl get componentrelease -n default
kubectl get releasebinding my-greeter-development -n default -o yaml
```

觀察:

1. 是否多出一個新的 ComponentRelease?
2. ReleaseBinding 指向的 Release 是否更新(因為 `autoDeploy: true`)?

## 清理
Duration: 1

```bash
kubectl delete -f my-greeter.yaml
```

## 自我檢核
Duration: 4

試著不看上文回答下面的問題;答不出來的,回頭看對應的章節。

1. Component 和 Workload 各回答什麼問題?

2. 網址 `http://development-default.openchoreoapis.localhost:19080/my-greeter-http/greeter/greet` 的 `/my-greeter-http` 是什麼?

3. 如果想讓服務只在叢集內使用,不產生外部路由,該怎麼設定端點?

4. 修改 `LOG_LEVEL` 後再 apply,發生了什麼事?

### 參考答案

1. Component 回答「這是什麼類型、怎麼被平台管理」;Workload 回答「我的程式需要什麼才能跑」(映像、埠、依賴)。

2. HTTPRoute 比對用的路徑前綴,格式是 `/{元件名}-{端點名}`,轉給應用時會被剝掉。

3. 不要把 `visibility` 寫成 `external`(例如寫 `project`),只有 `external` 才會產生對外路由。

4. 產生新的 ComponentRelease,因為 `autoDeploy: true`,development 的 ReleaseBinding 指向新 Release。

## 恭喜與下一步
Duration: 1

你已經:

* ✅ 安裝並登入 `occ`
* ✅ 手寫 Component + Workload 並部署
* ✅ 沿著 Release → ReleaseBinding → 實際資源追蹤了整個過程
* ✅ 透過閘道呼叫服務

### 延伸閱讀

* [Deploy and Explore](https://openchoreo.dev/docs/getting-started/deploy-and-explore/)
* [Projects and Components](https://openchoreo.dev/docs/developer-guide/projects-and-components/overview/)
* [Creating a Component](https://openchoreo.dev/docs/developer-guide/projects-and-components/creating-a-component/)

### 下一課

**04:從原始碼建置** — 啟用 Workflow Plane,從 Git 原始碼自動建置映像並部署。
