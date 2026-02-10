# Spec: R4 从题库开始练习

## Requirement

用户在题库管理页面选中题目后，可以直接以这些题目开始练习，无需手动创建套卷。

## Scenarios

### S4.1: 单题练习

**Given**: 用户在题库管理页选中1道题目
**When**: 点击"开始练习"按钮
**Then**: 跳转到单题练习页面，直接进入作答阶段，显示该题目

### S4.2: 多题套卷练习

**Given**: 用户在题库管理页选中3道题目
**When**: 点击"开始练习"按钮
**Then**: 弹出时限设置对话框（默认15分钟）

**When**: 用户设置时限为20分钟并确认
**Then**: 跳转到套卷练习页面，直接进入作答阶段，倒计时20分钟

### S4.3: 时限设置范围

**Given**: 时限设置对话框显示
**Then**: 时限输入范围为1-60分钟，步长1分钟

### S4.4: 未选择题目时按钮状态

**Given**: 未选中任何题目
**Then**: "开始练习"按钮不显示或禁用

## PBT Properties

### P4.1: 题目顺序保持

```
selectedOrder = [id1, id2, id3]
⟹ practiceQuestions.map(q => q.id) === [id1, id2, id3]
```

**Falsification**: 练习中题目顺序与选择顺序不一致

### P4.2: 时限传递正确性

```
userSetTimeLimit = 1200 (20min)
⟹ paperTimer.total === 1200
```

**Falsification**: 设置的时限与实际倒计时不一致

## Implementation Constraints

- 使用Vue Router的`query`参数传递题目ID和时限
- 单题模式: `/single-practice?questionId=123`
- 套卷模式: `/paper-practice?questionIds=1,2,3&timeLimit=1200`
- 练习页面`onMounted`时检查query参数，有则跳过选题步骤
