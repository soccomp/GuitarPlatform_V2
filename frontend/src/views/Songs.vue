<template>
  <div class="songs-view">
    <div class="songs-layout">
      <aside class="song-list">
        <div class="list-header">
          <div>
            <h2>歌曲练习</h2>
            <p>围绕谱面和伴奏快速进入练习状态</p>
          </div>
          <button class="ghost-btn" @click="scanSongs">扫描目录</button>
        </div>

        <label class="search-box">
          <span>快速定位</span>
          <input v-model.trim="searchQuery" type="text" placeholder="搜索歌曲名或版本关键词" />
        </label>

        <div v-if="loading" class="state-box">加载歌曲中...</div>
        <div v-else-if="songs.length === 0" class="state-box">
          暂无歌曲，可先将文件放到 `library/songs/`
        </div>
        <div v-else-if="filteredSongs.length === 0" class="state-box">
          没找到匹配的歌曲，换个关键词试试
        </div>
        <button
          v-for="song in filteredSongs"
          v-else
          :key="song.id"
          :class="['song-card', { active: selectedSong?.id === song.id }]"
          @click="selectSong(song)"
        >
          <strong>{{ song.title }}</strong>
          <p>{{ song.artist || '未填写歌手' }}</p>
          <span>{{ song.versions.length }} 个版本</span>
        </button>
      </aside>

      <section class="song-detail">
        <div v-if="!selectedSong" class="state-box">
          选择左侧歌曲开始练习
        </div>
        <template v-else>
          <div class="detail-header">
            <div>
              <h3>{{ selectedSong.title }}</h3>
              <p>{{ selectedSong.artist || '未填写歌手' }}</p>
            </div>
            <span class="path-pill">{{ selectedSong.path }}</span>
          </div>

          <div class="versions-section">
            <div class="section-heading">
              <h4>版本导航</h4>
              <span class="section-copy">{{ versionGroups.length }} 个主版本</span>
            </div>

            <div class="group-grid">
              <button
                v-for="group in versionGroups"
                :key="group.name"
                :class="['group-item', { active: currentGroupName === group.name }]"
                @click="selectVersionGroup(group)"
              >
                <strong>{{ group.name }}</strong>
                <small>{{ groupSummary(group) }}</small>
              </button>
            </div>

            <div v-if="currentVersionGroup?.segments?.length" class="segments-section">
              <div class="section-heading">
                <h4>练习段落</h4>
                <span class="section-copy">
                  {{ currentVersionGroup.segments.length }} 个段落
                </span>
              </div>

              <div class="versions-grid">
                <button
                  v-if="currentVersionGroup.root"
                  :class="['version-item', { active: selectedVersion === currentVersionGroup.root.name }]"
                  @click="selectVersion(currentVersionGroup.root)"
                >
                  <span>整版资料</span>
                  <small>{{ versionSummary(currentVersionGroup.root) }}</small>
                </button>
                <button
                  v-for="version in currentVersionGroup.segments"
                  :key="version.name"
                  :class="['version-item', { active: selectedVersion === version.name }]"
                  @click="selectVersion(version)"
                >
                  <span>{{ versionLeafLabel(version.name) }}</span>
                  <small>{{ versionSummary(version) }}</small>
                </button>
              </div>
            </div>

            <div v-else class="versions-grid">
              <button
                v-for="version in selectedSong.versions"
                :key="version.name"
                :class="['version-item', { active: selectedVersion === version.name }]"
                @click="selectVersion(version)"
              >
                <span>{{ version.name }}</span>
                <small>{{ versionSummary(version) }}</small>
              </button>
            </div>
          </div>

          <div class="player-section" v-if="selectedVersion">
            <div class="player-header">
              <span>当前版本：{{ selectedVersion }}</span>
              <button class="play-btn" :disabled="!currentAudioFile" @click="togglePlay">
                {{ isPlaying ? '暂停' : '播放' }}
              </button>
            </div>

            <div class="progress-panel" @click="seekAudio">
              <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
            </div>
            <div class="time-row">
              <span>{{ formatTime(currentTime) }}</span>
              <span>{{ formatTime(duration) }}</span>
            </div>

            <div class="control-row">
              <button :class="{ active: loopStart !== null }" @click="setLoopStart">
                A {{ loopStart === null ? '--:--' : formatTime(loopStart) }}
              </button>
              <button :class="{ active: loopEnd !== null }" @click="setLoopEnd">
                B {{ loopEnd === null ? '--:--' : formatTime(loopEnd) }}
              </button>
              <button @click="clearLoop">清除循环</button>
            </div>

            <div class="control-row speed-row">
              <span>速度</span>
              <button
                v-for="speed in speeds"
                :key="speed"
                :class="{ active: playbackRate === speed }"
                @click="setSpeed(speed)"
              >
                {{ speed }}x
              </button>
            </div>

            <div class="score-section">
              <div class="score-header">
                <h4>谱面与标记</h4>
                <button class="ghost-btn" :disabled="!currentAudioFile" @click="addMarker">
                  添加标记
                </button>
              </div>

              <div class="score-actions">
                <button v-if="selectedVersionFiles.pdf" @click="openScore('pdf')">打开 PDF</button>
                <button v-if="selectedVersionFiles.gp" @click="openScore('gp')">打开 GP</button>
                <a
                  v-if="referenceFiles.video"
                  :href="buildSongMediaUrl(referenceFiles.video)"
                  target="_blank"
                  rel="noreferrer"
                >
                  打开参考视频
                </a>
                <a
                  v-if="referenceFiles.image"
                  :href="buildSongMediaUrl(referenceFiles.image)"
                  target="_blank"
                  rel="noreferrer"
                >
                  打开参考图片
                </a>
              </div>

              <div class="media-hints">
                <span v-if="selectedVersionFiles.audio">当前版本有伴奏</span>
                <span v-else>当前版本没有独立伴奏</span>
                <span v-if="referenceFiles.video">同组带参考视频</span>
                <span v-if="referenceFiles.image">同组带参考图</span>
              </div>

              <div class="markers-list" v-if="visibleMarkers.length">
                <button
                  v-for="(marker, index) in visibleMarkers"
                  :key="`${marker.version}-${index}`"
                  class="marker-item"
                  @click="seekToTime(marker.time)"
                >
                  <strong>{{ formatTime(marker.time) }}</strong>
                  <span>{{ marker.label }}</span>
                </button>
              </div>
              <div v-else class="empty-copy">当前版本暂无标记</div>
            </div>
          </div>
        </template>
      </section>
    </div>

    <div v-if="showScoreModal" class="score-modal" @click.self="closeScoreModal">
      <div class="score-modal-content">
        <div class="score-modal-header">
          <span>{{ selectedSong?.title }} / {{ selectedVersion }}</span>
          <div class="score-modal-actions">
            <a v-if="scoreUrl" class="ghost-link" :href="scoreUrl" target="_blank" rel="noreferrer">
              打开原文件
            </a>
            <button class="ghost-btn" @click="closeScoreModal">关闭</button>
          </div>
        </div>

        <div class="score-viewer">
          <div v-if="scoreNotice" class="score-notice">{{ scoreNotice }}</div>
          <div v-if="scoreType === 'gp'" class="gp-shell">
            <div v-if="gpLoading" class="empty-copy">正在加载 GP 谱...</div>
            <div v-else-if="gpError" class="empty-copy">
              {{ gpError }}
              <a class="inline-score-link" :href="scoreUrl" target="_blank" rel="noreferrer">打开原始 GP 文件</a>
            </div>
            <div v-else ref="gpContainer" class="gp-container"></div>
          </div>
          <div v-else class="pdf-container">
            <iframe :src="scoreUrl" title="PDF 曲谱预览"></iframe>
          </div>
        </div>

        <div class="modal-audio-controls">
          <div class="modal-transport">
            <button :disabled="!currentAudioFile" @click="togglePlay">{{ isPlaying ? '暂停' : '播放' }}</button>
            <span>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
            <button @click="setLoopStart">设 A</button>
            <button @click="setLoopEnd">设 B</button>
          </div>
          <input
            class="modal-seek"
            type="range"
            min="0"
            :max="duration || 0"
            step="0.1"
            :value="currentTime"
            :disabled="!duration"
            @input="seekAudioRange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import seedIndex from '../../../backend/data/index.json'

export default {
  name: 'SongsView',
  data() {
    return {
      songs: [],
      loading: false,
      selectedSong: null,
      selectedVersion: '',
      selectedVersionFiles: {},
      searchQuery: '',
      audio: null,
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      playbackRate: 1,
      speeds: [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0],
      loopStart: null,
      loopEnd: null,
      showScoreModal: false,
      scoreType: 'pdf',
      scoreUrl: '',
      pdfDoc: null,
      gpApi: null,
      gpLoading: false,
      gpError: '',
      scoreNotice: '',
    }
  },
  computed: {
    currentAudioFile() {
      return this.selectedVersionFiles.audio || ''
    },
    filteredSongs() {
      const keyword = this.searchQuery.trim().toLowerCase()
      if (!keyword) return this.songs
      return this.songs.filter(song => {
        const haystacks = [
          song.title,
          song.artist,
          ...(song.versions || []),
        ]
        return haystacks.some(value => (value || '').toLowerCase().includes(keyword))
      })
    },
    progressPercent() {
      if (!this.duration) return 0
      return Math.min((this.currentTime / this.duration) * 100, 100)
    },
    visibleMarkers() {
      if (!this.selectedSong || !this.selectedVersion) return []
      return (this.selectedSong.markers || []).filter(marker => marker.version === this.selectedVersion)
    },
    versionGroups() {
      if (!this.selectedSong?.versions?.length) return []
      const groups = new Map()

      this.selectedSong.versions.forEach(version => {
        const segments = version.name.split(' / ').map(part => part.trim()).filter(Boolean)
        const groupName = segments[0] || version.name

        if (!groups.has(groupName)) {
          groups.set(groupName, { name: groupName, root: null, segments: [] })
        }

        const group = groups.get(groupName)
        if (segments.length <= 1 || version.name === '默认版') {
          group.root = version
        } else {
          group.segments.push(version)
        }
      })

      return Array.from(groups.values())
    },
    currentGroupName() {
      if (!this.selectedVersion) return ''
      return this.selectedVersion.split(' / ')[0]
    },
    currentVersionGroup() {
      if (!this.currentGroupName) return null
      return this.versionGroups.find(group => group.name === this.currentGroupName) || null
    },
    referenceFiles() {
      const group = this.currentVersionGroup
      return group?.root?.files || {}
    },
  },
  async mounted() {
    this.initAudio()
    await this.loadSongs()
  },
  beforeUnmount() {
    if (this.audio) {
      this.audio.pause()
      this.audio.src = ''
    }
    this.destroyGpApi()
  },
  methods: {
    initAudio() {
      this.audio = new Audio()
      this.audio.addEventListener('timeupdate', () => {
        this.currentTime = this.audio.currentTime
        if (
          this.loopStart !== null
          && this.loopEnd !== null
          && this.loopEnd > this.loopStart
          && this.audio.currentTime >= this.loopEnd
        ) {
          this.audio.currentTime = this.loopStart
        }
      })
      this.audio.addEventListener('loadedmetadata', () => {
        this.duration = this.audio.duration || 0
      })
      this.audio.addEventListener('play', () => {
        this.isPlaying = true
      })
      this.audio.addEventListener('pause', () => {
        this.isPlaying = false
      })
      this.audio.addEventListener('ended', () => {
        this.isPlaying = false
      })
    },
    async loadSongs() {
      this.loading = true
      try {
        const response = await fetch('/api/songs')
        if (!response.ok) throw new Error('歌曲列表加载失败')
        this.songs = await response.json()
      } catch (error) {
        this.songs = seedIndex.songs.map(song => ({
          id: song.id,
          title: song.title,
          artist: song.artist || '',
          versions: song.versions.map(version => version.name),
        }))
      } finally {
        if (!this.selectedSong && this.songs.length) {
          await this.selectSong(this.songs[0])
        }
        this.loading = false
      }
    },
    async scanSongs() {
      this.loading = true
      try {
        await fetch('/api/songs/scan?persist=true')
        await this.loadSongs()
      } finally {
        this.loading = false
      }
    },
    async selectSong(song) {
      this.stopAudio()
      try {
        const response = await fetch(`/api/songs/${song.id}`)
        if (!response.ok) throw new Error('歌曲详情加载失败')
        this.selectedSong = await response.json()
      } catch {
        this.selectedSong = seedIndex.songs.find(item => item.id === song.id) || null
      }
      if (!this.selectedSong) return
      if (this.selectedSong.versions?.length) {
        this.selectVersion(this.selectedSong.versions[0])
      }
    },
    selectVersion(version) {
      this.selectedVersion = version.name
      this.selectedVersionFiles = version.files || {}
      this.loopStart = null
      this.loopEnd = null
      this.stopAudio()
      if (this.currentAudioFile) {
        this.audio.src = this.buildSongMediaUrl(this.currentAudioFile)
        this.audio.load()
        this.audio.playbackRate = this.playbackRate
      }
    },
    selectVersionGroup(group) {
      if (group.segments?.length) {
        this.selectVersion(group.segments[0])
        return
      }

      if (group.root) {
        this.selectVersion(group.root)
      }
    },
    async togglePlay() {
      if (!this.currentAudioFile) return
      if (this.audio.paused) {
        await this.audio.play()
      } else {
        this.audio.pause()
      }
    },
    stopAudio() {
      if (!this.audio) return
      this.audio.pause()
      this.audio.currentTime = 0
      this.currentTime = 0
      this.duration = 0
    },
    seekAudio(event) {
      if (!this.duration) return
      const rect = event.currentTarget.getBoundingClientRect()
      const percent = (event.clientX - rect.left) / rect.width
      this.audio.currentTime = Math.max(0, Math.min(this.duration, percent * this.duration))
    },
    seekAudioRange(event) {
      if (!this.audio || !this.duration) return
      this.audio.currentTime = Math.max(0, Math.min(this.duration, Number(event.target.value)))
    },
    setSpeed(speed) {
      this.playbackRate = speed
      if (this.audio) {
        this.audio.playbackRate = speed
      }
    },
    setLoopStart() {
      this.loopStart = this.clampAudioTime(this.audio.currentTime)
      if (this.loopEnd !== null && this.loopEnd <= this.loopStart) {
        this.loopEnd = null
      }
    },
    setLoopEnd() {
      const end = this.clampAudioTime(this.audio.currentTime)
      if (this.loopStart !== null && end <= this.loopStart) {
        this.loopStart = Math.max(0, end - 0.5)
      }
      this.loopEnd = end
    },
    clearLoop() {
      this.loopStart = null
      this.loopEnd = null
    },
    seekToTime(time) {
      this.audio.currentTime = time
      if (this.audio.paused) {
        this.audio.play().catch(() => {})
      }
    },
    clampAudioTime(time) {
      const value = Number.isFinite(time) ? time : 0
      if (!this.duration) return Math.max(0, value)
      return Math.max(0, Math.min(this.duration, value))
    },
    formatTime(seconds) {
      if (!Number.isFinite(seconds)) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    versionSummary(version) {
      const files = []
      if (version.files?.audio) files.push('伴奏')
      if (version.files?.pdf) files.push('PDF')
      if (version.files?.gp) files.push('GP')
      if (version.files?.video) files.push('视频')
      if (version.files?.image) files.push('图片')
      return files.join(' / ') || '无媒体'
    },
    versionLeafLabel(versionName) {
      const parts = versionName.split(' / ')
      return parts[parts.length - 1]
    },
    groupSummary(group) {
      const parts = []
      if (group.root) {
        parts.push(`整版 ${this.versionSummary(group.root)}`)
      }
      if (group.segments.length) {
        parts.push(`${group.segments.length} 个段落`)
      }
      return parts.join(' · ')
    },
    buildSongMediaUrl(file) {
      const path = `${this.selectedSong.path}/${file}`
      const cleanPath = path.split('/').map(encodeURIComponent).join('/')
      return this.isFilePreview()
        ? `file:///Users/claw/GuitarPlatform_v2/library/songs/${cleanPath}`
        : `/api/songs/${this.selectedSong.id}/asset?path=${encodeURIComponent(file)}`
    },
    isFilePreview() {
      return window.location.protocol === 'file:'
    },
    async addMarker() {
      if (!this.selectedSong || !this.selectedVersion) return
      const label = window.prompt('输入标记名称')
      if (!label) return

      const response = await fetch(`/api/songs/${this.selectedSong.id}/markers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          time: this.audio.currentTime,
          label,
          version: this.selectedVersion,
        }),
      })

      if (!response.ok) return
      const data = await response.json()
      this.selectedSong.markers = [...(this.selectedSong.markers || []), data.marker]
    },
    async openScore(type) {
      const file = this.selectedVersionFiles[type]
      if (!file) return
      this.gpError = ''
      this.scoreNotice = ''

      if (type === 'gp' && this.selectedVersionFiles.pdf) {
        this.scoreType = 'pdf'
        this.scoreUrl = this.buildSongMediaUrl(this.selectedVersionFiles.pdf)
        this.scoreNotice = 'GP 暂时使用同版本 PDF 预览。'
        this.showScoreModal = true
        this.destroyGpApi()
        return
      }

      this.scoreType = type
      this.scoreUrl = this.buildSongMediaUrl(file)
      this.showScoreModal = true

      if (type === 'pdf') {
        this.destroyGpApi()
      } else {
        await this.$nextTick()
        const rendered = await this.renderGP(this.scoreUrl)
        if (!rendered && this.selectedVersionFiles.pdf) {
          this.scoreType = 'pdf'
          this.scoreUrl = this.buildSongMediaUrl(this.selectedVersionFiles.pdf)
          this.scoreNotice = 'GP 暂时无法渲染，已自动切换到同版本 PDF 预览。'
          this.destroyGpApi()
        }
      }
    },
    closeScoreModal() {
      this.showScoreModal = false
      this.scoreUrl = ''
      this.pdfDoc = null
      this.scoreNotice = ''
      this.destroyGpApi()
    },
    async renderGP(url) {
      this.gpLoading = true
      this.gpError = ''
      this.destroyGpApi()

      try {
        if (this.isFilePreview()) {
          throw new Error('静态预览模式无法直接渲染 GP 谱，请点击打开原始 GP 文件；本地服务模式会使用 alphaTab 渲染。')
        }
        const alphaTab = await this.ensureAlphaTab()
        const container = this.$refs.gpContainer
        if (!container) {
          throw new Error('GP 容器未找到')
        }

        container.innerHTML = ''
        this.gpApi = new alphaTab.AlphaTabApi(container, {
          file: url,
        })
        return true
      } catch (error) {
        this.gpError = `GP 谱加载失败：${error.message}`
        return false
      } finally {
        this.gpLoading = false
      }
    },
    async ensureAlphaTab() {
      if (window.alphaTab?.AlphaTabApi) {
        return window.alphaTab
      }

      await new Promise((resolve, reject) => {
        const existing = document.querySelector('script[data-alphatab="true"]')
        if (existing) {
          existing.addEventListener('load', () => resolve(), { once: true })
          existing.addEventListener('error', () => reject(new Error('alphaTab 脚本加载失败')), { once: true })
          return
        }

        const script = document.createElement('script')
        script.src = 'https://cdn.jsdelivr.net/npm/@coderline/alphatab@latest/dist/alphaTab.js'
        script.dataset.alphatab = 'true'
        script.onload = () => resolve()
        script.onerror = () => reject(new Error('alphaTab 脚本加载失败'))
        document.head.appendChild(script)
      })

      if (!window.alphaTab?.AlphaTabApi) {
        throw new Error('alphaTab 未正确初始化')
      }

      return window.alphaTab
    },
    destroyGpApi() {
      if (this.gpApi?.destroy) {
        this.gpApi.destroy()
      }
      this.gpApi = null
      this.gpLoading = false
      this.gpError = ''
    },
  },
}
</script>

<style scoped>
.songs-view {
  min-height: 680px;
}

.songs-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
}

.song-list,
.song-detail {
  background: #16213e;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 20px;
}

.list-header,
.detail-header,
.score-header,
.player-header,
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.list-header {
  margin-bottom: 16px;
}

.list-header h2,
.detail-header h3,
.versions-section h4,
.score-section h4 {
  color: #f3f4f6;
}

.list-header p,
.detail-header p,
.empty-copy,
.song-card p {
  color: #94a3b8;
}

.search-box {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
  color: #cbd5e1;
  font-size: 13px;
}

.search-box input {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: #0f1730;
  color: #f8fafc;
  padding: 10px 12px;
}

.song-card,
.version-item,
.marker-item,
.group-item {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 14px;
  background: #0f1730;
  color: #e5e7eb;
  padding: 14px;
  margin-bottom: 10px;
  cursor: pointer;
}

.song-card.active,
.version-item.active,
.group-item.active {
  border-color: rgba(249, 115, 22, 0.7);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
}

.song-card span,
.version-item small,
.group-item small,
.path-pill {
  color: #f97316;
}

.path-pill {
  display: inline-flex;
  border-radius: 999px;
  padding: 6px 12px;
  background: #0f1730;
  font-size: 12px;
}

.versions-section,
.player-section,
.score-section {
  margin-top: 20px;
}

.versions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.group-item strong,
.version-item span {
  display: block;
}

.segments-section {
  margin-top: 20px;
}

.section-copy {
  color: #94a3b8;
  font-size: 13px;
}

.progress-panel {
  position: relative;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: #0f1730;
  margin-top: 16px;
  cursor: pointer;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #f97316, #fb7185);
}

.time-row {
  display: flex;
  justify-content: space-between;
  color: #94a3b8;
  font-size: 13px;
  margin-top: 8px;
}

.control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.control-row button,
.score-actions button,
.ghost-btn,
.play-btn,
.modal-audio-controls button {
  border: 1px solid rgba(249, 115, 22, 0.4);
  background: transparent;
  color: #f97316;
  border-radius: 999px;
  padding: 8px 14px;
  cursor: pointer;
}

.control-row button.active {
  background: #f97316;
  color: #fff7ed;
}

.score-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 12px 0;
}

.score-actions a {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(249, 115, 22, 0.4);
  color: #f97316;
  border-radius: 999px;
  padding: 8px 14px;
  text-decoration: none;
}

.media-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.media-hints span {
  border-radius: 999px;
  background: rgba(15, 23, 48, 0.9);
  color: #cbd5e1;
  padding: 6px 10px;
  font-size: 12px;
}

.markers-list {
  display: grid;
  gap: 10px;
}

.marker-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  border-radius: 16px;
  background: #0f1730;
  color: #94a3b8;
  text-align: center;
}

.score-modal {
  position: fixed;
  inset: 0;
  background: rgba(4, 8, 19, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 1000;
}

.score-modal-content {
  width: min(1100px, 100%);
  max-height: 92vh;
  overflow: auto;
  background: #111827;
  border-radius: 20px;
  padding: 20px;
}

.score-modal-header,
.modal-transport {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  color: #e5e7eb;
}

.score-modal-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ghost-link,
.inline-score-link {
  border: 1px solid rgba(249, 115, 22, 0.4);
  color: #f97316;
  border-radius: 999px;
  padding: 8px 14px;
  text-decoration: none;
  font-size: 14px;
}

.inline-score-link {
  display: inline-flex;
  margin-left: 10px;
}

.modal-audio-controls {
  display: grid;
  gap: 12px;
  color: #e5e7eb;
}

.modal-seek {
  width: 100%;
  accent-color: #f97316;
}

.score-viewer {
  margin: 20px 0;
  border-radius: 18px;
  background: #0b1224;
  min-height: 320px;
  padding: 20px;
}

.gp-shell {
  min-height: 320px;
}

.gp-container {
  min-height: 320px;
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
}

.pdf-container {
  display: flex;
  justify-content: center;
  min-height: 72vh;
}

.pdf-container iframe {
  width: 100%;
  min-height: 72vh;
  border: 0;
  border-radius: 12px;
  background: #fff;
}

@media (max-width: 960px) {
  .songs-layout {
    grid-template-columns: 1fr;
  }
}
</style>
