summary: 部署 Google 的 11 個服務微服務範例,學習 Project、Resource、服務依賴注入,並練習從症狀定位故障的排錯流程
id: openchoreo-09-microservices
categories: openchoreo,kubernetes,microservices
environments: Web
status: Published
feedback link: https://github.com/openchoreo/openchoreo/issues
author: 雷N

# OpenChoreo 實戰 09:微服務實戰

## 概覽
Duration: 2

前面的服務都是「單打獨鬥」。真實系統由許多服務互相呼叫,還有資料庫、快取。這一課部署 Google 的 **Online Boutique** 微服務範例:一個線上商店,由 10 個應用服務加上 1 個 Redis(Valkey)快取組成,服務之間用 gRPC 溝通。

### 先決條件

* 已完成第 1 到 3 課
* 資源:建議 **8 GB RAM 以上**,磁碟至少 **5 GB** 可用
* 能連到 `us-central1-docker.pkg.dev`(範例映像來源)
* 範例映像為 **AMD64**;Apple Silicon 需要容器執行環境支援 AMD64 模擬

### 你會學到

* 一個 Project 如何容納多個 Component
* 用 `Resource` 宣告資料庫或快取,並讓元件取得連線字串
* 用 `dependencies` 讓服務自動取得彼此的位址
* 驗證整個購物流程
* 故意弄壞一個服務,練習定位問題

## 先備知識:微服務與服務之間的呼叫
Duration: 10

### 單體 vs 微服務

| | 單體(Monolith) | 微服務(Microservices) |
|---|---|---|
| 結構 | 所有功能在一個程式裡 | 每個功能一個獨立服務 |
| 優點 | 簡單、呼叫快、好除錯 | 各服務可獨立開發、部署、擴展,可用不同語言 |
| 缺點 | 越大越難改、一處壞全壞 | 服務之間的網路呼叫、整體複雜度、更難排錯 |

微服務不是銀彈,它用「分散式系統的複雜度」換「組織與部署的彈性」。這也是為什麼平台需要幫忙:依賴、設定、觀測都要有人管。

### Online Boutique

這一課的範例是 Google 公開的微服務示範應用(線上商店)。它刻意用不同語言(Go、C#、Node.js、Python、Java)寫成,適合展示多語言環境。

### gRPC 與 Protocol Buffers

服務之間常用 **gRPC** 溝通,它是 Google 開發的高效能遠端呼叫框架:

| | REST/JSON | gRPC |
|---|---|---|
| 格式 | 文字(JSON) | 二進位(Protocol Buffers) |
| 契約 | 常靠文件 | 用 `.proto` 檔嚴格定義 |
| 傳輸 | HTTP/1.1 為主 | HTTP/2,可串流 |

在 OpenChoreo 中,端點的 `type: gRPC` 會讓平台知道要怎麼建立 Service。

### 服務如何找到彼此:服務探索

Pod 的 IP 會隨時變動,所以不能寫死 IP。Kubernetes 用 **Service** 提供穩定的名稱,並由叢集 DNS 解析:

```
<服務名>.<namespace>.svc.cluster.local:<port>
```

你在第 9 課會看到 frontend 收到的環境變數,就是這種格式(例如 `cart.dp-default-...svc.cluster.local:7070`)。**OpenChoreo 幫你算出這個位址並注入環境變數**,你只需宣告「我依賴 cart 的 grpc 端點」。

### 有狀態與無狀態

| | 無狀態(Stateless) | 有狀態(Stateful) |
|---|---|---|
| 例子 | frontend、checkout | Redis、資料庫 |
| 特性 | 任何副本都一樣,隨時可替換 | 資料要保存,不能隨便丟 |

無狀態服務適合用 Deployment 擴縮。有狀態的基礎設施(資料庫、快取)比較麻煩,所以 OpenChoreo 提供 **Resource** 抽象:你宣告「我要一個 valkey」,平台負責佈建並把連線資訊安全地交給需要它的元件(經由 Secret,而不是寫在設定裡)。

### 連鎖故障(Cascading Failure)

微服務最可怕的事:**一個服務壞了,依賴它的服務跟著壞,一路往上蔓延**。本課的排錯演練就是示範:關掉 productcatalog,結果整個首頁回 500。

防禦手段(超出本課範圍,但值得知道):

* **逾時(timeout)**:不要無限等待
* **重試與退避**:短暫故障自動恢復,但要避免「重試風暴」
* **斷路器(circuit breaker)**:持續失敗就先停止呼叫
* **降級(graceful degradation)**:商品目錄壞了,至少顯示靜態頁

### 排錯思維

Google SRE 書中提出的**四個黃金訊號**,是判斷服務健康的好起點:

| 訊號 | 問題 |
|---|---|
| 延遲(Latency) | 請求花多久? |
| 流量(Traffic) | 有多少請求? |
| 錯誤(Errors) | 多少請求失敗? |
| 飽和度(Saturation) | 資源用到多滿? |

排錯的通用順序:**症狀 → 哪個服務 → 為什麼 → 誰改了什麼**。本課的排錯演練會帶你照這個順序走一遍。

## 架構
Duration: 4

```
                        ┌──────────┐
 瀏覽器 ──(外部)──────▶ │ frontend │
                        └────┬─────┘
        ┌───────┬────────┬───┴────┬─────────┬──────────┬───────────┐
        ▼       ▼        ▼        ▼         ▼          ▼           ▼
       ad     cart   checkout  currency  recommendation shipping productcatalog
                │        │
                ▼        ├──▶ payment
             [redis]     ├──▶ email
                         └──▶ shipping / currency / productcatalog / cart
```

| 服務 | 語言 | 角色 |
|---|---|---|
| frontend | Go | 網站,**唯一對外**的服務 |
| productcatalog | Go | 商品目錄 |
| cart | C# | 購物車,資料存在 Redis |
| checkout | Go | 結帳,協調其他服務 |
| currency / payment | Node.js | 匯率、付款 |
| email / recommendation | Python | 寄信、推薦 |
| shipping / ad | Go / Java | 運費、廣告 |
| redis | Valkey | 購物車快取,以 **Resource** 宣告 |

Positive
: 只有 `frontend` 宣告了 `visibility: [external]`,其他服務預設只在 Project 內可見。這是 OpenChoreo 的「預設封閉」:內部服務不會因為你忘了設定而暴露到外面。

## 建立 Project
Duration: 4

```bash
R=https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/samples/gcp-microservices-demo
kubectl apply -f $R/gcp-microservice-demo-project.yaml
```

這個檔案包含一個 Project 與三個 `ProjectReleaseBinding`(development、staging、production):

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: Project
metadata:
  name: gcp-microservice-demo
  namespace: default
spec:
  deploymentPipelineRef:
    name: default
  type:
    kind: ClusterProjectType
    name: default
```

第 2 課提過:Project 對應到隔離的 namespace 與網路邊界。看看它在 Data Plane 上建了什麼:

```bash
kubectl get ns | grep dp-default-gcp
```

預期有 development、staging、production 三個 namespace。

Negative
: namespace 名稱會被截短成 `dp-default-gcp-microserv-<環境>-<雜湊>`(Project 名稱太長),不要用猜的,用 `kubectl get ns | grep dp-default-gcp` 查。

## 用 Resource 宣告 Redis
Duration: 6

`cart` 需要 Redis。我們不手寫 StatefulSet,而是宣告一個 `Resource`,類型是平台提供的 `valkey`(`ClusterResourceType`):

```bash
kubectl get clusterresourcetype
```

預期有 `nats`、`postgres`、`valkey`。

`resources/redis.yaml` 的重點:

```yaml
apiVersion: openchoreo.dev/v1alpha1
kind: Resource
metadata:
  name: redis
  namespace: default
spec:
  owner:
    projectName: gcp-microservice-demo
  type:
    kind: ClusterResourceType
    name: valkey
---
apiVersion: openchoreo.dev/v1alpha1
kind: ResourceReleaseBinding
metadata:
  name: redis-development
  namespace: default
spec:
  owner:
    projectName: gcp-microservice-demo
    resourceName: redis
  environment: development
  retainPolicy: Delete
```

這和元件的 Release / ReleaseBinding 模型一模一樣:Resource 產生不可變的 `ResourceRelease`,`ResourceReleaseBinding` 把它釘到某個環境。

套用,並把綁定釘到最新的 Release(控制器先建立 Release,綁定的 `resourceRelease` 欄位起初是空的):

```bash
kubectl apply -f $R/resources/redis.yaml
until release=$(kubectl get resource redis -n default -o jsonpath='{.status.latestRelease.name}') && [ -n "$release" ]; do sleep 2; done
kubectl patch resourcereleasebinding redis-development -n default \
  --type=merge -p "{\"spec\":{\"resourceRelease\":\"$release\"}}"
kubectl get resourcereleasebinding redis-development -n default
```

預期 `READY` 變成 `True`(剛套用時會短暫是 `False`)。

## 服務依賴
Duration: 6

看 `cart` 的 Workload,它宣告了對 Redis 的**資源依賴**:

```yaml
spec:
  endpoints:
    grpc:
      type: gRPC
      port: 7070
  dependencies:
    resources:
      - ref: redis
        envBindings:
          connectionString: REDIS_ADDR
```

`envBindings` 的意思:把 Redis 輸出的 `connectionString`,注入成環境變數 `REDIS_ADDR`。

再看 `frontend` 的**端點依賴**(節錄):

```yaml
  dependencies:
    endpoints:
      - project: gcp-microservice-demo
        component: cart
        name: grpc
        visibility: project
        envBindings:
          address: CART_SERVICE_ADDR
      # ... 還有 ad、checkout、currency、payment、
      #     recommendation、shipping、productcatalog
```

開發者只宣告「我依賴 cart 的 grpc 端點」,平台負責算出實際位址、注入環境變數。

### 部署全部元件

```bash
args=""
for c in ad cart checkout currency email frontend payment productcatalog recommendation shipping; do
  args="$args -f $R/components/$c-component.yaml"
done
kubectl apply $args
```

等待所有 Deployment 就緒(第一次需要下載映像,實測約 1 到 2 分鐘,網路慢時會更久):

```bash
kubectl get deploy -A -l openchoreo.dev/project=gcp-microservice-demo
```

預期 10 個 Deployment 都是 `1/1`。

### 驗證依賴注入

```bash
NS=$(kubectl get ns -o name | grep dp-default-gcp.*development | cut -d/ -f2)

# frontend 拿到其他服務的位址
kubectl get deploy -n $NS -l openchoreo.dev/component=frontend \
  -o jsonpath='{range .items[0].spec.template.spec.containers[0].env[*]}{.name}={.value}{"\n"}{end}'

# cart 的 REDIS_ADDR 來自 Secret
kubectl get deploy -n $NS -l openchoreo.dev/component=cart \
  -o jsonpath='{.items[0].spec.template.spec.containers[0].env}{"\n"}'
```

預期 frontend 看到 `CART_SERVICE_ADDR=cart.<namespace>.svc.cluster.local:7070` 這類位址;cart 的 `REDIS_ADDR` 用 `secretKeyRef` 指向 Redis 的連線字串 Secret,**密碼不會出現在 Deployment 裡**。

Positive
: 這就是平台抽象的價值:位址、Secret 的名稱與 key 全由平台管理。開發者換環境時,不需要改任何一個 URL。

## 測試商店
Duration: 6

找出 frontend 的外部網址:

```bash
HOST=$(kubectl get httproute -A -l openchoreo.dev/component=frontend \
  -o jsonpath='{.items[0].spec.hostnames[0]}')
H=http://$HOST:19080
echo $H
```

用瀏覽器開啟,或用 `curl` 走完整個流程:

```bash
# 首頁與商品頁
curl -s -o /dev/null -w "%{http_code}\n" $H/
curl -s -o /dev/null -w "%{http_code}\n" $H/product/OLJCESPC7Z

# 加入購物車(2 件),再查看
curl -s -c /tmp/cj -b /tmp/cj -o /dev/null -w "%{http_code}\n" \
  -d "product_id=OLJCESPC7Z&quantity=2" $H/cart
curl -s -b /tmp/cj $H/cart | grep -o -E "Cart \([0-9]+\)|Sunglasses" | sort -u

# 結帳
curl -s -b /tmp/cj -c /tmp/cj -o /tmp/order.html -d "email=someone@example.com&street_address=1600 Amphitheatre Parkway&zip_code=94043&city=Mountain View&state=CA&country=United States&credit_card_number=4432801561520454&credit_card_expiration_month=1&credit_card_expiration_year=2030&credit_card_cvv=672" \
  $H/cart/checkout
grep -o "Your order is complete" /tmp/order.html
```

預期:兩個 `200`、加入購物車回 `302`、看到 `Cart (2)` 與 `Sunglasses`、最後印出 `Your order is complete`。

這一個結帳請求,牽動了 frontend → checkout → cart(Redis)/ productcatalog / currency / shipping / payment / email 共 7 個服務。

Negative
: 範例文件說服務完全就緒可能要 5 到 10 分鐘。若頁面回 500 或連不上,先等一下,再用 `kubectl get pods -A | grep -v Running` 找出還沒就緒的 Pod。

## 排錯演練
Duration: 8

練習「從症狀倒推原因」。我們讓 `productcatalog` 下線:

```bash
kubectl patch releasebinding productcatalog-development -n default --type merge \
  -p '{"spec":{"componentTypeEnvironmentConfigs":{"replicas":0}}}'
sleep 15
curl -s -o /dev/null -w "%{http_code}\n" $H/
```

### 症狀:首頁回 500

頁面上會有錯誤細節,類似:

```
rpc error: code = Unavailable desc = connection error: desc = "transport: Error while dialing: dial tcp 10.43.x.x:3550: connect: connection refused"
```

### 步驟 1:錯誤訊息告訴你什麼?

* `Unavailable` + `connection refused` + 連接埠 **3550**。回頭看架構表,3550 是 `productcatalog`。

### 步驟 2:看呼叫端的日誌

```bash
kubectl logs -n $NS deploy/$(kubectl get deploy -n $NS -l openchoreo.dev/component=frontend \
  -o jsonpath='{.items[0].metadata.name}') --tail=200 | grep -i "could not retrieve"
```

會看到 `could not retrieve products: rpc error: code = Unavailable ...`。

### 步驟 3:確認被呼叫端

```bash
kubectl get deploy -n $NS | grep productcatalog     # 0/0
kubectl get endpoints -n $NS productcatalog         # <none>
```

Deployment 是 `0/0`、Service 沒有任何後端,原因就找到了。

### 步驟 4:找出為什麼是 0

```bash
kubectl get releasebinding productcatalog-development -n default -o yaml | grep -A3 componentTypeEnvironmentConfigs
```

有人(就是我們)把 `replicas` 覆寫成 0。

### 修復

```bash
kubectl patch releasebinding productcatalog-development -n default --type merge \
  -p '{"spec":{"componentTypeEnvironmentConfigs":{"replicas":1}}}'
kubectl wait --for=condition=Available deploy -n $NS -l openchoreo.dev/component=productcatalog --timeout=120s
curl -s -o /dev/null -w "%{http_code}\n" $H/
```

實測 Pod 就緒後 5 秒內首頁恢復 `200`。

Positive
: 排錯口訣:**症狀 → 錯誤碼與連接埠 → 呼叫端日誌 → 被呼叫端狀態 → 找出誰改了什麼**。因為所有環境差異都集中在 ReleaseBinding,最後一步通常就看那裡。

## 選修:啟用分散式追蹤
Duration: 8

範例中 7 個服務(frontend、checkout、productcatalog、currency、payment、email、recommendation)已內建 OpenTelemetry。這一節需要先完成第 7 課的 Observability Plane。

把 Collector 位址與開關加進 Workload:

```bash
COLLECTOR_ADDR="opentelemetry-collector.openchoreo-observability-plane.svc.cluster.local:4317"
for svc in checkout currency email frontend payment productcatalog recommendation; do
  kubectl patch workload "$svc" -n default --type=json -p="[
    {\"op\":\"add\",\"path\":\"/spec/container/env/-\",\"value\":{\"key\":\"COLLECTOR_SERVICE_ADDR\",\"value\":\"$COLLECTOR_ADDR\"}},
    {\"op\":\"add\",\"path\":\"/spec/container/env/-\",\"value\":{\"key\":\"ENABLE_TRACING\",\"value\":\"1\"}}]"
done
```

Negative
: **環境變數在 ConfigMap 裡,Pod 不會自動重啟。** 修改後 ConfigMap 名稱沒變,所以 Deployment 不會滾動更新,新環境變數不會生效。需要手動重啟:`kubectl rollout restart deploy -n $NS -l openchoreo.dev/component=<服務>`。

重啟、打幾次流量後,查看 OpenSearch(帳密與 port-forward 見第 7 課):

```bash
curl -sk -u "$U:$P" "https://localhost:19200/_cat/indices?h=index,docs.count" | grep otel
```

實測出現了 `otel-traces-YYYY-MM-DD` 索引,span 帶有 `k8s.deployment.name`、`k8s.namespace.name` 等屬性,來源包含 frontend 與 productcatalog。

Negative
: 作者實測只看到 OTLP 匯出器**自己**的 gRPC span(`opentelemetry.proto.collector.trace.v1.TraceService/Export`),沒有看到 `GET /` 這類請求層級的 span。追蹤管線本身確實通了,但請求層級追蹤是否完整,本課沒有驗證。

## 清理
Duration: 3

```bash
kubectl delete $args
kubectl delete -f $R/resources/redis.yaml
kubectl delete -f $R/gcp-microservice-demo-project.yaml
```

Project 刪除後,Data Plane 上的 `dp-default-gcp-*` namespace 會進入 Terminating,一兩分鐘內消失。

## 自我檢核
Duration: 4

試著不看上文回答下面的問題;答不出來的,回頭看對應的章節。

1. frontend 怎麼知道 cart 的位址?

2. cart 的 `REDIS_ADDR` 為什麼用 `secretKeyRef`?

3. productcatalog 下線時,首頁回 500。你會依什麼順序排錯?

4. 為什麼改了 `ENABLE_TRACING` 還要重啟 Pod?

### 參考答案

1. 在 Workload 宣告對 cart grpc 端點的 dependency,平台計算出位址並注入環境變數(格式如 `cart.<ns>.svc.cluster.local:7070`)。

2. 連線字串屬於敏感資訊,放在 Secret 並以參照注入,不會明文出現在 Deployment 裡。

3. 症狀 → 錯誤碼與連接埠(3550 = productcatalog)→ 呼叫端日誌 → 被呼叫端狀態(0/0、無 endpoints)→ 找出誰改了什麼(ReleaseBinding 的 replicas)。

4. 環境變數在 ConfigMap 裡,ConfigMap 名稱沒變所以 Deployment 不會滾動更新,Pod 不會自動重讀。

## 恭喜與下一步
Duration: 1

你已經:

* ✅ 部署了 10 個服務加一個 Redis Resource 的完整應用
* ✅ 理解端點依賴與資源依賴如何自動注入設定
* ✅ 跑通了瀏覽、加入購物車、結帳的完整流程
* ✅ 練習了從 500 錯誤定位到被關閉的服務
* ✅ 讓真實的服務把 span 送進 Observability Plane

### 延伸閱讀

* [Google Microservices Demo 範例](https://github.com/openchoreo/openchoreo/tree/release-v1.3/samples/gcp-microservices-demo)
* [OpenChoreo 文件](https://openchoreo.dev/docs/)

### 下一課

**10:AI 與 MCP 整合(選修)** — 讓 AI 代理人透過 MCP 操作 OpenChoreo。
