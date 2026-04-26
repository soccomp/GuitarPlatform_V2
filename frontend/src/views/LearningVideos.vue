<template>
  <div class="learning-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div>
          <h2>学习视频</h2>
          <p>收藏视频按主题整理，统一回看和练习</p>
        </div>
        <button class="ghost-btn" :disabled="scanning" @click="scanVideos">
          {{ scanning ? '扫描中...' : '扫描目录' }}
        </button>
      </div>

      <label class="search-panel">
        <span>快速定位</span>
        <input
          v-model.trim="searchQuery"
          type="text"
          class="text-input"
          placeholder="搜索标题、作者或分类"
        />
      </label>

      <div class="nav-block">
        <div class="nav-block-header">
          <h3>最近打开</h3>
          <span>{{ recentVideos.length }}</span>
        </div>
        <div v-if="recentVideos.length" class="resume-list">
          <button
            v-for="item in recentVideos"
            :key="item.key"
            :class="['resume-card', { active: selectedKey === item.key }]"
            @click="selectVideo(item)"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.subtitle }}</p>
          </button>
        </div>
        <div v-else class="empty-side-copy">
          打开过的视频会出现在这里，方便你反复回看。
        </div>
      </div>
    </aside>

    <section class="content">
      <div class="video-shelf">
        <div class="section-header">
          <div>
            <h3>{{ currentFilterLabel }}</h3>
            <p>像逛视频首页一样，直接点卡片开始学。</p>
          </div>
          <span>{{ filteredVideos.length }} 条内容</span>
        </div>

        <div v-if="loading" class="state-box">加载视频中...</div>
        <div v-else-if="error" class="state-box error">{{ error }}</div>
        <div v-else-if="filteredVideos.length === 0" class="state-box">
          当前条件下还没有收藏视频
        </div>
        <div v-else class="video-grid">
          <button
            v-for="item in filteredVideos"
            :key="item.key"
            :class="['video-card', { active: selectedKey === item.key }]"
            @click="selectVideo(item)"
          >
            <div
              :class="['video-thumb', { 'has-thumbnail': item.thumbnailUrl }]"
              :style="{ '--cover-hue': coverHue(item) }"
            >
              <img v-if="item.thumbnailUrl" :src="item.thumbnailUrl" :alt="`${item.title} 封面`" />
              <span class="play-badge">▶</span>
              <span v-if="displayCategory(item)" class="thumb-tag">{{ displayCategory(item) }}</span>
              <strong v-if="!item.thumbnailUrl">{{ coverTitle(item.title) }}</strong>
            </div>
            <div class="video-card-body">
              <strong>{{ item.title }}</strong>
              <p>{{ item.author || item.subtitle || '点击播放学习视频' }}</p>
            </div>
          </button>
        </div>
      </div>

      <teleport to="body">
        <div
          v-if="selectedVideo"
          class="video-modal"
          role="dialog"
          aria-modal="true"
          @click.self="closeVideo"
        >
          <div class="video-modal-card">
            <div class="player-header">
              <div>
                <span class="panel-tag">{{ displayCategory(selectedVideo) || '学习视频' }}</span>
                <h3>{{ selectedVideo.title }}</h3>
                <p v-if="selectedVideo.subtitle">{{ selectedVideo.subtitle }}</p>
              </div>
              <button class="close-btn" @click="closeVideo">关闭</button>
            </div>

            <div class="video-frame">
              <video
                v-if="selectedVideo.path"
                :key="selectedVideo.id"
                :src="selectedVideo.url"
                controls
                controlsList="nodownload"
                autoplay
              ></video>
              <div v-else class="state-box">当前视频未配置媒体路径</div>
            </div>

            <div class="detail-strip">
              <div>
                <span>分类</span>
                <strong>{{ displayCategory(selectedVideo) || '未填写' }}</strong>
              </div>
              <div>
                <span>作者</span>
                <strong>{{ selectedVideo.author || '未整理' }}</strong>
              </div>
              <div>
                <span>备注</span>
                <strong>{{ selectedVideo.description || '暂无整理备注' }}</strong>
              </div>
            </div>
          </div>
        </div>
      </teleport>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import seedIndex from '../../../backend/data/index.json'

const STORAGE_KEY = 'guitar-platform-collected-videos'

const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const selectedKey = ref('')
const videos = ref([])
const scanning = ref(false)
const recentKeys = ref(loadRecentKeys())

const allVideos = computed(() =>
  videos.value.map(video => ({
    key: `video:${video.id}`,
    id: video.id,
    title: video.title,
    subtitle: video.author || '',
    source: video.source,
    author: video.author || '',
    category: video.category || '',
    tags: video.tags || [],
    path: video.path || '',
    description: video.description || '',
    thumbnail: video.thumbnail || '',
    thumbnailUrl: video.thumbnail ? mediaUrl('collected', video.thumbnail) : '',
    url: video.path ? videoStreamUrl(video) : '',
  }))
)

const filteredVideos = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return allVideos.value

  return allVideos.value.filter(item =>
    [item.title, item.subtitle, item.author, item.category, ...(item.tags || [])]
      .some(value => (value || '').toLowerCase().includes(keyword))
  )
})

const selectedVideo = computed(() =>
  allVideos.value.find(item => item.key === selectedKey.value) || null
)

const recentVideos = computed(() =>
  recentKeys.value
    .map(key => allVideos.value.find(item => item.key === key))
    .filter(Boolean)
)

const currentFilterLabel = computed(() => {
  return searchQuery.value.trim() ? `搜索：${searchQuery.value.trim()}` : '全部视频'
})

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetch('/api/videos')
    if (!response.ok) throw new Error('收藏视频列表加载失败')
    videos.value = await response.json()
  } catch (err) {
    videos.value = seedIndex.videos || []
    error.value = ''
  } finally {
    loading.value = false
  }
}

async function scanVideos() {
  scanning.value = true
  error.value = ''
  try {
    const response = await fetch('/api/videos/scan?persist=true')
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '扫描失败')

    videos.value = data.videos || []
    if (allVideos.value.length > 0) {
      selectedKey.value = ''
    }
  } catch (err) {
    error.value = err.message
  } finally {
    scanning.value = false
  }
}

function selectVideo(item) {
  selectedKey.value = item.key
  recentKeys.value = [item.key, ...recentKeys.value.filter(key => key !== item.key)].slice(0, 8)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(recentKeys.value))
  }
}

function closeVideo() {
  selectedKey.value = ''
}

function displayCategory(item) {
  const category = String(item?.category || '').trim()
  return category && category !== '未分类' ? category : ''
}

function loadRecentKeys() {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function sourceLabel(source) {
  const labels = {
    local: '本地收藏',
    xiaohongshu: '小红书',
    bilibili: '哔哩哔哩',
    youtube: 'YouTube',
  }
  return labels[source] || source || '未分类来源'
}

function coverTitle(title) {
  return String(title || '视频').replace(/\s+/g, '').slice(0, 6)
}

function coverHue(item) {
  const seed = String(item.title || item.id || '').split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)
  return `${seed % 360}deg`
}

function videoStreamUrl(video) {
  return isFilePreview()
    ? mediaUrl('collected', video.path)
    : `/api/videos/${video.id}/stream`
}

function mediaUrl(section, path) {
  const cleanPath = String(path || '').split('/').map(encodeURIComponent).join('/')
  return `../../library/${section}/${cleanPath}`
}

function isFilePreview() {
  return typeof window !== 'undefined' && window.location.protocol === 'file:'
}

loadData()
</script>

<style scoped>
.learning-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  min-height: 680px;
}

.sidebar,
.video-shelf {
  background: #16213e;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar {
  padding: 20px;
}

.sidebar-header h2,
.nav-block-header h3,
.section-header h3,
.player-header h3,
.video-modal-card h3 {
  color: #f4f5f7;
}

.sidebar-header p,
.nav-block-header span,
.section-header span,
.section-header p,
.player-header p,
.video-card p,
.empty-side-copy {
  color: #95a2bf;
}

.search-panel,
.resume-list {
  display: grid;
  gap: 10px;
}

.search-panel,
.nav-block {
  margin-top: 20px;
}

.search-panel {
  color: #dbe3f4;
  font-size: 13px;
}

.sidebar-header,
.nav-block-header,
.section-header,
.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.sidebar-header {
  align-items: flex-start;
}

.text-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  background: #101a34;
  color: #e5e7eb;
}

.ghost-btn {
  border: 1px solid rgba(249, 115, 22, 0.5);
  border-radius: 999px;
  background: transparent;
  color: #f97316;
  padding: 7px 12px;
  cursor: pointer;
  white-space: nowrap;
}

.ghost-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.resume-card,
.video-card {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 12px 14px;
  background: #0f1730;
  color: #d9dfeb;
  cursor: pointer;
}

.resume-card.active,
.video-card.active {
  border-color: rgba(249, 115, 22, 0.7);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
}

.content {
  display: grid;
  gap: 20px;
}

.video-shelf {
  padding: 20px;
}

.panel-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #fff7ed;
  background: #f97316;
}

.close-btn {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
  padding: 8px 14px;
  cursor: pointer;
}

.video-frame {
  margin: 18px 0 20px;
  border-radius: 16px;
  overflow: hidden;
  background: #0a1022;
}

.video-frame video {
  width: 100%;
  max-height: 68vh;
  display: block;
  background: #000;
  object-fit: contain;
}

.detail-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.detail-strip div {
  background: #0f1730;
  border-radius: 14px;
  padding: 12px 14px;
  min-width: 0;
}

.detail-strip span {
  display: block;
  color: #95a2bf;
  font-size: 12px;
  margin-bottom: 4px;
}

.detail-strip strong {
  display: block;
  overflow: hidden;
  color: #dbe3f4;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 18px;
}

.video-card {
  overflow: hidden;
  padding: 0;
  border-radius: 16px;
  background: #0f1730;
  transition: border-color 0.2s ease, transform 0.2s ease, background 0.2s ease;
}

.video-card:hover {
  transform: translateY(-3px);
  border-color: rgba(249, 115, 22, 0.5);
}

.video-thumb {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 128px;
  overflow: hidden;
  background:
    radial-gradient(circle at 22% 20%, rgba(255, 255, 255, 0.34), transparent 18%),
    linear-gradient(135deg, hsl(var(--cover-hue) 70% 42%), hsl(calc(var(--cover-hue) + 42deg) 76% 26%));
}

.video-thumb.has-thumbnail {
  background: #020617;
}

.video-thumb::after {
  position: absolute;
  inset: auto 0 0;
  height: 56%;
  content: '';
  background: linear-gradient(180deg, transparent, rgba(5, 10, 24, 0.72));
}

.video-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-thumb strong {
  position: relative;
  z-index: 1;
  max-width: 78%;
  color: rgba(255, 255, 255, 0.9);
  font-size: 24px;
  letter-spacing: 0.08em;
}

.play-badge,
.thumb-tag {
  position: absolute;
  z-index: 2;
  border-radius: 999px;
  color: #fff7ed;
  background: rgba(15, 23, 48, 0.72);
  backdrop-filter: blur(12px);
}

.play-badge {
  left: 12px;
  bottom: 12px;
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  font-size: 13px;
}

.thumb-tag {
  right: 10px;
  bottom: 12px;
  max-width: 62%;
  overflow: hidden;
  padding: 6px 10px;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-card-body {
  display: grid;
  gap: 8px;
  padding: 12px 13px 14px;
}

.video-card-body strong {
  display: -webkit-box;
  min-height: 42px;
  overflow: hidden;
  color: #f4f5f7;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.video-card-body p {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.video-modal {
  position: fixed;
  z-index: 1000;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 28px;
  background: rgba(2, 6, 23, 0.76);
  backdrop-filter: blur(14px);
}

.video-modal-card {
  width: min(1080px, calc(100vw - 56px));
  max-height: calc(100vh - 56px);
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 22px;
  padding: 22px;
  background:
    radial-gradient(circle at top left, rgba(249, 115, 22, 0.18), transparent 34%),
    #16213e;
  box-shadow: 0 26px 90px rgba(0, 0, 0, 0.42);
}

.video-modal .video-frame {
  display: grid;
  place-items: center;
}

.video-modal .video-frame video {
  width: auto;
  max-width: 100%;
  max-height: min(68vh, 760px);
}

@media (max-width: 960px) {
  .learning-layout,
  .detail-strip {
    grid-template-columns: 1fr;
  }

  .video-modal {
    padding: 12px;
  }

  .video-modal-card {
    width: calc(100vw - 24px);
    max-height: calc(100vh - 24px);
    padding: 14px;
  }

  .video-modal .video-frame video {
    max-height: 62vh;
  }
}
</style>
