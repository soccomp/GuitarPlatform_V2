<template>
  <div class="songs-view">
    <div class="songs-layout">
      <!-- 左侧：歌曲列表 -->
      <div class="song-list">
        <h2>🎵 歌曲练习</h2>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="songs.length === 0" class="empty">
          暂无歌曲，请先上传文件到 library/songs/
        </div>
        <div
          v-else
          v-for="song in songs"
          :key="song.id"
          class="song-card"
          :class="{ active: selectedSong && selectedSong.id === song.id }"
          @click="selectSong(song)"
        >
          <div class="song-title">{{ song.title }}</div>
          <div class="song-artist">{{ song.artist }}</div>
          <div class="song-versions">{{ song.versions.length }} 个版本</div>
        </div>
      </div>

      <!-- 右侧：歌曲详情 -->
      <div class="song-detail" v-if="selectedSong">
        <div class="detail-header">
          <h3>{{ selectedSong.title }}</h3>
          <p class="artist">{{ selectedSong.artist }}</p>
        </div>

        <!-- 版本列表 -->
        <div class="versions-section">
          <h4>选择版本</h4>
          <div
            v-for="(version, idx) in selectedSong.versions"
            :key="idx"
            class="version-item"
            :class="{ active: selectedVersion === version.name }"
            @click="selectVersion(version)"
          >
            <span>{{ version.name }}</span>
            <div class="version-files">
              <span v-if="version.files.audio" class="file-tag audio">🔊 音频</span>
              <span v-if="version.files.gp" class="file-tag gp">🎸 GP</span>
              <span v-if="version.files.pdf" class="file-tag pdf">📄 PDF</span>
            </div>
          </div>
        </div>

        <!-- 播放控制 -->
        <div class="player-section" v-if="selectedVersion && currentAudioFile">
          <div class="player-header">
            <span>🎧 {{ selectedVersion }}</span>
            <button class="play-btn" @click="togglePlay">
              {{ isPlaying ? '⏸' : '▶' }}
            </button>
          </div>

          <!-- 进度条 -->
          <div class="progress-bar" @click="seekAudio">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            <div class="progress-time">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</div>
          </div>

          <!-- A-B 循环 -->
          <div class="ab-controls">
            <button @click="setLoopStart" :class="{ active: loopStart !== null }">A[{{ loopStart ? formatTime(loopStart) : '--' }}]</button>
            <button @click="setLoopEnd" :class="{ active: loopEnd !== null }">B[{{ loopEnd ? formatTime(loopEnd) : '--' }}]</button>
            <button @click="clearLoop" class="clear-btn">清除循环</button>
          </div>

          <!-- 速度控制 -->
          <div class="speed-controls">
            <span>速度:</span>
            <button
              v-for="s in speeds"
              :key="s"
              :class="{ active: playbackRate === s }"
              @click="setSpeed(s)"
            >{{ s }}x</button>
          </div>

          <!-- 打点标记 -->
          <div class="markers-section">
            <div class="markers-header">
              <span>📍 打点标记</span>
              <button class="add-marker-btn" @click="addMarker">+ 添加</button>
            </div>
            <div class="markers-list" v-if="markers.length">
              <div
                v-for="(m, idx) in markers"
                :key="idx"
                class="marker-item"
                @click="seekToTime(m.time)"
              >
                <span class="marker-time">{{ formatTime(m.time) }}</span>
                <span class="marker-label">{{ m.label }}</span>
                <span class="marker-version">{{ m.version }}</span>
              </div>
            </div>
            <div v-else class="no-markers">暂无标记</div>
          </div>

          <!-- 曲谱文件 -->
          <div class="score-files" v-if="hasScoreFiles">
            <h4>曲谱文件</h4>
            <div class="score-btns">
              <button v-if="selectedVersionFiles.gp" @click="openScore('gp')">🎸 打开 GP 谱</button>
              <button v-if="selectedVersionFiles.pdf" @click="openScore('pdf')">📄 打开 PDF</button>
            </div>
          </div>
        </div>
      </div>

      <div class="song-detail empty-detail" v-else>
        <p>← 选择左侧歌曲查看详情</p>
      </div>
    </div>

    <!-- 曲谱全屏弹窗 -->
    <div class="score-modal" v-if="showScoreModal" @click.self="closeScoreModal">
      <div class="score-modal-content">
        <div class="score-modal-header">
          <span>{{ selectedVersion }} - {{ scoreType === 'gp' ? 'GP谱' : 'PDF' }}</span>
          <button class="close-btn" @click="closeScoreModal">✕</button>
        </div>
        <div class="score-viewer" ref="scoreViewerRef">
          <!-- GP渲染区 -->
          <div v-if="scoreType === 'gp'" class="gp-container" ref="gpContainer"></div>
          <!-- PDF渲染区 -->
          <div v-if="scoreType === 'pdf'" class="pdf-container">
            <canvas ref="pdfCanvas"></canvas>
          </div>
        </div>
        <!-- 全屏时的伴奏控制条 -->
        <div class="modal-audio-controls">
          <button @click="togglePlay">{{ isPlaying ? '⏸' : '▶' }}</button>
          <span>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
          <button @click="setLoopStart">A</button>
          <button @click="setLoopEnd">B</button>
          <button
            v-for="s in speeds"
            :key="s"
            :class="{ active: playbackRate === s }"
            @click="setSpeed(s)"
          >{{ s }}x</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SongsView',
  data() {
    return {
      songs: [],
      selectedSong: null,
      selectedVersion: null,
      selectedVersionFiles: {},
      loading: false,
      // 音频
      audio: null,
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      playbackRate: 1.0,
      speeds: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
      loopStart: null,
      loopEnd: null,
      // 曲谱
      showScoreModal: false,
      scoreType: null,
      scoreFilePath: null,
      markers: [],
      // pdf.js
      pdfDoc: null,
      pdfPage: null,
      pdfScale: 1.5,
    };
  },
  computed: {
    currentAudioFile() {
      if (!this.selectedSong || !this.selectedVersion) return null;
      const v = this.selectedSong.versions.find(v => v.name === this.selectedVersion);
      return v ? v.files.audio : null;
    },
    hasScoreFiles() {
      return this.selectedVersionFiles && (this.selectedVersionFiles.gp || this.selectedVersionFiles.pdf);
    },
    progressPercent() {
      return this.duration ? (this.currentTime / this.duration) * 100 : 0;
    }
  },
  async mounted() {
    this.initAudio();
    await this.loadSongs();
  },
  methods: {
    initAudio() {
      this.audio = new Audio();
      this.audio.addEventListener('timeupdate', () => {
        this.currentTime = this.audio.currentTime;
        // A-B 循环
        if (this.loopEnd !== null && this.audio.currentTime >= this.loopEnd) {
          this.audio.currentTime = this.loopStart || 0;
        }
      });
      this.audio.addEventListener('loadedmetadata', () => {
        this.duration = this.audio.duration;
      });
      this.audio.addEventListener('ended', () => {
        this.isPlaying = false;
      });
    },
    async loadSongs() {
      this.loading = true;
      try {
        const res = await fetch('/api/songs');
        this.songs = await res.json();
      } catch (e) {
        console.error('加载歌曲列表失败:', e);
      } finally {
        this.loading = false;
      }
    },
    async selectSong(song) {
      this.selectedSong = song;
      this.selectedVersion = null;
      this.selectedVersionFiles = {};
      this.stopAudio();
      // 加载完整详情
      try {
        const res = await fetch(`/api/songs/${song.id}`);
        const full = await res.json();
        this.selectedSong = full;
        this.markers = full.markers || [];
        // 自动选中第一个版本
        if (full.versions && full.versions.length > 0) {
          this.selectVersion(full.versions[0]);
        }
      } catch (e) {
        console.error('加载歌曲详情失败:', e);
      }
    },
    selectVersion(version) {
      this.selectedVersion = version.name;
      this.selectedVersionFiles = version.files || {};
      this.stopAudio();
      if (this.selectedVersionFiles.audio) {
        this.loadAudio();
      }
    },
    loadAudio() {
      if (!this.selectedSong || !this.selectedVersion) return;
      const src = `/api/songs/${this.selectedSong.id}/play?version=${encodeURIComponent(this.selectedVersion)}`;
      this.audio.src = src;
      this.audio.load();
    },
    togglePlay() {
      if (!this.audio.src) return;
      if (this.isPlaying) {
        this.audio.pause();
      } else {
        this.audio.play();
      }
      this.isPlaying = !this.isPlaying;
    },
    stopAudio() {
      if (this.audio) {
        this.audio.pause();
        this.audio.currentTime = 0;
      }
      this.isPlaying = false;
      this.currentTime = 0;
    },
    seekAudio(e) {
      if (!this.duration) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const percent = (e.clientX - rect.left) / rect.width;
      this.audio.currentTime = percent * this.duration;
    },
    setSpeed(s) {
      this.playbackRate = s;
      this.audio.playbackRate = s;
    },
    setLoopStart() {
      this.loopStart = this.audio.currentTime;
    },
    setLoopEnd() {
      this.loopEnd = this.audio.currentTime;
    },
    clearLoop() {
      this.loopStart = null;
      this.loopEnd = null;
    },
    seekToTime(time) {
      if (this.audio) {
        this.audio.currentTime = time;
        if (!this.isPlaying) {
          this.audio.play();
          this.isPlaying = true;
        }
      }
    },
    formatTime(seconds) {
      if (!seconds || isNaN(seconds)) return '0:00';
      const m = Math.floor(seconds / 60);
      const s = Math.floor(seconds % 60);
      return `${m}:${s.toString().padStart(2, '0')}`;
    },
    async addMarker() {
      if (!this.selectedSong || !this.selectedVersion) return;
      const label = prompt('输入标记名称（如：尾奏入口）:');
      if (!label) return;
      try {
        const res = await fetch(`/api/songs/${this.selectedSong.id}/markers`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            time: this.audio.currentTime,
            label,
            version: this.selectedVersion
          })
        });
        const data = await res.json();
        if (data.ok) {
          this.markers.push(data.marker);
        }
      } catch (e) {
        alert('添加标记失败: ' + e.message);
      }
    },
    async openScore(type) {
      if (!this.selectedSong || !this.selectedVersion) return;
      const version = this.selectedSong.versions.find(v => v.name === this.selectedVersion);
      const file = version.files[type];
      if (!file) return;
      this.scoreType = type;
      const basePath = `/library/${this.selectedSong.path}${this.selectedVersion}/${file}`;
      this.scoreFilePath = basePath;
      this.showScoreModal = true;
      if (type === 'pdf') {
        await this.$nextTick();
        this.renderPDF(basePath);
      }
    },
    closeScoreModal() {
      this.showScoreModal = false;
      this.pdfDoc = null;
    },
    async renderPDF(url) {
      // 动态加载 pdf.js
      if (!window.pdfjsLib) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
        script.onload = () => this._renderPDF(url);
        document.head.appendChild(script);
      } else {
        this._renderPDF(url);
      }
    },
    async _renderPDF(url) {
      const pdfjsLib = window.pdfjsLib;
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      const loadingTask = pdfjsLib.getDocument(url);
      this.pdfDoc = await loadingTask.promise;
      const page = await this.pdfDoc.getPage(1);
      const viewport = page.getViewport({ scale: this.pdfScale });
      const canvas = this.$refs.pdfCanvas;
      const context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      await page.render({ canvasContext: context, viewport }).promise;
    }
  }
};
</script>

<style scoped>
.songs-view {
  background: #16213e;
  border-radius: 12px;
  padding: 24px;
  min-height: 500px;
}
.songs-layout {
  display: flex;
  gap: 24px;
  height: 100%;
}
.song-list {
  width: 280px;
  flex-shrink: 0;
}
.song-list h2 {
  color: #e94560;
  margin-bottom: 16px;
}
.song-card {
  background: #1a1a2e;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 10px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}
.song-card:hover {
  border-color: #e94560;
}
.song-card.active {
  border-color: #e94560;
  background: #1f1f3a;
}
.song-title {
  color: #fff;
  font-weight: bold;
  margin-bottom: 4px;
}
.song-artist {
  color: #888;
  font-size: 13px;
}
.song-versions {
  color: #e94560;
  font-size: 12px;
  margin-top: 4px;
}
.song-detail {
  flex: 1;
  background: #1a1a2e;
  border-radius: 12px;
  padding: 24px;
}
.detail-header h3 {
  color: #fff;
  margin: 0 0 4px;
}
.artist {
  color: #888;
  margin: 0 0 20px;
}
.versions-section h4,
.score-files h4 {
  color: #e94560;
  margin-bottom: 12px;
}
.version-item {
  background: #16213e;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.version-item:hover {
  border-color: #e94560;
}
.version-item.active {
  border-color: #e94560;
  background: #1f1f3a;
}
.version-files {
  display: flex;
  gap: 6px;
}
.file-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}
.file-tag.audio { background: #e94560; color: #fff; }
.file-tag.gp { background: #0f3460; color: #fff; }
.file-tag.pdf { background: #333; color: #fff; }
.player-section {
  margin-top: 24px;
}
.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: #fff;
}
.play-btn {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #e94560;
  border: none;
  font-size: 18px;
  cursor: pointer;
}
.progress-bar {
  height: 8px;
  background: #333;
  border-radius: 4px;
  cursor: pointer;
  position: relative;
  margin-bottom: 8px;
}
.progress-fill {
  height: 100%;
  background: #e94560;
  border-radius: 4px;
  transition: width 0.1s;
}
.progress-time {
  color: #888;
  font-size: 12px;
  text-align: right;
  margin-bottom: 12px;
}
.ab-controls, .speed-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.ab-controls button, .speed-controls button {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #444;
  background: #222;
  color: #aaa;
  cursor: pointer;
  font-size: 13px;
}
.ab-controls button.active {
  border-color: #e94560;
  color: #e94560;
}
.ab-controls .clear-btn {
  color: #888;
}
.speed-controls button.active {
  background: #e94560;
  border-color: #e94560;
  color: #fff;
}
.markers-section {
  margin-top: 16px;
}
.markers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #e94560;
}
.add-marker-btn {
  padding: 4px 10px;
  background: #e94560;
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}
.marker-item {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #2a2a4a;
  cursor: pointer;
  font-size: 13px;
}
.marker-item:hover {
  color: #e94560;
}
.marker-time { color: #e94560; width: 50px; }
.marker-label { color: #fff; flex: 1; }
.marker-version { color: #888; font-size: 12px; }
.no-markers { color: #666; font-size: 13px; }
.score-btns {
  display: flex;
  gap: 10px;
}
.score-btns button {
  padding: 10px 20px;
  background: #e94560;
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}
.score-btns button:hover {
  opacity: 0.9;
}
.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}
/* 全屏曲谱弹窗 */
.score-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.9);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}
.score-modal-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.score-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #1a1a2e;
  color: #fff;
}
.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
}
.score-viewer {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
}
.gp-container, .pdf-container {
  max-width: 100%;
}
.pdf-container canvas {
  max-width: 100%;
  height: auto;
}
.modal-audio-controls {
  background: #1a1a2e;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.modal-audio-controls button {
  padding: 8px 14px;
  background: #e94560;
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
}
.modal-audio-controls span {
  color: #fff;
}
.loading, .empty {
  color: #666;
  text-align: center;
  margin-top: 40px;
}
</style>
