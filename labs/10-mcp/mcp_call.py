#!/usr/bin/env python3
"""極簡 MCP 客戶端:取得 client-credentials token,呼叫 OpenChoreo MCP 的工具。

用法:
  python3 -I mcp_call.py cp  __list__
  python3 -I mcp_call.py cp  list_projects '{"namespace_name":"default"}'
  python3 -I mcp_call.py obs query_component_logs '{"namespace":"default",...}'
"""
import base64, json, re, sys, urllib.parse, urllib.request

TOKEN_URL = "http://thunder.openchoreo.localhost:8080/oauth2/token"
CLIENT = ("service_mcp_client", "service_mcp_client_secret")  # 本機實驗用的預設值
SERVERS = {
    "cp": "http://api.openchoreo.localhost:8080/mcp",
    "obs": "http://observer.openchoreo.localhost:11080/mcp",
}


def get_token():
    auth = base64.b64encode(":".join(CLIENT).encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
        headers={"Authorization": "Basic " + auth,
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    return json.load(urllib.request.urlopen(req, timeout=15))["access_token"]


def rpc(url, token, method, params=None):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
    )
    text = urllib.request.urlopen(req, timeout=30).read().decode()
    m = re.search(r"data: (.*)", text)  # 回應是 SSE 格式
    return json.loads(m.group(1) if m else text)


def main():
    server, tool = sys.argv[1], sys.argv[2]
    args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    url, token = SERVERS[server], get_token()
    if tool == "__list__":
        tools = rpc(url, token, "tools/list")["result"]["tools"]
        print(len(tools), "tools")
        for t in tools:
            print("-", t["name"])
    else:
        r = rpc(url, token, "tools/call", {"name": tool, "arguments": args})
        print(json.dumps(r.get("result", r), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
