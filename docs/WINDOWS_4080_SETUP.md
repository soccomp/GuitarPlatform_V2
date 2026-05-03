# Windows 4080 分析节点准备说明

编写日期：2026-05-03  
编写人：Codex

## 1. 目标

本文描述如何把带 `RTX 4080` 和 `Ollama` 的 Windows 笔记本准备成吉他学习平台的后台 AI 分析节点。

这个节点的职责不是替代主平台，而是负责：

- 节奏分析
- transcript 后处理
- 本地大模型老师式反馈
- 后续更重的音频 / 视频识别任务

## 2. 建议硬件

当前目标机器：

- Windows 11
- Dell X16 R1
- i9-13900HK
- 32GB RAM
- RTX 4080

该配置足够承担第一版分析任务。

## 3. 必装环境

### 3.1 Git

用于拉取代码和更新项目。

验证：

```powershell
git --version
```

### 3.2 Python 3.11

建议使用 `Python 3.11`。

验证：

```powershell
python --version
```

### 3.3 Node.js

如果这台机器未来也要直接运行前端或开发工具，建议安装 `Node.js 20+`。

验证：

```powershell
node --version
npm --version
```

### 3.4 ffmpeg / ffprobe

音视频分析必需。

验证：

```powershell
ffmpeg -version
ffprobe -version
```

### 3.5 Ollama

用于本地模型推理。

验证：

```powershell
ollama list
```

## 4. 建议准备的模型

第一阶段建议先选一个适合中文解释、能稳定输出老师式反馈的模型。

选择原则：

- 中文理解稳定
- 响应速度可接受
- 显存占用合理
- 指令跟随较稳

后续再根据实际效果更换模型，不建议在第一天就追求“最终最佳模型”。

## 5. 项目目录建议

建议把项目放在固定目录，例如：

```text
C:\GuitarPlatform_V2
```

如果只作为分析节点，也可以拆出独立的分析服务目录，例如：

```text
D:\GuitarCoachNode
```

## 6. 第一阶段要做的事

这台 Windows 机器第一阶段只需要承担一个新服务：

- `AI Coach Analysis Service`

建议职责：

- 接收平台上传的录音文件
- 执行节奏分析
- 结合上下文调用 Ollama
- 返回结构化练习反馈

不建议第一阶段就让它承担：

- 整个平台前后端全部常驻
- 实时摄像头复杂识别
- 大规模批处理所有音视频

当前仓库里已经包含这个服务骨架：

```text
coach_node/
```

它提供：

- `GET /health`
- `POST /api/coach/analyze-rhythm`

第一版职责：

- 接收 Mac 平台上传的录音
- 调用 Ollama 生成老师式反馈
- 返回结构化 JSON 给主平台

## 6.1 与 Scarlett 2i2 的配合方式

第一版建议用户把 `Scarlett 2i2` 接在 MacBook 上，而不是接在 4080 Windows 笔记本上。

推荐分工：

- `Scarlett 2i2` 负责把吉他音频送进 MacBook
- MacBook 平台负责录音和上传
- Windows 4080 节点只负责接收音频并分析

这样做的好处是：

- 用户练琴时仍然只面对主平台
- 音频采集和练习 UI 保持在同一台机器上
- 4080 节点专注做后台计算，不承担前台设备管理

也就是说，第一版的数据流更推荐：

- 吉他 -> `Scarlett 2i2` -> MacBook 平台录音
- MacBook 平台 -> Windows 4080 分析服务
- Windows 4080 -> 返回结构化反馈给平台

只有在后续需要更复杂的本地多轨分析时，才考虑把声卡直接挂到 Windows 分析节点上。

## 7. 与 Mac 平台的关系

MacBook 负责：

- 打开平台
- 录音 / 操作练习页面
- 展示分析结果

Windows 4080 负责：

- 接收分析请求
- 处理录音
- 生成结果

理想关系是：

- Mac 是前台
- Windows 4080 是后台 AI 节点

## 8. 网络要求

两台机器需要在同一局域网，或者至少可互相访问。

建议最终分析服务运行地址类似：

```text
http://192.168.x.x:9000
```

Mac 平台需要能访问这个地址。

第一版如果要让这条链路稳定工作，还要满足：

- MacBook 能稳定识别 `Scarlett 2i2`
- MacBook 浏览器或平台层能完成录音
- 上传到 Windows 节点的音频文件延迟和体积可接受

## 9. 第一轮验证清单

在 Windows 笔记本上，先确认以下都通过：

```powershell
git --version
python --version
ffmpeg -version
ffprobe -version
ollama list
```

在整条链路联调前，再额外确认：

- MacBook 插上 `Scarlett 2i2` 后系统可见
- 能从平台或浏览器拿到该输入设备录音
- MacBook 可以访问 Windows 分析节点地址
- Windows 节点能收到一段测试录音并返回结果

如果这些都 OK，这台机器就已经具备承担第一版分析节点的基础条件。

## 9.1 启动分析节点服务

在 Windows 机器上进入项目目录后，可以先这样启动：

```powershell
cd C:\GuitarPlatform_V2\coach_node
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:COACH_OLLAMA_MODEL="qwen3:8b"
.\.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 9000
```

启动后先验证：

```powershell
curl http://127.0.0.1:9000/health
```

如果返回 `{"ok":true,...}`，说明分析节点已经起来了。

## 9.1.1 推荐改成自动热重载

为了避免每次覆盖 `service.py` 后还要手工重启 `uvicorn`，仓库里已经提供：

```text
coach_node/start_coach_node.ps1
```

在 Windows 上以后建议直接运行：

```powershell
cd C:\GuitarPlatform_V2\coach_node
.\start_coach_node.ps1
```

这个脚本会：

- 自动检查 `.venv`
- 必要时自动安装依赖
- 自动设置 `OLLAMA_BASE_URL`
- 自动设置 `COACH_OLLAMA_MODEL`
- 用 `uvicorn --reload` 启动

这样后面只要覆盖：

- `main.py`
- `service.py`

保存后节点就会自动热重载，不需要再手工 `Ctrl + C` 重启。

## 9.2 Mac 平台如何指向分析节点

当 Windows 节点起来之后，在 MacBook 的：

```text
backend/.env
```

里加入：

```env
COACH_NODE_URL=http://192.168.x.x:9000/api/coach/analyze-rhythm
COACH_MODEL=qwen3:8b
COACH_NODE_TIMEOUT_SECONDS=90
```

然后重启 Mac 上的平台后端。

这样平台里的 `AI 陪练` 就会：

- 优先把录音发给 Windows 4080 节点
- 如果节点不可用，再自动回退到本地 preview 反馈

## 10. 后续扩展方向

准备完成后，后续可以继续扩展：

- 节奏分析 API
- transcript 批量生成
- Ollama 老师式反馈
- 练习历史总结
- 视频动作识别

## 11. 结论

这台 4080 Windows 笔记本不只是“另一台能跑平台的电脑”，而是未来 AI 吉他陪练系统的后台算力核心。

第一版最适合先让它承担：

- 节奏分析
- 本地模型反馈

等这一层稳定之后，再继续扩展到音高识别、拨弦动作识别和更接近真人老师的指导体验。
