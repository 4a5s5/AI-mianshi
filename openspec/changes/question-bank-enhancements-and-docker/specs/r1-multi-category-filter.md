# Spec: R1 多题型筛选

## Requirement

用户在题库管理页面可以同时选择多个题型进行筛选，显示所有匹配题型的题目。

## Scenarios

### S1.1: 单题型筛选（向后兼容）

**Given**: 用户在筛选下拉框中选择"综合分析"
**When**: 点击筛选或按回车
**Then**: 列表仅显示category="综合分析"的题目

### S1.2: 多题型筛选

**Given**: 用户在筛选下拉框中选择"综合分析"和"组织协调"
**When**: 选择完成后自动触发筛选
**Then**: 列表显示category为"综合分析"或"组织协调"的所有题目

### S1.3: 清空筛选

**Given**: 用户已选择多个题型
**When**: 点击清空按钮
**Then**: 显示所有题型的题目

### S1.4: 与关键词筛选组合

**Given**: 用户选择题型"综合分析,人际关系"且输入关键词"领导"
**When**: 执行搜索
**Then**: 显示(category IN ('综合分析','人际关系')) AND (content LIKE '%领导%') 的题目

## PBT Properties

### P1.1: 筛选结果子集性

```
∀ categories ⊆ AllCategories:
  filter(categories).items ⊆ all_questions
  ∧ ∀ q ∈ filter(categories).items: q.category ∈ categories
```

**Falsification**: 返回的任意题目其category不在筛选条件中

### P1.2: 空筛选等价全集

```
filter([]) ≡ filter(AllCategories) ≡ all_questions
```

**Falsification**: 不选择任何题型时，返回结果与选择所有题型不一致

## Implementation Constraints

- 前端使用Element Plus的`el-select`组件，设置`multiple`属性
- 后端`category`参数接收逗号分隔字符串，使用`split(",")`解析
- SQL使用`IN`子句而非多个`OR`条件
