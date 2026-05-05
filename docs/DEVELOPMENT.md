# 开发与本地运行

本文记录当前 `v1.1.0` 正式可用版的本地开发、配置、素材目录和验证流程。

## 1. 本地启动

当前版本默认使用后台常驻服务。日常访问直接打开：

```text
http://127.0.0.1:3000/
```

如需主动唤醒平台，可使用桌面启动器或脚本：

```bash
scripts/start_guitar_platform.command
```

如需管理服务状态，可使用：

```bash
scripts/control_guitar_platform.command
```

服务端口：

- 前端 Vite：`127.0.0.1:3000`
- 后端 FastAPI：`127.0.0.1:8000`

当前桌面入口：

- `吉他学习平台启动器.app`：唤醒后台服务并打开平台
- `吉他学习平台服务控制器.app`：重启服务 / 停止服务

## 2. MiniMax Token Plan 配置

真实密钥只放本地文件，不提交 GitHub：

```text
backend/.env
```

内容示例：

```env
MINIMAX_API_KEY=你的MiniMax国内TokenPlanKey
MINIMAX_BASE_URL=https://api.minimaxi.com/anthropic/v1/messages
```

说明：

- `backend/.env` 已被 `.gitignore` 忽略，不会上传 GitHub。
- `backend/.env.example` 只保留示例字段，可以提交。
- 当前小霞问答使用 MiniMax 国内 Token Plan 的 Anthropic Messages 兼容接口。
- 修改 `.env` 后需要重启后端服务。

## 3. 素材目录

平台通过 `library/` 目录扫描本地素材：

```text
library/
  courses/      系统教材视频与课程资料
  collected/    学习视频
  songs/        歌曲谱、伴奏、GP/PDF
```

学习视频扫描会生成封面：

```text
library/collected/.thumbnails/
```

`library/*` 下的真实素材默认不提交 GitHub。

## 4. 数据索引

当前索引文件：

```text
backend/data/index.json
```

常见扫描入口：

- 系统教材：`GET /api/courses/scan?persist=true`
- 学习视频：`GET /api/videos/scan?persist=true`
- 歌曲练习：`GET /api/songs/scan?persist=true`

学习视频索引包含 `thumbnail` 字段，前端卡片会优先显示真实视频封面。

## 5. 资源管理

当前版本支持平台内直接删除资源：

- 系统教材：删除当前课时，同时清理该课时视频、笔记和随课资料
- 学习视频：删除当前视频，同时清理对应缩略图
- 歌曲练习：删除整首歌曲目录及其谱、伴奏、参考资料

删除后会自动更新索引，无需手动编辑 `backend/data/index.json`。

## 6. 核心功能状态

当前正式版已打通：

- 系统教材：多套教材切换、树状章节、课程视频播放、小霞问答。
- 学习视频：本地视频扫描、真实封面卡片、弹窗播放、竖屏视频自适应。
- 歌曲练习：PDF/GP 打开、MP3 伴奏播放、进度拖拽、A/B 打点循环、变速练习、谱子弹窗底部紧凑播放器。
- 媒体服务：视频、音频、PDF、GP 均支持 HTTP Range 请求。

## 7. 验证命令

提交前至少执行：

```bash
python3 -m unittest discover -s backend/tests -v
npm run build --prefix frontend
python3 -m py_compile backend/main.py backend/routers/courses.py backend/routers/songs.py backend/routers/videos.py
```

当前后端测试覆盖：

- 索引扫描与路径安全
- 歌曲版本识别
- 学习视频缩略图路径
- 资源删除与索引刷新
- 媒体 Range 响应
- MiniMax `.env` 读取与响应解析

## 8. 安全注意

- 不要提交 `backend/.env`。
- 不要把 MiniMax API Key 写入代码、文档或 commit message。
- 如果小霞报鉴权错误，先确认 `backend/.env` 里的 `MINIMAX_BASE_URL` 是否为 Token Plan 接口。

## 9. AI 规划文档

当前 AI 相关规划建议优先参考：

- `docs/AI_COACH_V0_1.md`
  说明 AI 陪练录音、分析节点和基础反馈链路。
- `docs/AI_PRODUCT_STRATEGY.md`
  说明哪些 AI 功能应该保留、弱化或暂缓，以及后续更重要的“AI 学习教练 / 内容推荐系统”方向。
- `docs/AI_LEARNING_COACH_V0_1.md`
  说明 AI 学习教练 v0.1 的可开发功能清单，包括先做哪些数据分析、页面如何展示“下一步该练什么”、以及怎样把相关课程和学习视频推送给用户。
- `docs/PRODUCT_OPTIMIZATION_PRIORITIES.md`
  说明当前平台后续最值得做的产品优化，分为“立即做 / 下一阶段 / 暂缓”三档，便于后续排优先级。
- `docs/WORKLOG_2026-05-04.md`
  记录 2026-05-04 这轮开发的完整总结，包括学习教练、知识库、transcript 工作流和当前版本判断。
- `docs/WORKLOG_2026-05-05.md`
  记录 2026-05-05 这轮开发的完整总结，包括 4080 本地模型接入、AI 学习教练落地、歌曲练习录音录像工作流与界面交互收口。
- `docs/KNOWLEDGE_BASE_ROADMAP.md`
  记录系统教材与学习视频的知识库补全路线图，说明 transcript、摘要、标签和推荐系统后续如何继续推进。
- `docs/MAC_SHARE_PACKAGE.md`
  说明如何生成不带资源的 Mac 分享包，以及对方收到后如何安装本地服务并启动平台。
- `docs/CHANGELOG.md`
  记录当前正式版与开发中的阶段性版本进展，最新一轮开发汇总见 `v1.2.0-dev`。
