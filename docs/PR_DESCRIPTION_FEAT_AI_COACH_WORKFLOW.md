# PR: advance learning coach and practice workflow

## Summary

这轮 PR 把平台从“本地资料管理器 + 局部播放器”继续推进成一个更完整的本地练琴工作台，重点覆盖三条主线：

1. `AI 学习教练`：把歌曲练习中的推荐系统做成可执行流程  
2. `内容知识库`：让系统教材和学习视频都具备 transcript、摘要、标签与优先补全能力  
3. `练琴工作流`：完善歌曲练习里的播放、录音、录像、混音、最近练习、多音频与打点片段体验

## Why

- 当前平台已经具备系统教材、学习视频、歌曲练习三大核心模块，但还缺少真正把三者串起来的“学习教练”能力。
- 学习视频和系统课程只有在 transcript / 摘要 / 标签体系下，才能变成长期可用的知识库，而不是本地播放器。
- `歌曲练习` 是最高频场景，需要从“能放伴奏”进一步升级成“能记录、能回看、能推荐下一步”的工作台。

## What changed

### 1. AI 学习教练

- `歌曲练习` 新增：
  - `下一步该练什么`
  - `推荐练习路径`
  - `今天这样练`
  - `今天练了什么`
- 支持：
  - checklist 勾选
  - 步骤状态切换
  - 按歌曲记忆
  - 今日轮次 / 累计轮次统计

### 2. 学习视频与系统教材内容画像

- 学习视频与系统课程统一接入：
  - 学习重点
  - 内容摘要
  - 适合怎么用
  - 关键点
  - transcript 预览
- 后端新增：
  - `course_intelligence`
  - `video_intelligence`
  - `learning_recommendations`
  - `content_backlog`

### 3. transcript 与知识库补全

- 学习视频支持：
  - 单条生成 transcript
  - 批量补 transcript
  - transcript 覆盖率
  - 优先补全清单
- 系统教材支持：
  - 单课生成 transcript
  - transcript 覆盖率
  - 优先补全清单
  - 刷新内容理解

### 4. 歌曲练习工作流升级

- 统一播放模式：
  - 正常播放
  - 内录混音
  - 音画同录
- 录制确认流：
  - `Save / Retry / Cancel`
- 支持：
  - 多音频伴奏切换
  - 打点片段保存 / 删除 / 套用
  - 最近练习快捷入口
  - 当前歌曲专属练习记录
  - 录制回放播放与下载

### 5. 4080 本地模型接入

- 新增 Windows `coach_node` 分析节点与脚本
- 顶部全局大模型状态条
- 顶部模型切换：
  - `Qwen 3 8B`
  - `DeepSeek R1 8B`

### 6. 交付与文档

- 新增 / 更新：
  - `docs/AI_PRODUCT_STRATEGY.md`
  - `docs/AI_LEARNING_COACH_V0_1.md`
  - `docs/PRODUCT_OPTIMIZATION_PRIORITIES.md`
  - `docs/KNOWLEDGE_BASE_ROADMAP.md`
  - `docs/WORKLOG_2026-05-04.md`
  - `docs/WORKLOG_2026-05-05.md`
  - `docs/MAC_SHARE_PACKAGE.md`
- 新增分享包脚本与本地服务安装脚本

## Scope

- [x] Frontend
- [x] Backend
- [x] Docs
- [x] Scripts / Local runtime

## Validation

- [x] `backend/.venv/bin/python -m unittest backend.tests.test_coach_sessions backend.tests.test_coach -v`
- [x] `python3 -m py_compile backend/routers/coach.py backend/routers/courses.py backend/routers/songs.py backend/routers/videos.py backend/services/coach.py backend/services/coach_sessions.py backend/services/index_store.py backend/services/indexer.py backend/services/resource_manager.py backend/services/content_backlog.py backend/services/course_intelligence.py backend/services/learning_recommendations.py backend/services/video_intelligence.py backend/services/video_matching.py`
- [x] `npm run build --prefix frontend`

## Notes

- `.gitignore` 已补充忽略：
  - `backend/data/coach_recordings/`
  - `backend/data/coach_sessions.json`
  - `dist/`
  - `coach_node.zip`
- 本轮不提交真实资源、录音录像、会话数据与本地环境文件。
