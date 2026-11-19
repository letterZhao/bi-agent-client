# BI client 1.2.1_test

测试预发布，包含完整 bi-query Skill、五个参考文件、四类 MCP 配置模板及安装说明。
使用必要的工具、参数和指标协议；不分发服务端实现或真实业务样例。

优化师筛选先使用 `bi_get_pitcher_list` 获取当前身份的候选，按 `nickName` 精确匹配，
不猜测人员或改用缩写。保留实时权限校验、同期群指标映射和模板查询流程。

服务地址由管理员私下提供，个人凭据只在客户端本地设置。
Windows Codex App 手动安装无需 Codex CLI、Git 或 Node.js，见 README。

下载安装：从本 Release 下载两个归档与 SHA256SUMS，校验后安装。
从 Git 安装时使用固定 `1.2.1_test` Tag，仓库为 `letterZhao/bi-agent-client`。

CI 仅验证公开发行文件、安全规则及归档构建，不访问业务服务。
内部业务测试与源码审查在内部环境执行，不上传原始验收记录。
发布不证明远程服务部署版本、个人鉴权或所有客户端自然语言场景已验收。
