# Spec: R2 题目多选与全选

## Requirement

用户在题库管理页面可以通过复选框选择多个题目，支持全选当前页功能。

## Scenarios

### S2.1: 单个题目选择

**Given**: 题目列表显示多条记录
**When**: 用户点击某行的复选框
**Then**: 该行被选中，工具栏显示"已选1题"

### S2.2: 全选当前页

**Given**: 当前页显示20条记录
**When**: 用户点击表头的全选复选框
**Then**: 当前页所有20条记录被选中，工具栏显示"已选20题"

### S2.3: 取消全选

**Given**: 当前页所有记录已被选中
**When**: 用户再次点击表头全选复选框
**Then**: 所有选中状态取消，工具栏隐藏批量操作按钮

### S2.4: 翻页后选中状态

**Given**: 用户在第1页选中3条记录
**When**: 用户翻到第2页
**Then**: 第1页的选中状态保持（可选：清空或保持）

**决策**: 翻页时清空选中状态（简化实现，避免跨页选中的复杂性）

## PBT Properties

### P2.1: 选中计数一致性

```
selectedCount === selectedIds.length
∧ selectedIds ⊆ currentPageQuestionIds
```

**Falsification**: 显示的选中数量与实际选中ID数组长度不一致

### P2.2: 全选幂等性

```
selectAll(); selectAll() ≡ selectAll()
```

**Falsification**: 连续两次全选操作后状态与一次全选不一致

## Implementation Constraints

- 使用`el-table`的`type="selection"`列
- 通过`@selection-change`事件获取选中行数组
- 选中状态存储在组件`ref`中，非全局store
