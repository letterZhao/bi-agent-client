# 客户端连接与 Skill 安装

所有客户端使用管理员通过内部渠道提供的 Streamable HTTP 地址。
示例 `https://mcp.example.com/mcp` 必须由用户在本地替换；示例不包含可用凭据。

| 客户端 | MCP 模板 | 个人凭据 | Skill |
| --- | --- | --- | --- |
| Codex App / CLI | codex.toml.example | BI_ACCESS_TOKEN 进程环境变量 | 用户或项目的 .agents/skills/bi-query |
| Claude Code | claude.mcp.json.example | 请求头引用 ${BI_ACCESS_TOKEN} | .claude/skills/bi-query |
| DeepSeek Harness | deepseek-harness.yaml.example | ${credential:BI_ACCESS_TOKEN} 凭据提供方 | .dsh/skills/bi-query 或受支持的共享目录 |
| WorkBuddy | workbuddy.mcp.json.example | 在个人 MCP 配置中本地填写占位符 | 导入完整 Skill ZIP |

Codex App 的 Windows 手动安装与环境变量设置见包内 README。
模板需要合并，不覆盖其他服务。不要把个人配置、登录截图、Cookie 或业务响应上传到发行仓库。
不同客户端的变量语法不能混用；WorkBuddy 桌面版本不保证展开环境变量。
更新环境变量或个人配置后完全退出并重新启动客户端，使用新会话核对工具和技能状态。

验证分为：配置解析、工具连接、Skill 发现、自然语言实际调用、授权与业务结果对照。
某一层成功不能代替其他层验收。缺少或失效凭据必须拒绝访问，权限未知必须停止；
保留用户指定的筛选和指标，不以删除条件的方式取得数据。

macOS/Linux、Windows、WSL 和远程执行器在各自实际运行的环境配置。
本文不宣称所有客户端版本或操作系统均已实测；以发布说明中的实际验收范围为准。
