# Spec: R5 再次练习功能

## Requirement

用户完成练习后，可以选择用同样的题目再练一次，而不是返回选题页面。

## Scenarios

### S5.1: 单题再次练习

**Given**: 用户完成单题练习，在结果页查看分析
**When**: 点击"再次练习"按钮
**Then**: 保持当前题目，清空答题内容和分析结果，重新开始计时，进入作答阶段

### S5.2: 套卷再次练习

**Given**: 用户完成套卷练习（3道题），在结果页查看分析
**When**: 点击"再次练习"按钮
**Then**: 保持原有3道题目，重置倒计时为原始时限，清空所有答题内容，从第1题开始

### S5.3: 区分再次练习与换题练习

**Given**: 用户在结果页
**Then**: 显示两个按钮：
  - "再次练习"：保留题目，重新作答
  - "换题练习"（或"继续练习"）：返回选题页

### S5.4: 再次练习后的分析独立性

**Given**: 用户完成第一次练习（得分70），然后再次练习
**When**: 第二次练习完成并获得分析（得分85）
**Then**: 两次练习作为独立的答题记录保存，历史中显示两条记录

## PBT Properties

### P5.1: 题目状态保持

```
retry()
⟹ currentQuestion === previousQuestion
   ∧ transcript === ''
   ∧ analysisResult === null
```

**Falsification**: 再次练习后题目变化或之前答题内容未清空

### P5.2: 计时器重置

```
retry()
⟹ timer.elapsed === 0
   ∧ timer.isRunning === false (等待用户开始)
```

**Falsification**: 再次练习后计时器未归零

### P5.3: 独立记录生成

```
practice1 = complete()
retry()
practice2 = complete()
⟹ practice1.id ≠ practice2.id
   ∧ practice1.question_id === practice2.question_id
```

**Falsification**: 再次练习的结果覆盖了之前的记录

## Implementation Constraints

- PracticeResult组件新增`@retry`事件（与现有`@restart`区分）
- SinglePracticeView新增`handleRetry()`方法
- PaperPracticeView新增`handleRetry()`方法
- 不修改practiceStore的reset/resetPaper方法，新增独立的retry逻辑
