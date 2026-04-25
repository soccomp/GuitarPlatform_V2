<template>
  <div class="learning-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>学习视频</h2>
        <p>收藏小红书、B站和 YouTube 视频，统一整理后再学</p>
      </div>

      <form class="import-card" @submit.prevent="importVideo">
        <h3>导入收藏视频</h3>
        <input
          v-model="importForm.url"
          type="url"
          class="text-input"
          placeholder="粘贴小红书 / B站 / YouTube 链接"
        />
        <div class="import-grid">
          <select v-model="importForm.source" class="text-input">
            <option value="">自动识别来源</option>
            <option value="xiaohongshu">小红书</option>
            <option value="bilibili">哔哩哔哩</option>
            <option value="youtube">YouTube</option>
          </select>
          <input
            v-model="importForm.category"
            type="text"
            class="text-input"
            placeholder="分类（如扫弦 / 和弦）"
          />
        </div>
        <button class="import-btn" :disabled="importing || !importForm.url.trim()">
          {{ importing ? '导入中...' : '导入视频' }}
        </button>
        <p v-if="importError" class="import-error">{{ importError }}</p>
      </form>

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
            <div class="resume-meta">
              <span>{{ sourceLabel(item.source) }}</span>
              <span>{{ item.category || '未分类' }}</span>
            </div>
          </button>
        </div>
        <div v-else class="empty-side-copy">
          打开过的视频会出现在这里，方便你反复回看。
        </div>
      </div>

      <div class="nav-block">
        <div class="nav-block-header">
          <h3>视频来源</h3>
          <span>{{ sourceFilters.length }}</span>
        </div>
        <div class="filter-list">
          <button
            v-for="filter in sourceFilters"
            :key="filter.key"
            :class="['filter-btn', { active: activeFilter === filter.key }]"
            @click="selectFilter(filter.key)"
          >
            <span>{{ filter.label }}</span>
            <span class="filter-count">{{ filter.count }}</span>
          </button>
        </div>
      </div>
    </aside>

    <section class="content">
      <div class="content-grid">
        <div class="video-list">
          <div class="section-header">
            <h3>{{ currentFilterLabel }}</h3>
            <span>{{ filteredVideos.length }} 条内容</span>
          </div>

          <div v-if="loading" class="state-box">加载视频中...</div>
          <div v-else-if="error" class="state-box error">{{ error }}</div>
          <div v-else-if="filteredVideos.length === 0" class="state-box">
            当前条件下还没有收藏视频
          </div>
          <button
            v-for="item in filteredVideos"
            v-else
            :key="item.key"
            :class="['video-card', { active: selectedKey === item.key }]"
            @click="selectVideo(item)"
          >
            <div class="video-card-top">
              <span class="pill">{{ sourceLabel(item.source) }}</span>
              <span class="meta">{{ item.category || '未分类' }}</span>
            </div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.subtitle }}</p>
            <div class="video-card-meta">
              <span>{{ item.author || '作者未整理' }}</span>
              <span v-if="item.tags?.length">{{ item.tags.slice(0, 2).join(' / ') }}</span>
            </div>
          </button>
        </div>

        <div class="player-panel">
          <div v-if="!selectedVideo" class="state-box">
            选择左侧视频开始学习
          </div>
          <template v-else>
            <div class="player-header">
              <div>
                <span class="panel-tag">{{ sourceLabel(selectedVideo.source) }}</span>
                <h3>{{ selectedVideo.title }}</h3>
                <p>{{ selectedVideo.subtitle }}</p>
              </div>
            </div>

            <div class="video-frame">
              <video
                v-if="selectedVideo.path"
                :src="selectedVideo.url"
                controls
                controlsList="nodownload"
              ></video>
              <div v-else class="state-box">当前视频未配置媒体路径</div>
            </div>

            <div class="detail-grid single">
              <div class="detail-card">
                <h4>视频信息</h4>
                <ul>
                  <li><span>来源</span><strong>{{ sourceLabel(selectedVideo.source) }}</strong></li>
                  <li><span>作者</span><strong>{{ selectedVideo.author || '未填写' }}</strong></li>
                  <li><span>分类</span><strong>{{ selectedVideo.category || '未填写' }}</strong></li>
                  <li><span>标签</span><strong>{{ selectedVideo.tags?.join(' / ') || '暂无标签' }}</strong></li>
                </ul>
              </div>

              <div class="detail-card">
                <h4>整理备注</h4>
                <pre class="transcript">{{ selectedVideo.description || '当前视频还没有补充整理说明。' }}</pre>
              </div>
            </div>
          </template>
        </div>
      </div>
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
const activeFilter = ref('all')
const selectedKey = ref('')
const videos = ref([])
const importing = ref(false)
const importError = ref('')
const importForm = ref({
  url: '',
  source: '',
  category: '',
})
const recentKeys = ref(loadRecentKeys())

const allVideos = computed(() =>
  videos.value.map(video => ({
    key: `video:${video.id}`,
    id: video.id,
    title: video.title,
    subtitle: video.category || video.author || sourceLabel(video.source),
    source: video.source,
    author: video.author || '',
    category: video.category || '',
    tags: video.tags || [],
    path: video.path || '',
    description: video.description || '',
    url: video.path ? mediaUrl('collected', video.path) : '',
  }))
)

const sourceFilters = computed(() => {
  const counts = new Map()
  for (const video of allVideos.value) {
    counts.set(video.source, (counts.get(video.source) || 0) + 1)
  }
  return [
    { key: 'all', label: '全部视频', count: allVideos.value.length },
    ...Array.from(counts.entries()).map(([source, count]) => ({
      key: `source:${source}`,
      label: sourceLabel(source),
      count,
    })),
  ]
})

const filteredVideos = computed(() => {
  let items = allVideos.value
  if (activeFilter.value.startsWith('source:')) {
    const source = activeFilter.value.slice('source:'.length)
    items = items.filter(item => item.source === source)
  }

  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return items

  return items.filter(item =>
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
  const current = sourceFilters.value.find(item => item.key === activeFilter.value)
  if (current?.label) return current.label
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
    if (selectedKey.value && allVideos.value.find(item => item.key === selectedKey.value)) {
      loading.value = false
      return
    }
    if (recentVideos.value.length > 0) {
      selectedKey.value = recentVideos.value[0].key
      loading.value = false
      return
    }
    if (allVideos.value.length > 0) {
      selectedKey.value = allVideos.value[0].key
    }
    loading.value = false
  }
}

async function importVideo() {
  importing.value = true
  importError.value = ''
  try {
    const response = await fetch('/api/videos/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: importForm.value.url.trim(),
        source: importForm.value.source || null,
        category: importForm.value.category.trim() || null,
      }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '导入失败')

    videos.value = [data, ...videos.value.filter(item => item.id !== data.id)]
    importForm.value = { url: '', source: '', category: '' }
    activeFilter.value = `source:${data.source}`
    selectVideo({
      key: `video:${data.id}`,
      id: data.id,
    })
  } catch (err) {
    importError.value = err.message
  } finally {
    importing.value = false
  }
}

function selectFilter(key) {
  activeFilter.value = key
  if (!filteredVideos.value.find(item => item.key === selectedKey.value) && filteredVideos.value.length > 0) {
    selectVideo(filteredVideos.value[0])
  }
}

function selectVideo(item) {
  selectedKey.value = item.key
  recentKeys.value = [item.key, ...recentKeys.value.filter(key => key !== item.key)].slice(0, 8)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(recentKeys.value))
  }
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
    xiaohongshu: '小红书',
    bilibili: '哔哩哔哩',
    youtube: 'YouTube',
  }
  return labels[source] || source || '未分类来源'
}

function mediaUrl(section, path) {
  const cleanPath = String(path || '').split('/').map(encodeURIComponent).join('/')
  return isFilePreview()
    ? `../../library/${section}/${cleanPath}`
    : `/library/${section}/${cleanPath}`
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
.video-list,
.player-panel {
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
.detail-card h4,
.import-card h3 {
  color: #f4f5f7;
}

.sidebar-header p,
.nav-block-header span,
.section-header span,
.player-header p,
.video-card p,
.empty-side-copy {
  color: #95a2bf;
}

.import-card,
.search-panel,
.resume-list,
.filter-list {
  display: grid;
  gap: 10px;
}

.import-card {
  margin-top: 18px;
  padding: 14px;
  border-radius: 14px;
  background: #0f1730;
}

.import-grid {
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

.nav-block-header,
.section-header,
.player-header,
.video-card-top,
.resume-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.text-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  background: #101a34;
  color: #e5e7eb;
}

.import-btn {
  border: 0;
  border-radius: 12px;
  padding: 11px 14px;
  background: linear-gradient(135deg, #f97316, #fb7185);
  color: #fff7ed;
  font-weight: 700;
  cursor: pointer;
}

.import-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.import-error {
  color: #fda4af;
  font-size: 13px;
}

.resume-card,
.filter-btn,
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
.filter-btn.active,
.video-card.active {
  border-color: rgba(249, 115, 22, 0.7);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
}

.filter-count,
.resume-meta,
.meta,
.video-card-meta {
  color: #f97316;
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}

.video-list,
.player-panel {
  padding: 20px;
}

.video-card {
  margin-bottom: 12px;
}

.video-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin-top: 10px;
}

.pill,
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

.video-frame {
  margin: 18px 0 20px;
  border-radius: 16px;
  overflow: hidden;
  background: #0a1022;
}

.video-frame video {
  width: 100%;
  display: block;
  background: #000;
}

.detail-grid.single {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.detail-card {
  background: #0f1730;
  border-radius: 16px;
  padding: 18px;
}

.detail-card ul {
  display: grid;
  gap: 12px;
  list-style: none;
}

.detail-card li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #cdd6e6;
}

.detail-card li span {
  color: #95a2bf;
}

.transcript {
  color: #dbe3f4;
  white-space: pre-wrap;
  line-height: 1.6;
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

@media (max-width: 960px) {
  .learning-layout,
  .content-grid,
  .detail-grid.single {
    grid-template-columns: 1fr;
  }
}
</style>
