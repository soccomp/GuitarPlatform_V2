# CHANGELOG

格式：版本号 | 日期 | 更新内容

---

## [v0.3.0] - 2026-04-25

### 新增
- **小霞问答模块** — 基于 MiniMax-M2.7 的课程实时答疑
- **小霞陪练** — 根据课程主题生成循序渐进的练习任务
- 课程详情页问答浮层 UI（右下角悬浮面板）
- 练习任务弹窗（支持入门/进阶/高级三级难度）
- `POST /api/courses/{id}/ask` — 小霞 Q&A 接口
- `POST /api/courses/generate-practice` — 练习任务生成接口
- `GET /api/courses/{id}/stream` — 视频流地址接口

### 修复
- MiniMax API 模型名修正（`MiniMax-Text-01` → `MiniMax-M2.7`）

### 文档
- `docs/BRANCHES.md` — 分支策略与 commit 规范
- `docs/ISSUES.md` — Issue 跟踪表

---

## [v0.2.0] - 2026-04-25

### 新增
- **歌曲库模块** — 完整后端 + 前端
- 曲谱全屏浏览（PDF / GPX 渲染）
- 音频播放器（A-B 循环 / 速度调节 / 打点标记）
- `POST /api/songs/{id}/markers` — 打点接口
- `GET /api/songs/{id}/markers` — 获取标记接口

---

## [v0.1.0] - 2026-04-25

### 新增
- 项目基础结构（Vue3 + FastAPI）
- 课程列表 + 课程详情 API
- 视频播放支持
- Transcript 加载
- `.github/workflows/ci.yml` — GitHub Actions 自动检查
