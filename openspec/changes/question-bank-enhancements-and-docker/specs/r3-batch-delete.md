# Spec: R3 批量删除题目

## Requirement

用户选中多道题目后，可以一键删除。采用软删除策略，保留历史答题记录的完整性。

## Scenarios

### S3.1: 批量删除成功

**Given**: 用户选中5道无关联答题记录的题目
**When**: 点击"删除选中"按钮并确认
**Then**: 5道题目被软删除（is_deleted=True），从列表消失，提示"删除成功"

### S3.2: 批量删除含关联数据

**Given**: 用户选中3道题目，其中2道有关联的答题记录
**When**: 点击"删除选中"按钮并确认
**Then**: 3道题目全部被软删除，历史记录中这些题目显示"原题已删除"

### S3.3: 删除确认取消

**Given**: 用户选中题目并点击删除
**When**: 在确认对话框点击"取消"
**Then**: 无任何题目被删除，选中状态保持

### S3.4: 空选择时删除按钮

**Given**: 未选中任何题目
**Then**: "删除选中"按钮不显示或禁用

## API Specification

### POST /api/v1/questions/batch-delete

**Request Body**:
```json
{
  "ids": [1, 2, 3, 4, 5]
}
```

**Response 200**:
```json
{
  "deleted_count": 5,
  "message": "删除成功"
}
```

**Response 400** (空列表):
```json
{
  "detail": "请选择要删除的题目"
}
```

## PBT Properties

### P3.1: 软删除幂等性

```
batchDelete([1,2,3]); batchDelete([1,2,3])
⟹ questions(1,2,3).is_deleted === True
```

**Falsification**: 重复删除同一批ID导致错误或状态不一致

### P3.2: 删除后不可见性

```
∀ id ∈ deletedIds: id ∉ listQuestions().items.map(q => q.id)
```

**Falsification**: 软删除的题目仍出现在列表中

### P3.3: 历史记录完整性

```
∀ answer ∈ answers:
  answer.question_id ∈ deletedIds
  ⟹ answer.question.content === null ∧ answer.question.is_deleted === true
```

**Falsification**: 答题记录的关联题目信息丢失或不可访问

## Implementation Constraints

- Question模型新增`is_deleted: Column(Boolean, default=False)`
- 所有题目查询默认添加`.where(Question.is_deleted == False)`
- 删除API在单个事务中执行所有更新
