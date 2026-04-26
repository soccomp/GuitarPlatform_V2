# CHANGELOG

格式：版本号 | 日期 | 更新内容

---

## [v1.0.0] - 2026-04-26

### 正式版
- 系统教材、学习视频、歌曲练习三大核心场景进入本地可用状态。
- 系统教材支持多套教材固定切换、树状章节浏览和课程视频播放。
- 学习视频支持目录扫描、真实视频封面卡片、弹窗播放和竖屏视频自适应。
- 歌曲练习支持 PDF/GP 打开、MP3 伴奏播放、进度条拖拽、A/B 打点循环和 0.60-1.00 变速。
- 小霞问答接入 MiniMax 国内 Token Plan Anthropic Messages 兼容接口。

### 技术
- 后端媒体接口支持 HTTP Range，解决视频、MP3、PDF、GP 预览/拖拽问题。
- 学习视频扫描自动生成 `.thumbnails` 封面并写入索引。
- `backend/.env` 本地读取 MiniMax 配置，并通过 `.gitignore` 防止密钥上传。
- 新增 `docs/DEVELOPMENT.md` 记录本地启动、配置、素材目录、扫描接口和验证命令。

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
