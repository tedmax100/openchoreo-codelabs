#!/usr/bin/env python3
"""依 tutorials/*.md 的 id 與 Duration 產生 generated/index.html(用 index.template.html)。"""
import glob, re

META = {
    "01": ("5 分鐘跑起 OpenChoreo", "本機安裝、部署範例、登入 Backstage", "入門"),
    "02": ("架構與核心概念", "期望狀態、五大 Plane、Project / Component / Workload / Release", "入門"),
    "03": ("部署你的第一個 Component", "occ CLI、手寫 YAML、追蹤 Release 與路由", "基礎"),
    "04": ("從原始碼建置", "CI/CD 概念、Workflow Plane、Dockerfile 建置、自動部署", "進階"),
    "05": ("多環境與 Promotion", "不可變制品、DeploymentPipeline、ReleaseBinding、晉升與回滾", "進階"),
    "06": ("GitOps", "GitOps 原則、Argo CD 同步、自動部署、漂移還原", "進階"),
    "07": ("可觀測性", "三大支柱、OpenTelemetry、日誌 / 指標 / 事件 / 追蹤", "進階"),
    "08": ("自訂 Golden Path", "平台工程、CEL、ComponentType、Trait、驗證規則", "進階"),
    "09": ("微服務實戰", "微服務與 gRPC、Resource、服務依賴、排錯演練", "進階"),
    "10": ("AI 與 MCP 整合", "LLM 工具呼叫、MCP、OAuth、權限與提示注入風險", "選修"),
}

cards = ""
for path in sorted(glob.glob("tutorials/*.md")):
    text = open(path, encoding="utf-8").read()
    num = path.split("/")[1][:2]
    slug = re.search(r"^id: (.*)$", text, re.M).group(1)
    minutes = sum(int(x) for x in re.findall(r"^Duration: (\d+)\s*$", text, re.M))
    title, desc, level = META[num]
    cards += (f'<a class="card" href="{slug}/index.html"><span class="n">{num}</span>'
              f'<h2>{title}</h2><p>{desc}</p><small>{level} · 約 {minutes} 分</small></a>')

tpl = open("index.template.html", encoding="utf-8").read()
open("generated/index.html", "w", encoding="utf-8").write(tpl.replace("@@CARDS@@", cards))
print("index.html: %d cards" % len(glob.glob("tutorials/*.md")))
