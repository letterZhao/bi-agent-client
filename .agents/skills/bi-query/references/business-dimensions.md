# 城市、负责人、产品组与广告类型

先读取当前目标报表契约。候选只证明值存在，不能替代目标报表菜单、字段及业务数据权限。

| 工具 | 返回字段 | 用途 |
| --- | --- | --- |
| bi_get_city_list | city、cityValue | cityValue 用于城市编码筛选；收入时区表 cityList 用 city，cityValueList 用编码。日报表与收入时区表 cityValue 为字符串，IAA 两表为整数。 |
| bi_get_principal_user | id、nickName | 负责人姓名精确对应 id，再传 principalIdList；不是优化师。 |
| bi_get_dept_tree | id、parentId、name、children | 完整产品组树，按真实名称定位节点。 |
| bi_get_ad_type_list | label、value | 项目总表与 IAA 同期表 adTypeList 使用 value。 |
| bi_get_ad_format_list | label、value | 收入时区报表 formatList 使用 value，不能混用 IAA 编码。 |
| bi_get_principal_dict | label、value | 收入对账表 principalNameList 使用 label；不能代替负责人 ID 列表。 |

产品组名称按当前完整部门树定位；仅可将英文大小写差异用于唯一候选名称定位，保留实际名称，不猜 ID。
选中父产品组时，收集本节点与全部递归子节点 ID，去重后作为 deptIdList，和网页产品组选择行为一致。
返回重名节点时向用户展示其部门路径并消歧，不自动选择第一个。直接提交的 deptIdList 精确按传入集合筛选，
不会由 MCP 自动扩展；保存模板继续保留原集合。不要将事业部名称筛选改成 business_group 分组。

例如用户输入“产品组：Fixture事业部”，应先调用树工具；若真实候选恰为某父节点，读取其当前 ID 和后代，
再用这些 ID 筛选日报表。这里不提供任何固定业务 ID 或长期缓存。

广告类型的 label 可能重名且对应不同 value，不能合并候选。用户指定的名称对应多个编码时询问其编码选择，
或仅在用户明确要求覆盖全部该名称类型时使用全部真实匹配编码。不能在两套字典间自行翻译。

当前有效组合：城市支持日报、项目总表、IAA 同期及收入时区表；产品组支持前三者及 IAP 同期表；负责人 ID
支持这些报表及收入时区、IAA 收入差异、收入对账表。收入对账表另有姓名筛选。广告类型支持两张 IAA 表及收入时区表。
日报表没有广告类型分组或筛选。其他报表仅继承同名 DTO 字段不代表可用，必须按当前契约拒绝不支持的组合。

完整空数组保留；负责人接口为空时不猜负责人 ID，不调用全部用户接口替代，不将姓名字典当作 ID 候选。
PARAM_NOT_ALLOWED 表示值不属于完整候选，不能据此声称已确认报表无权限；PARAM_VALIDATION_UNAVAILABLE 表示候选
调用、结构或完整性无法验证。两者都保留用户条件并停止该查询，不改查全部。
