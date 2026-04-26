# Issue 跟踪

> 格式：`[ ] 待办  [x] 已完成  [!] 进行中`
> 每个 Issue 关联分支：`feat/issue-NN-描述`

---

## 功能需求

- [ ] **#1** 视频下载模块（B站/小红书/YouTube）
  - 关联分支：`feat/video-download`
  - 优先级：高
  - 备注：Phase4 内容

- [ ] **#2** Whisper 课程转录自动化
  - 关联分支：`feat/whisper-transcribe`
  - 优先级：中
  - 备注：上传视频后自动生成 transcript

- [ ] **#3** 课程进度跟踪（学完哪节课）
  - 关联分支：`feat/course-progress`
  - 优先级：中
  - 备注：需要数据库支持

## Bug

- [ ] **#4** 音频播放器速度调节时 A-B 循环点偏移
  - 关联分支：`fix/player-ab-loop`
  - 优先级：低
  - 备注：切换速度后 currentTime 应重置

## 技术优化

- [ ] **#5** 歌曲列表虚拟滚动（200+ 歌曲性能）
  - 关联分支：`ref/songs-virtual-scroll`
  - 优先级：低
  - 备注：数据量大时考虑

- [ ] **#6** PDF/GP 全屏模式添加手势支持
  - 关联分支：`ref/fullscreen-gesture`
  - 优先级：低

## 已完成

- [x] **#1** ~~Phase1 项目基础结构~~ → `phase1`
- [x] **#2** ~~Phase2 歌曲库模块~~ → `phase2`
- [x] **#3** ~~Phase3 小霞问答~~ → `phase3`
- [x] **#4** ~~课程视频流媒体支持~~ → `phase3`
- [x] **#5** ~~学习视频卡片流与真实封面~~ → `v1.0.0`
- [x] **#6** ~~本地媒体 Range 播放修复~~ → `v1.0.0`
- [x] **#7** ~~MiniMax Token Plan 小霞配置~~ → `v1.0.0`
