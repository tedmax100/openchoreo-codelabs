summary: 理解 OpenChoreo 的五大 Plane 與 Project、Component、Workload、Environment 等核心資源,並用 kubectl 實際觀察
id: openchoreo-02-architecture-concepts
categories: openchoreo,kubernetes,architecture
environments: Web
status: Published
feedback link: https://github.com/openchoreo/openchoreo/issues
author: 雷N

# OpenChoreo 實戰 02:架構與核心概念

## 概覽
Duration: 2

### 先決條件

* 已完成 **01:5 分鐘跑起 OpenChoreo**,叢集仍在運行
* 本機已安裝 `kubectl`,且能連到 k3d 叢集(或在 Dev Container 內操作)

### 你會學到

* OpenChoreo 的五種 Plane 各自負責什麼
* 開發者資源與平台資源的分工
* 用 `kubectl` 把概念對應到真實的資源

## 先備知識:Kubernetes 的「期望狀態」模型
Duration: 8

要看懂 OpenChoreo 的架構,必須先理解 Kubernetes 一個最核心的設計。

### 命令式 vs 宣告式

| | 命令式(Imperative) | 宣告式(Declarative) |
|---|---|---|
| 你說什麼 | 「啟動 3 個副本」 | 「我要有 3 個副本」 |
| 重複執行 | 可能多啟動一次 | 結果相同,安全 |
| 出狀況 | 你必須自己發現並處理 | 系統自己補回來 |

Kubernetes 是宣告式的:你描述**期望狀態(desired state)**,系統負責讓**實際狀態(actual state)**追上它。

### 調和迴圈(Reconciliation Loop)

負責「讓實際追上期望」的程式叫 **控制器(Controller)**,它永遠在跑一個迴圈:

```
        ┌──────────────────────────────┐
        ▼                              │
  觀察實際狀態 ──▶ 和期望狀態比較 ──▶ 有差異就採取行動 ──┘
```

例子:你宣告 `replicas: 3`,但有一個 Pod 當機了。控制器發現「實際 2 個、期望 3 個」,就補啟動一個。你完全不用介入。

### CRD:擴充 Kubernetes 的詞彙

Kubernetes 內建的資源種類(Pod、Deployment…)是固定的。**CRD(CustomResourceDefinition)** 讓你新增自己的資源種類,例如 `Component`。

只有 CRD 還不夠,還需要一個懂得處理它的控制器。這個「CRD + 控制器」的組合就是 **Operator 模式**。

**OpenChoreo 本質上就是一組 CRD 加上一群控制器。** 第 1 課你在叢集裡看到的 `controller-manager`,就是這些控制器所在的地方。你寫 `Component`,控制器負責把它變成真正的 Deployment、Service 等資源。

Positive
: 這解釋了為什麼 OpenChoreo 和 GitOps 工具天生合得來(第 6 課):兩者都建立在「宣告期望狀態、持續調和」的同一個模型上。

### 為什麼要拆成多個 Plane?

「Plane」可以理解成「平面」或「層」。OpenChoreo 把不同職責放在不同的 Plane,理由和大型組織的分工很像:

| 類比 | 對應 |
|---|---|
| 公司總部:制定規則、管理所有分店 | Control Plane |
| 分店:真正服務客人的地方 | Data Plane |
| 中央廚房:大量準備共用的東西 | Workflow Plane(建置) |
| 品管與監視中心 | Observability Plane |
| 櫃檯與服務窗口 | Experience Plane(CLI 與入口網站) |

拆開的好處:

* **安全隔離**:跑使用者程式的 Data Plane,不需要有建置或管理的高權限
* **獨立擴展與故障隔離**:建置很吃資源,不該拖垮正在服務的應用
* **多叢集**:一個 Control Plane 可以管理分佈在不同區域、不同雲的多個 Data Plane

在本機實驗時,所有 Plane 擠在同一個叢集;正式環境可以拆開。概念不變。

### 領域驅動設計(DDD)的「界限上下文」

下面會提到 **Project 是一個 bounded context**。這是領域驅動設計的詞彙:把「彼此關係緊密、共同完成一個商業能力」的東西圈成一個邊界。例如「訂單」和「付款」可能各自是一個 Project。邊界內可以自由溝通,跨邊界則要透過明確的介面。這也是為什麼 Project 同時是安全與網路的邊界。

準備好了,看看實際的架構。

## 五大 Plane
Duration: 5

OpenChoreo 採模組化多 Plane 架構,各 Plane 彼此獨立,可以跑在同一個或不同的叢集。

| Plane | 角色 |
|---|---|
| **Control Plane** | 中央協調者,持續把「期望狀態」調和(reconcile)到其他 Plane |
| **Experience Plane** | 提供有權限控管的介面:`occ` CLI 與 Backstage 入口網站 |
| **Data Plane** | 隔離、可觀測的執行環境與閘道,真正跑你的應用 |
| **Workflow Plane** | 執行 CI 建置、測試、GitOps 流程與平台定義的任務(例如佈建資源) |
| **Observability Plane** | 收集並彙整日誌、指標與 OpenTelemetry Tracing |

Positive
: 在第 1 課的本機安裝裡,這些 Plane 全部壓在同一個 k3d 叢集上;正式環境可以拆開。Workflow 與 Observability Plane 就是 `--with-build`、`--with-observability` 所啟用的部分。

### 兩種 API 兩種角色

* **Platform API**:平台工程師宣告平台設定(環境、元件類型、流程等)
* **Developer API**:開發者宣告自己的資源(Project、Component、Workload 等)

這個分工是 OpenChoreo 的核心想法:平台工程師定義**護欄與模板**,開發者在護欄內**自助**。

## 開發者資源
Duration: 7

資源階層:

```
Namespace
└── Project
    └── Component
        └── Workload
```

### Project

一個 **bounded context**(領域驅動設計的概念),把同一個商業能力的 Components 分組,是程式碼擁有權、部署與營運的邊界。Project 對應到隔離的 namespace、網路邊界與安全政策;同一 Project 內的 Components 可以自由互相通訊。

### Component

一個**可部署的軟體單元**:微服務、網站或背景工作。它由四個部分組成:

* **ComponentType 參照**:格式為 `{workloadType}/{名稱}`,如 `deployment/service`
* **Parameters**:符合 ComponentType schema 的參數,跨環境一致
* **Traits**:附加能力(儲存、監控…),可多次實例化
* **Workflow 設定**(選用):指定如何從原始碼建置

### Workload

Component 的**執行期合約**:描述「需要什麼」,而不是「平台怎麼提供」。包含:

* **Container**:映像、指令、參數、環境變數
* **Endpoints**:對外暴露的埠與協定(HTTP、gRPC、GraphQL、Websocket、TCP、UDP)
* **Dependencies**:對其他 Component 端點的依賴,或對同 Project 內 Resource 的依賴

### Resource 與 WorkflowRun

* **Resource**:Project 內的受管基礎設施宣告(資料庫、佇列、快取…)
* **WorkflowRun**:Workflow 的一次執行,記錄參數、狀態與歸屬的 Component/Project

## 平台資源
Duration: 4

由平台工程師維護:

* **ComponentType / ClusterComponentType**:Component 的模板,決定它最終會產生哪些 Kubernetes 資源
* **Trait / ClusterTrait**:可重用的附加能力
* **Workflow**:建置等流程的模板
* **Environment**:一個部署階段(development、staging、production…),綁定到一個 DataPlane
* **DataPlane**:應用實際執行的地方,含閘道設定

Positive
: 帶有 **Cluster** 前綴的類型(如 `ClusterComponentType`)是叢集範圍的共用版本,可跨 namespace 使用;沒有前綴的是 namespace 範圍。

### 發佈模型

OpenChoreo 用**不可變的 Release** 管理變更:

1. Component 變更 → 控制器產生不可變的 **ComponentRelease**
2. 每個環境有一個 **ReleaseBinding**,把某個 Release「釘」在該環境
3. **Promotion(晉升)** 就是把釘選指向較新的 Release

環境專屬的設定放在 ReleaseBinding 的 `environmentConfigs`,而不是 Component 的 Parameters。這個模型第 5 課會深入。

## 動手觀察
Duration: 7

把概念對應到真實叢集。先看你有哪些 OpenChoreo 的 CRD:

```bash
kubectl api-resources --api-group=openchoreo.dev
```

查看已有的 Project、Environment、Component:

```bash
kubectl get project,environment,component -A
```

用 `occ` 看同樣的事(需先安裝並登入,見第 3 課):

```bash
occ namespace list
occ project list -n default
occ component list -n default
```

### 找出資料層真正的 Kubernetes 資源

Control Plane 裡的 Component 只是「宣告」,實際的 Deployment、Service 等在 Data Plane 的獨立 namespace:

```bash
kubectl get ns | grep dp-
kubectl get deployment,svc -A -l openchoreo.dev/component=react-starter
```

Negative
: 如果最後一個指令沒有輸出,可能是 label 或 Component 名稱和你的環境不同。先用 `kubectl get component -A` 確認名稱。這些 label 與 namespace 命名是依官方文件整理,請以你叢集的實際輸出為準。

### 思考題

1. `react-starter` 在 Control Plane 與 Data Plane 各留下了哪些資源?
2. 為什麼開發者不直接寫 Deployment,而是寫 Component + Workload?

## 自我檢核
Duration: 4

試著不看上文回答下面的問題;答不出來的,回頭看對應的章節。

1. 宣告式與命令式差在哪?請用 `replicas: 3` 舉例。

2. OpenChoreo 本質上是由什麼組成的?

3. 為什麼要把 Control Plane 和 Data Plane 分開?至少說出兩個理由。

4. Project 為什麼同時是「領域邊界」和「安全邊界」?

### 參考答案

1. 宣告式描述「我要 3 個副本」,系統持續調和;即使有 Pod 當機也會補回來。命令式是「啟動 3 個」,重複執行可能多啟動。

2. 一組 CRD 加上處理它們的控制器(Operator 模式)。

3. 安全隔離(跑使用者程式的地方不需要管理高權限)、故障與資源隔離、一個控制平面可管理多個資料平面或多叢集。

4. 它對應 DDD 的 bounded context:同一能力的元件圈在一起,並對應到獨立 namespace、網路與安全政策,邊界內自由溝通。

## 小結
Duration: 1

| 概念 | 一句話 |
|---|---|
| Plane | 五種職責分離的執行層 |
| Project | 領域邊界,Component 的分組 |
| Component | 可部署單元 = 類型 + 參數 + Trait + Workflow |
| Workload | 執行期合約:容器、端點、依賴 |
| Environment | 綁定 DataPlane 的部署階段 |
| Release / ReleaseBinding | 不可變版本與其在各環境的釘選 |

### 延伸閱讀

* [Architecture](https://openchoreo.dev/docs/overview/architecture)
* [Developer Abstractions](https://openchoreo.dev/docs/concepts/developer-abstractions/)
* [Deployment Topology](https://openchoreo.dev/docs/platform-engineer-guide/deployment-topology/)

### 下一課

**03:部署你的第一個 Component** — 自己寫 YAML,用 `occ` 與 `kubectl` 部署。
