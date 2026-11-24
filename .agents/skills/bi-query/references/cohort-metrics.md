# 同期群（集群）指标

用 `bi://contracts/{tool_name}` 的 `queryCapabilities.cohortMetricGroups` 查完整选项及 `responsePath`。下面仅列容易混淆的映射；具体字段可用性、空值及业务提示以真实返回为准。

| 报表 | Tool | 分区/模式 | 返回指标位置 |
|---|---|---|---|
| IAA 同期表 | `bi_synchronism_report_list_new` | `whetherCohort: true`；`timeZone: Asia/Shanghai` 对应网页选择 | 行的直接字段 |
| IAP 同期表 | `bi_iap_subscribe_report` | 北京时间 `subTimeZone: 8`；UTC `0` | 行的直接字段 |
| 项目总表 | `bi_synthesize_report_list_new` | 按契约选择时间及分组 | 行的直接字段 |
| 用户标签分析 | `bi_query_ab_ltv_index_page` | 北京时间 `subTimeZone: 8`；UTC `0` | 行的直接字段 |
| 同期续订退款表 | `bi_iap_renew_refund_report` | 北京时间 `subTimeZone: 8`；UTC `0` | 行内 `metrics` 字典 |
| ROI 趋势表 | `bi_iap_cohort_roi_trend_report` | 北京时间 `subTimeZone: 8`；UTC `0` | 行内 `metrics` 字典 |

三张表按“日期、项目代号”分组时使用 `groupList: "day,app"`、`dimensionChecked: ["day", "app"]`；`dateDimension: "day"` 选择日粒度。不能把中文“日期”猜成 `date` 分组字段。

`showColChecked` 使用选择值，不能用组标题猜字段。`_d000` 是“全部”，返回字段去掉这一后缀；`_d0` 是 Day0。自然日与 `_24h_` 分别选择；卸载小时列使用 `_h1` 等，不能拼成 `_dh1`。只选契约列出的组合，不把所有日期和类型任意组合。

| 选择值 | 返回路径 | 含义 |
|---|---|---|
| `screen_impressions_d000` | `screenImpressions` | IAA 全屏广告全部展示次数 |
| `screen_impressions_d0` | `screenImpressionsD0` | IAA 自然日 Day0 展示次数 |
| `screen_impressions_24h_d0` | `screenImpressions24hD0` | IAA 24H Day0 展示次数 |
| `nav_banner_impression_per_d000` | `navBannerImpressionPer` | IAA 原生横幅人均展示次数 |
| `uninstall_users_rate_h1` | `uninstallUsersRateH1` | IAA 1 小时卸载率 |
| `roi_d7` | `roiD7` | IAP Day7 全部 ROI |
| `weekly_roi_d7` | `weeklyRoiD7` | IAP Day7 周订阅 ROI |
| `cohort_quarterly_unsubscribe_ratio_d14` | `cohortQuarterlyUnsubscribeRatioD14` | IAP Day14 季订阅取消率 |
| `monthly_trial_ratio_d000` | `monthlyTrialRatio` | IAP 月试用率，全部周期 |
| `quarterly_trial_purchase_ratio_d000` | `quarterlyTrialPurchaseRatio` | IAP 季试用转标率，全部周期 |
| `total_roi_d7` | `metrics.totalRoiD7` | ROI 趋势 Day7 总 ROI |
| `quarterly_roi_d740` | `metrics.quarterlyRoiD740` | ROI 趋势 Day740 季订阅 ROI |

IAA 同期表有 14 个指标组，包含广告类型、留存、卸载、LTV、每日收入和每日 ROI。IAP 有 9 组：ROI、取消率、退款率、计费重试人数、计费重试率、试用率、试用转标率、周订阅首次续订人数、周订阅首次续订率。ROI 趋势含总、广告、全部订阅、周/月/季/年订阅 7 种类型，后端支持完整 Day0—740（网页只列部分周期）；周期不是查询日期区间，也不证明历史样本已经成熟。

ROI 趋势的确切前缀如下；选择值是前缀加 `_d` 加周期，例如 Day7 广告 ROI 为 `iaa_roi_d7`。请按资源核对生成规则，可通过 `bi://cohort/bi_iap_cohort_roi_trend_report/iaa_roi_d7` 单独核验，避免读取数千个选项导致截断。返回路径在 `metrics` 中，按资源返回值读取，不能用默认累计 `totalRoi` 替代指定周期。

| ROI 趋势类型 | 选择值前缀 |
|---|---|
| 全部类型（包含广告及订阅） | `total_roi` |
| 广告 ROI | `iaa_roi` |
| 全部订阅 ROI | `iap_roi` |
| 周订阅 ROI | `weekly_roi` |
| 月订阅 ROI | `monthly_roi` |
| 季订阅 ROI | `quarterly_roi` |
| 年订阅 ROI | `yearly_roi` |

网页的“全部类型 ROI”是上表第一种类型，即广告及订阅收入合计的 `total_roi`。查询其 D0～D10 共 11 个指标：`total_roi_d0` 至 `total_roi_d10`，读取 `metrics.totalRoiD0` 至 `metrics.totalRoiD10`。只有用户明确要求七种类型分别返回时，才选择 77 个指标；不能把“全部类型”这个选项名称扩大解释为七类各查一遍。

IAA 同期 `roiD*`、`retentionRateD*`、`uninstallUsersRate*` 的原始比值由网页乘 100 后保留两位百分数；IAP 同期 ROI/取消率/试用率，以及 ROI 趋势的 ROI 已由后端乘 100 并保留两位，展示只添加 `%`。不要对整份响应做统一缩放；累计指标等其他字段按各自契约与网页格式处理。

IAP 的 `day7Roi`、`cohortWeeklyUnsubscribeRatioD0` 不支持非空数值筛选；MCP 对这两个非空条件返回 `FILTER_NOT_SUPPORTED` 并拒绝查询。不能删除用户条件、改为全部或在当前页自行过滤后宣称全量筛选已完成。可以按用户明确要求查询对应展示列；展示选择与数值筛选分别处理。其他比值筛选的阈值须核对原始单位，不能从返回百分数推定。

IAA `cohortMetricFilters` 仅接受契约白名单中的展示次数/人均展示次数/ECPM 及已登记操作符，不能把留存率等任意指标放入该筛选字典。ROI 趋势的展示指标不自动具有同名筛选参数。

保留 `null`、缺失字段和零的区别。未成熟、零分母、字段裁剪或无样本不自行解释成零；只在有有效契约和实际证据时说明原因。回答同时列出查询日期范围和同期群周期。

同期续订退款表按 `renew_purchasers` 和 `renew_rate` 两个父字段授权，四种订阅类型各支持第 1～200 次续订。例如 `weekly_renew_rate_d1` 返回 `metrics.weeklyRenewRateD1`；`d1` 在此表示续订次数，不是 Day1。显式字段、模板和返回投影均按当前用户的父字段、订阅类型及期数权限校验。中台全量定义不能代替当前账号权限。

IAP ROI 的周期按类型分别限定：`roi` 为 D0/3/7/10/14/17；`weekly_roi` 为 D0/3/7/10/14/17/21/28/35/42/45；`iaa_roi`、月/季/年 ROI 为 D0/3/7/14/17/21/28/35/42/45。两组首次周续订指标也采用后一组周期。不能从中台的类型与周期列表任意做笛卡尔积。用户标签 LTV 支持 D0/1/3/7/14/30，中台中的 D5 在当前固定前后端源码均不受支持，查询须拒绝。

动态选择值、父权限和返回路径使用同一有限注册表。`bi://cohort/{tool_name}/{selector}` 也能读取源码支持、但未在静态网页数组完整列出的动态字段。接口中出现零、null 或缺失仍按真实响应保留；完整映射不代表每个周期已有非空业务样本。

## IAA 同期表：日期粒度与 H-N（1.4.1 起）

`bi_synchronism_report_list_new` 用 `dateDimension` 选择 `hour`（小时）、`day`、`week`、`month`、`day_hour`（按日汇总的小时口径）。`hour` 由 MCP 转为上游小时开关，不等于 `day_hour`；不将两者混用。普通查询不提供时按日。

仅 `day` 和 `day_hour` 可选 `dataCutoffHours` 整数 1～23；H-3 为 3。范围须包含数据时区当天，N 不能超过当地当前小时；默认 Asia/Shanghai。实时省略参数，普通查询 null 也表示实时；模板用 `clearFields=["dataCutoffHours"]` 清除。不要传 0、字符串数字或空字符串。

用户明确指定 H-N 而条件不可执行时说明原因并追问调整，不改为实时或删截止条件；旧模板同样重新校验。IAA 模板可临时覆盖 dateDimension；与 timeGranularity/小时开关明确冲突时要求澄清。小时和日（小时口径）与国家分组/筛选冲突时停止，不静默去掉国家。

**日＋H-N：消耗及消耗衍生指标不准确，其余指标正常可参考。** 回答必须保留网页该提示，不自行纠正数值。注明粒度、时区、H-N、分页及刷新信息；H-N 不固定快照，跨截止小时或刷新批次的页不能拼成同批次全量。

提问示例：“沿用我的 IAA 同期模板，改为今天、日（小时口径）、+8 时区、截止 H-3”“改成小时粒度，并明确恢复实时”“保留日粒度，将数据截止改为 H-1”。所需项目、指标仍取真实候选；日期歧义先澄清，不伪造样本。
