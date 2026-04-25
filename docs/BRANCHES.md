# 分支策略

## 分支结构

```
main          ─── 稳定版本，始终可部署
    │
    ├── feat/xxx  ─── 功能开发分支（命名：feat/功能名）
    ├── fix/xxx   ─── Bug 修复分支（命名：fix/问题描述）
    └── ref/xxx   ─── 重构分支（命名：ref/范围）
```

## 命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feat/功能名` | `feat/video-streaming` |
| 修复 | `fix/问题描述` | `fix/player-controls-zindex` |
| 重构 | `ref/范围` | `ref/songs-api` |
| 阶段 | `phase/N-描述` | `phase4-video-download` |

## 工作流程

```
1. 从 main 新建分支
   git checkout -b feat/awesome-feature

2. 开发 + commit（使用 commit 规范，见下方）

3. 推送分支
   git push -u origin feat/awesome-feature

4. 合并回 main
   - 方式 A：直接 merge（小型改动）
   - 方式 B：创建 Pull Request → review → merge（推荐）
```

## Commit 规范

格式：`type: 简短描述`

| type | 含义 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `ref` | 重构/优化 |
| `docs` | 文档更新 |
| `chore` | 杂项（依赖、配置） |
| `phase` | 阶段里程碑 |

示例：
```
feat: 小霞问答浮层 UI
fix: 音频播放器 A-B 循环重置问题
phase2: 歌曲库后端接口完成
```

## Issue 驱动流程

1. 哥提出需求/问题 → 我创 Issue
2. 从 Issue 派生出分支
3. 完成后 PR 关联 Issue
4. 合并后 Issue 自动关闭

示例分支名 → Issue 关联：
```
git checkout -b feat/video-download     # Issue #12
git commit -m "feat: 视频下载模块"       # commit message 包含 Issue 号更好
```
