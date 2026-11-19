# BI MCP 客户端与 Skill

本仓库仅分发客户端配置、完整 Skill 和安装包，不包含服务端源码、真实业务数据或个人凭据。
服务地址由管理员通过内部渠道提供，示例 `https://mcp.example.com/mcp` 必须在本地替换。

完整 `bi-query` 包含按需读取的 `references/ad-performance-analysis.md`，可基于已支持报表分析广告效果、回收、订阅质量及系列/素材表现，并以可预览 HTML 展示来源、证据和未验证项。缺少回本目标时可先做相对比较；预算或暂停均为建议，不执行广告平台操作。无需额外安装广告分析 Skill。

## 下载与校验

从本仓库对应版本的 Release 下载三个附件：客户端 TAR、Skill ZIP 和 SHA256SUMS。
在 Windows PowerShell 中可执行以下命令。版本号以发布通知为准：

```powershell
$ErrorActionPreference = 'Stop'
$version = '1.2.1_test'
$dir = Join-Path $env:USERPROFILE "Downloads\bi-agent-$version"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Set-Location $dir
$base = "https://github.com/letterZhao/bi-agent-client/releases/download/$version"
foreach ($file in @("bi-agent-client-$version.tar.gz", "bi-query-skill-$version.zip", 'SHA256SUMS')) {
    Invoke-WebRequest -Uri "$base/$file" -OutFile $file
}
foreach ($line in Get-Content .\SHA256SUMS) {
    $expected, $file = $line.Trim() -split '\s+', 2
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $expected) {
        throw 'Checksum mismatch; stop installation'
    }
    Write-Host "OK: $file"
}
```

macOS/Linux 用户同样下载三个附件，执行 `shasum -a 256 -c SHA256SUMS` 或
`sha256sum -c SHA256SUMS`，通过后解压客户端 TAR。不要执行未经校验的安装脚本。

## Windows Codex App：无需 CLI

1. 在文件资源管理器中解压 Skill ZIP，把整个 `bi-query` 文件夹复制到
   `%USERPROFILE%\.agents\skills\`。保留 SKILL.md、全部 references（含 ad-performance-analysis.md）和 release.json。
   已有同名文件夹时先备份到技能扫描目录之外，不直接覆盖个人修改。
2. 登录管理员提供的 BI 网站，从自己的登录会话取得访问凭据。
   在 Windows“编辑账户的环境变量”中新增用户变量 `BI_ACCESS_TOKEN`，值仅为个人 token，
   不带 Bearer 前缀。不要将值粘贴到聊天、项目配置或本仓库。
3. 在 App 设置的 MCP servers 中添加 Streamable HTTP 服务，名称 `bi`，
   URL 填管理员提供的真实地址，Bearer token 环境变量填 `BI_ACCESS_TOKEN`。
   若界面没有环境变量项，在用户 `.codex/config.toml` 中合并以下配置，不覆盖其他服务器：

```toml
[mcp_servers.bi]
url = "https://mcp.example.com/mcp"
bearer_token_env_var = "BI_ACCESS_TOKEN"
startup_timeout_sec = 30
tool_timeout_sec = 600
```

4. 完全退出并重新打开 App，新建本地会话，输入：
   “使用 bi-query Skill，通过 BI MCP 查询我可以访问的项目列表。”
   `/mcp` 可查看连接状态。401 时检查个人凭据和 App 环境；
   环境未刷新时注销 Windows 后重新登录。不要绕过鉴权。

解压后的目录应为 `.agents/skills/bi-query/SKILL.md`，不要额外套一层同名文件夹。
WSL 或远程执行环境需要在实际执行 Agent 的环境安装和配置，不能依靠 Windows 主机目录自动生效。

## 从固定 Tag 安装

已安装 Git 和 Node.js ≥22.20 的用户，可在项目目录执行：

```bash
npx --yes skills@1.9.0 add 'https://github.com/letterZhao/bi-agent-client.git#1.2.1_test' --skill bi-query --agent codex --copy --yes
```

Claude Code 改用 `--agent claude-code`。无需 Node.js 的用户直接安装 ZIP。
Claude Code 的用户级技能目录为 `~/.claude/skills/bi-query`。

## 其他客户端与使用

配置模板和兼容说明位于 `docs/`。Skill 安装和 MCP 注册是两个独立步骤；
模板中的示例地址不能直接用于真实查询，个人凭据必须在客户端本地提供。
WorkBuddy 导入本版本 Skill ZIP；Harness 安装完整技能目录。

连接后先查询当前身份的项目候选，再按 Skill 选择报表、时间范围、时区、指标和筛选。
项目、人员、渠道等值必须来自真实授权候选，不猜测，不删除用户条件绕过权限。
工具不可用或没有真实返回时，应说明未执行，不能编造业务数值。

## 版本与兼容

`release.json` 中 `sourceCommit` 标识内部已验收源码，`distributionCommit` 标识公开发行提交；
二者不同是正常的。版本、工具数量、policyVersion、逐文件哈希和 Release 的 SHA256SUMS
用于核对安装包。不得用新包覆盖旧 Tag 或旧附件。
客户端发布不表示远程 MCP 已部署到同一提交，也不替代个人鉴权、四端或业务数据验收。
卸载只删除该技能和对应 MCP 配置，不会自动撤销个人凭据。
