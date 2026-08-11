# Mac 分享包说明

这份说明用于把平台发给另一台 Mac 使用，**不包含你的资源库内容**，只包含：

- 前端代码
- 后端代码
- 启动脚本
- 本地服务安装脚本
- 文档

不包含：

- `library/` 里的课程、学习视频、歌曲资源
- `backend/.env`
- 你的本地练习录音与会话数据
- `frontend/node_modules`
- `backend/.venv`

## 1. 生成分享包

在项目根目录执行：

```bash
scripts/build_shareable_mac_bundle.sh
```

生成产物：

```text
dist/share/GuitarPlatform_Mac_No_Resources.zip
```

## 2. 发给朋友的内容

把下面这个 zip 发给对方即可：

```text
dist/share/GuitarPlatform_Mac_No_Resources.zip
```

## 3. 朋友收到后的安装步骤

### 3.1 解压

建议解压到一个固定目录，例如：

```text
~/Applications/GuitarPlatform_Mac_No_Resources
```

或：

```text
~/Projects/GuitarPlatform_Mac_No_Resources
```

### 3.2 安装基础环境

对方机器需要：

- `python3`
- `npm`

可选但强烈建议：

- `ffmpeg`

说明：

- 没有 `python3` 无法启动后端
- 没有 `npm` 无法构建和预览前端
- 没有 `ffmpeg` 时，部分媒体处理和 transcript 能力会受限

### 3.3 安装本地服务

进入解压目录后，双击或执行：

```bash
scripts/install_local_services.command
```

这一步会自动：

- 创建空的 `library/` 目录结构
- 创建空的 `backend/data/index.json`
- 在 `~/Library/LaunchAgents/` 里安装前后端服务
- 启动本地服务

安装完成后访问：

```text
http://127.0.0.1:3000/
```

## 4. 日常使用

### 打开平台

双击：

```text
scripts/start_guitar_platform.command
```

### 控制服务

双击：

```text
scripts/control_guitar_platform.command
```

可执行：

- 重启服务
- 停止服务

## 5. 卸载本地服务

如果对方不再需要后台常驻服务，可执行：

```bash
scripts/uninstall_local_services.command
```

## 6. 首次使用后要做什么

因为分享包不带资源，所以对方第一次打开后需要自己往这些目录里放内容：

- `library/courses/`
- `library/collected/`
- `library/songs/`

然后再使用平台的扫描 / 整理能力。

## 7. 关于 API Key

分享包不会带你的真实 key。

如果对方要使用需要密钥的能力，应在自己的环境中创建：

```text
backend/.env
```

参考：

```text
backend/.env.example
```
