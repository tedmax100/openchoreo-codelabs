summary: 安裝 Observability Plane,認識 OpenChoreo 的日誌、指標、追蹤與事件收集架構,並直接查詢底層資料確認管線運作
id: openchoreo-07-observability
categories: openchoreo,kubernetes,observability
environments: Web
status: Published
feedback link: https://github.com/openchoreo/openchoreo/issues
author: 雷N

# OpenChoreo 實戰 07:可觀測性

## 概覽
Duration: 2

部署完成不代表運作正常。這一課啟用 **Observability Plane**,讓平台自動收集你應用的日誌、指標與 Kubernetes 事件。

### 先決條件

* 已完成第 1 到 3 課
* 資源:建議 **8 GB RAM 以上**,主機磁碟至少 **10 GB** 可用(OpenSearch 與 Prometheus 會佔用)
* 能連到 `ghcr.io`(需要下載多個 Helm chart 與映像)

### 你會學到

* Observability Plane 由哪些元件組成
* 如何安裝並向控制平面註冊
* 日誌、指標、事件各自存放在哪裡
* 如何用 `kubectl port-forward` 直接查底層資料來排錯
* 追蹤(Tracing)需要什麼條件(實際驗證在第 9 課)

Negative
: 本課的 Observer API、`occ component logs` 與入口網站的觀測畫面都需要 OAuth 登入,作者在自動化環境無法完成瀏覽器登入,所以這些介面**沒有實際操作**,只有列出指令。底層的 OpenSearch 與 Prometheus 查詢則是實測過的。

## 先備知識:可觀測性的三大支柱
Duration: 10

### 監控 vs 可觀測性

| | 監控(Monitoring) | 可觀測性(Observability) |
|---|---|---|
| 回答的問題 | 「已知的問題有沒有發生?」 | 「為什麼出問題?我沒預料到的問題呢?」 |
| 做法 | 預先設定指標與告警 | 收集足夠豐富的資料,事後能自由探索 |

系統一複雜(尤其是微服務),你無法預先猜到所有問題,所以需要能「事後提問」的資料。

### 三大支柱 + 事件

| 支柱 | 它是什麼 | 回答的問題 | 例子 |
|---|---|---|---|
| **日誌(Logs)** | 帶時間戳的文字紀錄 | 「發生了什麼事?」 | `Starting HTTP Greeter on port 9090` |
| **指標(Metrics)** | 隨時間變化的數字 | 「整體狀況如何?趨勢?」 | CPU 使用率、每秒請求數 |
| **追蹤(Traces)** | 一個請求經過各服務的完整路徑 | 「這個請求慢在哪裡?」 | frontend → checkout → payment |
| **事件(Events)** | Kubernetes 的狀態變化紀錄 | 「叢集做了什麼?」 | Pod 被排程、映像拉取失敗 |

三者互補:**指標告訴你有問題,追蹤告訴你問題在哪個服務,日誌告訴你為什麼。**

### 追蹤的詞彙

| 名詞 | 說明 |
|---|---|
| **Trace(追蹤)** | 一個請求從頭到尾的完整紀錄,有唯一的 `traceId` |
| **Span(跨度)** | 追蹤中的一個步驟(例如「呼叫 payment 服務」),有起訖時間、`spanId`、`parentSpanId` |
| **傳遞(propagation)** | 服務之間透過標頭傳遞 `traceId`,才能把各服務的 span 串成一棵樹 |

因為追蹤需要**程式碼配合**(埋點),所以不像日誌那樣「自動就有」。這也是為什麼第 3 課的 Greeter 沒有追蹤資料。

### OpenTelemetry

**OpenTelemetry(OTel)** 是 CNCF 的觀測資料標準與工具集,核心是統一「資料長什麼樣、怎麼傳」:

| 元件 | 說明 |
|---|---|
| **SDK** | 放進你的應用程式,產生 span、指標 |
| **OTLP** | 傳輸協定(gRPC 4317 或 HTTP 4318) |
| **Collector** | 接收、處理(例如附加 Kubernetes 標籤)、轉送到後端 |

好處是**與廠商無關**:今天送到 OpenSearch,明天換別的後端,應用程式不用改。

### 各元件在做什麼?

| 元件 | 做法 |
|---|---|
| **Fluent Bit** | 以 DaemonSet 在每個節點跑一份,讀取容器的 stdout/stderr 日誌檔,轉送出去 |
| **Prometheus** | 以**拉取(pull)**方式,定期去各目標的 `/metrics` 端點抓數字,存成時間序列;用 PromQL 查詢 |
| **OpenSearch** | 可水平擴充的搜尋引擎,擅長全文檢索,適合存日誌與追蹤 |
| **kube-state-metrics** | 把 Kubernetes 物件的狀態(例如 Pod 重啟次數)轉成指標 |

### 為什麼標籤(labels)這麼重要?

原始的容器日誌只知道「來自某個 Pod」。OpenChoreo 的收集管線會附上 `component`、`project`、`environment` 等標籤。這讓你能問**平台層級**的問題:「development 環境裡 checkout 元件的錯誤日誌」,而不是去猜 Pod 名稱(Pod 名稱每次重建都會變)。

### 為什麼觀測資料要放在獨立的 Plane?

* 觀測資料量大,不該和業務服務搶資源
* 服務掛了,觀測系統必須還活著,才能告訴你為什麼掛
* 可以集中收集多個 Data Plane 的資料

### 可替換的模組化設計

OpenChoreo 把日誌、指標、追蹤各做成獨立的 Helm 模組,透過 **adapter(轉接器)** 對外提供統一的查詢介面。想換掉 OpenSearch 或 Prometheus,只要換對應的模組即可。

下面就來安裝它們。

## 架構
Duration: 4

| 元件 | 角色 |
|---|---|
| **Fluent Bit** | DaemonSet,收集每個節點上容器的日誌 |
| **OpenSearch** | 儲存日誌、事件(與追蹤) |
| **Prometheus + kube-state-metrics** | 收集指標 |
| **OpenTelemetry Collector** | 接收 OTLP 追蹤(gRPC 4317 / HTTP 4318) |
| **events-collector** | 把 Kubernetes 事件寫進 OpenSearch |
| **logs / metrics / tracing adapter** | 把各後端包成統一的查詢介面 |
| **Observer** | 對外的查詢 API,需要 OAuth token |
| **cluster-agent** | 與控制平面通訊 |

資料流向:

```
容器 stdout ─▶ Fluent Bit ─▶ OpenSearch ─▶ logs-adapter ┐
cAdvisor/kube-state ─▶ Prometheus ─▶ metrics-adapter    ├─▶ Observer ─▶ Backstage / occ / MCP
應用 OTLP ─▶ OTel Collector ─▶ OpenSearch ─▶ tracing-adapter ┘
```

Positive
: OpenChoreo 的觀測是**可替換的模組**:日誌、追蹤、指標各自是一個 Helm 模組,平台團隊可以換成其他後端,只要實作對應的 adapter。

## 安裝 Observability Plane
Duration: 15

以下對應官方 k3d 文件的 Step 7。若你用第 1 課的 Quick Start 容器,執行 `./install.sh --version v1.3.1 --with-observability` 即可,可跳過本節。

### 1. Namespace 與 CA

```bash
kubectl create namespace openchoreo-observability-plane --dry-run=client -o yaml | kubectl apply -f -
CA_CRT=$(kubectl get secret cluster-gateway-ca \
  -n openchoreo-control-plane -o jsonpath='{.data.ca\.crt}' | base64 -d)
kubectl create configmap cluster-gateway-ca \
  --from-literal=ca.crt="$CA_CRT" \
  -n openchoreo-observability-plane --dry-run=client -o yaml | kubectl apply -f -
```

### 2. 密鑰(OpenSearch 帳密與 Observer OAuth)

```bash
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: opensearch-admin-credentials
  namespace: openchoreo-observability-plane
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: default
  target:
    name: opensearch-admin-credentials
  data:
  - secretKey: username
    remoteRef: {key: opensearch-username, property: value}
  - secretKey: password
    remoteRef: {key: opensearch-password, property: value}
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: observer-secret
  namespace: openchoreo-observability-plane
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: default
  target:
    name: observer-secret
  data:
  - secretKey: UID_RESOLVER_OAUTH_CLIENT_SECRET
    remoteRef: {key: observer-oauth-client-secret, property: value}
EOF
kubectl wait -n openchoreo-observability-plane \
  --for=condition=Ready externalsecret/opensearch-admin-credentials externalsecret/observer-secret --timeout=60s
```

### 3. 為 Fluent Bit 產生 machine-id

```bash
docker exec k3d-openchoreo-server-0 sh -c \
  "test -s /etc/machine-id || cat /proc/sys/kernel/random/uuid | tr -d '-' > /etc/machine-id"
```

### 4. 核心元件

```bash
helm upgrade --install openchoreo-observability-plane \
  oci://ghcr.io/openchoreo/helm-charts/openchoreo-observability-plane \
  --version 1.3.1 --namespace openchoreo-observability-plane \
  --values https://raw.githubusercontent.com/openchoreo/openchoreo/release-v1.3/install/k3d/single-cluster/values-op.yaml \
  --set observer.audit.enabled=true --timeout 25m
```

### 5. 日誌、追蹤、指標模組

```bash
helm upgrade --install observability-logs-opensearch \
  oci://ghcr.io/openchoreo/helm-charts/observability-logs-opensearch \
  --create-namespace --namespace openchoreo-observability-plane --version 0.6.0 \
  --set openSearchSetup.openSearchSecretName=opensearch-admin-credentials \
  --set adapter.openSearchSecretName=opensearch-admin-credentials \
  --set auditLogs.enabled=true

helm upgrade --install observability-traces-opensearch \
  oci://ghcr.io/openchoreo/helm-charts/observability-tracing-opensearch \
  --create-namespace --namespace openchoreo-observability-plane --version 0.6.0 \
  --set openSearch.enabled=false \
  --set openSearchSetup.openSearchSecretName=opensearch-admin-credentials

helm upgrade --install observability-metrics-prometheus \
  oci://ghcr.io/openchoreo/helm-charts/observability-metrics-prometheus \
  --create-namespace --namespace openchoreo-observability-plane --version 0.7.1
```

### 6. 啟用日誌收集與事件收集

```bash
helm upgrade observability-logs-opensearch \
  oci://ghcr.io/openchoreo/helm-charts/observability-logs-opensearch \
  --namespace openchoreo-observability-plane --version 0.6.0 --reuse-values \
  --set fluent-bit.enabled=true --set fluentBitCustomizations.clusterInstance=openchoreo
```

Kubernetes 事件收集(`observability-events-otel-collector`,版本 0.1.2)的完整 values 較長,請直接複製[官方文件](https://openchoreo.dev/docs/getting-started/try-it-out/on-k3d-locally/)的 Step 7.9。

### 7. 向控制平面註冊並連結

```bash
kubectl wait -n openchoreo-observability-plane \
  --for=condition=Ready certificate/cluster-agent-observabilityplane-tls --timeout=300s
AGENT_CA=$(kubectl get secret cluster-agent-tls \
  -n openchoreo-observability-plane -o jsonpath='{.data.ca\.crt}' | base64 -d)
kubectl apply -f - <<EOF
apiVersion: openchoreo.dev/v1alpha1
kind: ClusterObservabilityPlane
metadata:
  name: default
spec:
  planeID: default
  clusterAgent:
    clientCA:
      value: |
$(echo "$AGENT_CA" | sed 's/^/        /')
  observerURL: http://observer.openchoreo.localhost:11080
EOF

kubectl patch clusterdataplane default --type merge \
  -p '{"spec":{"observabilityPlaneRef":{"kind":"ClusterObservabilityPlane","name":"default"}}}'
kubectl patch clusterworkflowplane default --type merge \
  -p '{"spec":{"observabilityPlaneRef":{"kind":"ClusterObservabilityPlane","name":"default"}}}'
```

最後一步是在控制平面啟用稽核日誌(官方 Step 7.12,`helm upgrade openchoreo-control-plane ... --set openchoreoApi.config.audit.enabled=true`)。

### 驗證

```bash
kubectl get pods -n openchoreo-observability-plane
kubectl get clusterobservabilityplane
```

所有 Pod 應為 Running 或 Completed(`opensearch-setup-*` 是一次性 Job)。

Negative
: **第一次安裝很慢。** 實測在慢速網路下,核心元件約 12 分鐘,另有幾個映像(`events-collector`、`metrics-adapter`、你的應用)在 `ContainerCreating` 停留數分鐘。用 `kubectl describe pod` 看到 `Pulling image` 就是在下載,耐心等待即可。

## 產生資料
Duration: 5

部署第 3 課的服務並打一些流量(沿用 `my-greeter.yaml`,把名稱換成 `obs-demo`):

```bash
sed 's/my-greeter/obs-demo/g' my-greeter.yaml | kubectl apply -f -
kubectl wait --for=condition=Available deploy -A -l openchoreo.dev/component=obs-demo --timeout=300s

for i in $(seq 1 40); do
  curl -s -o /dev/null -w "%{http_code} " \
    "http://development-default.openchoreoapis.localhost:19080/obs-demo-http/greeter/greet?name=u$i"
done; echo
```

預期 40 個 `200`。

## 日誌
Duration: 6

直接查 OpenSearch(底層儲存)。先取得帳密並 port-forward:

```bash
NS=openchoreo-observability-plane
U=$(kubectl get secret opensearch-admin-credentials -n $NS -o jsonpath='{.data.username}' | base64 -d)
P=$(kubectl get secret opensearch-admin-credentials -n $NS -o jsonpath='{.data.password}' | base64 -d)
kubectl port-forward -n $NS svc/opensearch 19200:9200 &
sleep 3
curl -sk -u "$U:$P" "https://localhost:19200/_cat/indices?h=index,docs.count&s=index"
```

預期看到的索引:

| 索引 | 內容 |
|---|---|
| `container-logs-YYYY-MM-DD` | 所有容器的 stdout/stderr |
| `k8s-events-YYYY-MM-DD` | Kubernetes 事件 |
| `security-auditlog-*` | 稽核日誌 |

查詢某個 Component 的日誌。OpenChoreo 會把 Pod 的標籤(`openchoreo.dev/component` 等)原樣附到每筆日誌上,點會被轉成底線:

```bash
curl -sk -u "$U:$P" "https://localhost:19200/container-logs-*/_search?size=1" \
  -H 'content-type: application/json' \
  -d '{"query":{"match_phrase":{"kubernetes.labels.openchoreo_dev/component":"obs-demo"}}}'
```

每筆日誌包含:

| 欄位 | 範例 |
|---|---|
| `log` | `Starting HTTP Greeter on port 9090` |
| `stream` | `stderr` |
| `kubernetes.pod_name` | `obs-demo-development-…` |
| `kubernetes.namespace_name` | `dp-default-default-development-…` |
| `kubernetes.labels.openchoreo_dev/component` | `obs-demo` |
| `kubernetes.labels.openchoreo_dev/environment` | `development` |

Positive
: 因為每筆日誌都帶有 component、project、environment 標籤,Observer 才能回答「development 環境裡 `obs-demo` 的日誌」這種平台層級的問題,而不是只能依 Pod 名稱查。

Negative
: 這個 Greeter 範例只在啟動時印一行日誌,不會記錄每個請求,所以你只會查到 1 筆。要看到更多日誌,請換成會輸出存取日誌的應用。

### 透過平台介面查詢

登入後可用 `occ`(依 `--help` 整理,未實測):

```bash
occ component logs obs-demo
occ component logs obs-demo --env development -f
```

## 指標
Duration: 5

Prometheus 收集了容器與 kube-state 指標:

```bash
kubectl port-forward -n openchoreo-observability-plane svc/prometheus-operated 19090:9090 &
sleep 3
curl -s localhost:19090/api/v1/query \
  --data-urlencode 'query=sum(container_cpu_usage_seconds_total{namespace="dp-default-default-development-f8e58905"}) by (pod)'
```

預期結果包含你的 `obs-demo-development-…` Pod 的 CPU 累計秒數。

常用查詢:

| 目的 | PromQL |
|---|---|
| 容器 CPU 使用率 | `rate(container_cpu_usage_seconds_total{pod=~"obs-demo.*"}[5m])` |
| 記憶體 | `container_memory_working_set_bytes{pod=~"obs-demo.*"}` |
| 重啟次數 | `kube_pod_container_status_restarts_total{pod=~"obs-demo.*"}` |

Positive
: Data Plane 的 namespace 名稱(`dp-<namespace>-<project>-<environment>-<雜湊>`)可用 `kubectl get ns | grep dp-` 查到,每台叢集的雜湊不同。

## 追蹤與事件
Duration: 5

### 事件

Kubernetes 事件(Pod 排程、拉取映像失敗…)被寫進 `k8s-events-*` 索引,適合排查「為什麼 Pod 起不來」。

### 追蹤

OpenTelemetry Collector 在叢集內開放 OTLP 端點:

| 協定 | 位址 |
|---|---|
| gRPC | `opentelemetry-collector.openchoreo-observability-plane:4317` |
| HTTP | `opentelemetry-collector.openchoreo-observability-plane:4318` |

你的應用要自己用 OpenTelemetry SDK 送出 span 到上面的位址。Greeter 範例沒有埋點,所以不會產生任何追蹤。

Positive
: 追蹤管線已用真實服務驗證:在第 9 課讓叢集內的微服務把 span 送到上面的 Collector 位址,OpenSearch 出現了 `otel-traces-YYYY-MM-DD` 索引,span 帶有 K8s 屬性。

Negative
: 作者一開始從本機 `kubectl port-forward` 用 `telemetrygen` 送測試 span,**沒有**看到追蹤索引,Collector 也沒有錯誤,原因未查明(推測與 Collector 依來源 Pod 關聯 K8s 屬性有關,未驗證)。要驗證追蹤,請讓叢集內有 OTel 埋點的應用送出 span,做法見第 9 課。

## Observer API 與入口網站
Duration: 3

Observer 透過閘道對外:

```bash
curl http://observer.openchoreo.localhost:11080/health
```

回 `200`。其他端點需要 OAuth token,沒有 token 會被拒絕:

```bash
curl -X POST http://observer.openchoreo.localhost:11080/api/v1/logs/query
# {"error":"MISSING_TOKEN","message":"missing or invalid authentication token"}
```

Observer 只服務已通過身分驗證的使用者(入口網站、`occ`、MCP server)。

### 用 MCP 走正門查詢

第 10 課會介紹如何用 Client Credentials 取得 token。有了 token,Observer 的 MCP 端點 `http://observer.openchoreo.localhost:11080/mcp` 就能查詢日誌與指標。實測 `query_component_logs` 查到了 `react-starter` 的存取日誌,`query_resource_metrics` 回傳了 CPU 與記憶體的時間序列。細節請見第 10 課。

## 清理
Duration: 1

```bash
sed 's/my-greeter/obs-demo/g' my-greeter.yaml | kubectl delete -f -
```

Observability Plane 可以保留;如果想釋放資源:

```bash
helm uninstall -n openchoreo-observability-plane \
  openchoreo-observability-plane observability-logs-opensearch \
  observability-traces-opensearch observability-metrics-prometheus \
  observability-events-otel-collector
```

## 自我檢核
Duration: 4

試著不看上文回答下面的問題;答不出來的,回頭看對應的章節。

1. 指標、日誌、追蹤各回答什麼問題?

2. 為什麼 Greeter 範例不會有追蹤資料?

3. OpenChoreo 為什麼要在日誌上附 component、environment 等標籤?

4. Prometheus 是推還是拉?

### 參考答案

1. 指標:整體狀況與趨勢(有問題嗎);追蹤:請求慢在哪個服務;日誌:為什麼出錯。

2. 追蹤需要應用程式自己用 OpenTelemetry SDK 埋點並送出 span,Greeter 沒有埋點。

3. 讓人能問平台層級的問題(某環境某元件的錯誤),而不是依會變動的 Pod 名稱查。

4. 拉取(pull):定期去各目標的 `/metrics` 端點抓取。

## 恭喜與下一步
Duration: 1

你已經:

* ✅ 安裝並註冊了 Observability Plane
* ✅ 理解日誌、指標、追蹤、事件各自的路徑
* ✅ 直接查詢 OpenSearch 與 Prometheus,確認資料有進來
* ✅ 知道追蹤需要應用自己埋點,以及哪些介面需要登入

### 延伸閱讀

* [Run Locally on K3d(Step 7)](https://openchoreo.dev/docs/getting-started/try-it-out/on-k3d-locally/)
* [OpenTelemetry 文件](https://opentelemetry.io/docs/)

### 下一課

**08:平台工程師——自訂 Golden Path** — 自己定義 ComponentType 與 Trait。
