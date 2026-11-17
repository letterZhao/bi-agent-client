# 同期群（集群）指标

用 `bi://contracts/{tool_name}` 的 `queryCapabilities.cohortMetricGroups` 查完整选项及 `responsePath`。下面仅列容易混淆的映射；具体字段可用性、空值及业务提示以真实返回为准。

| 报表 | Tool | 分区/模式 | 返回指标位置 |
|---|---|---|---|
| IAA 同期表 | `bi_synchronism_report_list_new` | `whetherCohort: true`；`timeZone: Asia/Shanghai` 对应网页选择 | 行的直接字段 |
| IAP 同期表 | `bi_iap_subscribe_report` | 北京时间 `subTimeZone: 8`；UTC `0` | 行的直接字段 |
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

IAA 同期表有 14 个指标组，包含广告类型、留存、卸载、LTV、每日收入和每日 ROI。IAP 有 7 组：ROI、取消率、退款率、计费重试人数、计费重试率、试用率、试用转标率。ROI 趋势含总、广告、全部订阅、周/月/季/年订阅 7 种类型，周期为 Day0—365 以及 370、540、730、740；周期不是查询日期区间，也不证明历史样本已经成熟。

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

IAA `cohortMetricFilters` 仅接受契约白名单中的展示次数/人均展示次数及已登记操作符，不能把留存率等任意指标放入该筛选字典。ROI 趋势的展示指标不自动具有同名筛选参数。

保留 `null`、缺失字段和零的区别。未成熟、零分母、字段裁剪或无样本不自行解释成零；只在有有效契约和实际证据时说明原因。回答同时列出查询日期范围和同期群周期。
