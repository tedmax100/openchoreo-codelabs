# OpenChoreo 實戰 Codelabs

由淺入深的 10 堂繁體中文教學,在本機 Kubernetes 上學會 [OpenChoreo](https://openchoreo.dev/)(CNCF Sandbox 的內部開發者平台)。使用 Google Codelabs(`claat`)格式。

每一課都先講「先備知識」(為什麼這樣設計),再動手,最後有「自我檢核」。

| 課 | 主題 | 難度 |
|---|---|---|
| 01 | 5 分鐘跑起 OpenChoreo | 入門 |
| 02 | 架構與核心概念 | 入門 |
| 03 | 部署你的第一個 Component | 基礎 |
| 04 | 從原始碼建置 | 進階 |
| 05 | 多環境與 Promotion | 進階 |
| 06 | GitOps | 進階 |
| 07 | 可觀測性 | 進階 |
| 08 | 自訂 Golden Path | 進階 |
| 09 | 微服務實戰 | 進階 |
| 10 | AI 與 MCP 整合(選修) | 選修 |

## 預覽

```bash
./serve.sh          # 預設 8088,被占用會自動換 port
```

開啟 `http://localhost:<port>` 即可。

## 重建

```bash
go install github.com/googlecodelabs/tools/claat@latest
./build.sh
```

`build.sh` 會:檢查 callout 格式 → `claat export` → 套用 DevSite 主題 → 依 `tutorials/*.md` 重新產生首頁(`build_index.py` + `index.template.html`)。

## 目錄

```
tutorials/     教學原始檔(Markdown)
generated/     匯出的 HTML(可直接部署成靜態網站)
labs/          教學用的實驗檔案
  06-gitops/       Argo CD 實驗(git-server.yaml、application.yaml、publish.sh、repo-template/)
  08-golden-path/  自訂 ComponentType 與 Trait
  10-mcp/          極簡 MCP 客戶端(mcp_call.py)
claat-public/  codelab 的前端資源
```

## 驗證範圍與已知限制

教學中的指令是在下列環境實測的:OpenChoreo **v1.3.1**,k3d 單叢集,Linux。各課裡凡是**沒有實測**的地方都已明確標註(Negative 提示框),主要有:

* 需要瀏覽器登入的 `occ` 指令(`occ login`、`occ component logs`、`occ component deploy`)
* 第 6 課的 prune(刪檔案後資源被清除)
* 第 7、9 課的請求層級追蹤(只確認了 OTLP 匯出器自身的 span)
* 第 10 課在 AI 客戶端(Claude Code、Cursor…)的設定;內建 SRE / FinOps Agent
* 官方文件部分頁面(如 platform-engineer-guide 的 observability / component-types)當時回 404,相關內容依叢集實際的資源與行為整理

網路慢的環境(ghcr.io 下載)首次部署可能要很久,見第 4、7、9 課的說明。

## 注意

* 教學中的預設帳密(`admin@openchoreo.dev` / `Admin@123`、`service_mcp_client_secret`)是 OpenChoreo 本機實驗的公開預設值,**不可用於正式環境**。
* 實驗會在叢集建立並在課末清理資源;第 4、7 課安裝的 Workflow / Observability Plane 需要自行決定是否保留。
