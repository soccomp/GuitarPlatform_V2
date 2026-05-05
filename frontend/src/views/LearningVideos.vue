<template>
  <div class="learning-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div>
          <h2>学习视频</h2>
          <p>收藏视频按主题整理，统一回看和练习。</p>
        </div>
        <div class="sidebar-actions">
          <button class="ghost-btn" :disabled="rebuildingIntelligence" @click="rebuildIntelligence">
            {{ rebuildingIntelligence ? '整理中...' : '刷新内容理解' }}
          </button>
          <button class="ghost-btn" :disabled="scanning" @click="scanVideos">
            {{ scanning ? '扫描中...' : '扫描目录' }}
          </button>
        </div>
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

      <div class="nav-block">
        <div class="nav-block-header">
          <h3>内容整理</h3>
          <span>{{ transcriptCoverageLabel }}</span>
        </div>
        <div class="resume-list">
          <div class="resume-card info-card">
            <strong>总计 {{ allVideos.length }} 条</strong>
            <p>已有 transcript {{ transcriptReadyCount }} 条，待补 {{ transcriptPendingCount }} 条。</p>
          </div>
          <button
            class="resume-card action-card"
            :disabled="batchGeneratingTranscript || transcriptPendingCount === 0"
            @click="generatePendingTranscripts"
          >
            <strong>{{ batchGeneratingTranscript ? '批量生成中...' : '批量补 transcript' }}</strong>
            <p>先为最需要整理的几条学习视频补文字内容。</p>
          </button>
        </div>
        <div v-if="intelligenceSummary?.prioritized_items?.length" class="priority-list">
          <div class="priority-title">优先补这几条</div>
          <button
            v-for="item in intelligenceSummary.prioritized_items"
            :key="`priority-video-${item.id}`"
            class="priority-card"
            @click="openPriorityVideo(item.id)"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.reason }}</p>
          </button>
        </div>
      </div>
    </aside>

    <section class="content">
      <div class="video-shelf">
        <div class="section-header">
          <div>
            <h3>{{ currentFilterLabel }}</h3>
            <p>直接点卡片开始看，少跳转、少打断。</p>
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
              <p>{{ item.author || item.subtitle || displayCategory(item) || '点击播放学习视频' }}</p>
              <div class="video-card-highlights">
                <span v-if="item.learningFocus">{{ item.learningFocus }}</span>
              </div>
              <div class="video-card-meta">
                <span>播放 {{ item.playCount || 0 }} 次</span>
                <span v-if="displayCategory(item)">{{ displayCategory(item) }}</span>
              </div>
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
              <div class="modal-actions">
                <button class="ghost-btn" :disabled="generatingTranscript || deleting || savingMeta" @click="generateTranscript">
                  {{ generatingTranscript ? '生成中...' : (selectedVideo?.transcriptAvailable ? '重新生成 transcript' : '生成 transcript') }}
                </button>
                <button class="ghost-btn" :disabled="deleting || savingMeta" @click="openMetaEditor">
                  {{ savingMeta ? '保存中...' : (isEditingMeta ? '取消编辑' : '编辑信息') }}
                </button>
                <button class="danger-btn" :disabled="deleting" @click="deleteSelectedVideo">
                  {{ deleting ? '删除中...' : '删除视频' }}
                </button>
                <button class="close-btn" @click="closeVideo">关闭</button>
              </div>
            </div>

            <div class="video-modal-layout">
              <div class="video-modal-main">
                <div class="video-frame">
                  <video
                    v-if="selectedVideo.path"
                    ref="videoPlayerRef"
                    :key="selectedVideo.id"
                    :src="selectedVideo.url"
                    controls
                    controlsList="nodownload"
                    autoplay
                    @loadedmetadata="handleVideoReady"
                    @timeupdate="handleVideoProgress"
                    @play="isPlaying = true"
                    @pause="isPlaying = false"
                  ></video>
                  <div v-else class="state-box">当前视频未配置媒体路径</div>
                </div>

                <div v-if="selectedVideo.path" class="practice-controls">
                  <div class="practice-topbar">
                    <button class="ghost-btn" @click="togglePlay">
                      {{ isPlaying ? '暂停' : '播放' }}
                    </button>
                    <span>{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
                  </div>

                  <input
                    class="seek-slider"
                    type="range"
                    min="0"
                    :max="duration || 0"
                    step="0.1"
                    :value="currentTime"
                    :disabled="!duration"
                    @input="seekVideoRange"
                  />

                  <div class="practice-actions">
                    <button :class="{ active: loopStart !== null }" @click="setLoopStart">
                      A {{ loopStart === null ? '--:--' : formatTime(loopStart) }}
                    </button>
                    <button :class="{ active: loopEnd !== null }" @click="setLoopEnd">
                      B {{ loopEnd === null ? '--:--' : formatTime(loopEnd) }}
                    </button>
                    <button @click="clearLoop">清除循环</button>
                  </div>

                  <div class="practice-actions speed-row">
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
                </div>
              </div>

              <aside class="video-modal-side">
                <div class="detail-strip detail-strip-stack">
                  <div>
                    <span>分类</span>
                    <strong>{{ displayCategory(selectedVideo) || '未填写' }}</strong>
                  </div>
                  <div>
                    <span>作者</span>
                    <strong>{{ selectedVideo.author || '未整理' }}</strong>
                  </div>
                  <div>
                    <span>学习重点</span>
                    <strong>{{ selectedVideo.learningFocus || '待整理' }}</strong>
                  </div>
                </div>

                <div class="intelligence-grid intelligence-grid-single">
                  <div class="meta-editor-card intelligence-card">
                    <div class="meta-editor-header">
                      <h4>内容摘要</h4>
                      <span>{{ selectedVideo.summary ? '会参与推荐' : '补 transcript 后会更准' }}</span>
                    </div>
                    <p class="intelligence-copy">{{ selectedVideo.summary || selectedVideo.description || '当前还没有整理出内容摘要。' }}</p>
                  </div>

                  <div class="meta-editor-card intelligence-card">
                    <div class="meta-editor-header">
                      <h4>适合怎么用</h4>
                      <span>{{ selectedVideo.recommendedFor ? '会参与学习教练推荐' : '当前先按标题和标签理解' }}</span>
                    </div>
                    <p class="intelligence-copy">{{ selectedVideo.recommendedFor || '适合先作为参考视频收藏，后面补 transcript 后会更适合做智能推荐。' }}</p>
                  </div>

                  <div class="meta-editor-card intelligence-card">
                    <div class="meta-editor-header">
                      <h4>关键点</h4>
                      <span>先抓 1 到 2 个最值得回看的点</span>
                    </div>
                    <ul v-if="selectedVideo.keyPoints?.length" class="intelligence-points">
                      <li v-for="(point, index) in selectedVideo.keyPoints" :key="`${selectedVideo.id}-point-${index}`">
                        {{ point }}
                      </li>
                    </ul>
                    <p v-else class="intelligence-copy">当前还没有提炼出关键点。</p>
                  </div>

                  <div class="meta-editor-card intelligence-card">
                    <div class="meta-editor-header">
                      <h4>标签</h4>
                      <span>会直接参与搜索和歌曲练习推荐</span>
                    </div>
                    <div v-if="selectedVideo.tags?.length" class="chip-row">
                      <span v-for="tag in selectedVideo.tags" :key="`${selectedVideo.id}-${tag}`" class="chip">
                        {{ tag }}
                      </span>
                    </div>
                    <p v-else class="intelligence-copy">当前还没有标签。</p>
                  </div>

                  <div v-if="selectedVideo.transcriptAvailable || selectedVideo.transcriptPreview" class="meta-editor-card intelligence-card">
                    <div class="meta-editor-header">
                      <h4>文字内容预览</h4>
                      <span>{{ selectedVideo.transcriptAvailable ? '后面可继续做问答、摘要和相关推荐' : '当前只显示少量内容' }}</span>
                    </div>
                    <p class="intelligence-copy transcript-preview">{{ selectedVideo.transcriptPreview || '当前还没有可用的 transcript 预览。' }}</p>
                  </div>

                  <div v-if="selectedVideo" class="meta-editor-card">
                    <div class="meta-editor-header">
                      <h4>视频标题与介绍</h4>
                      <span>{{ isEditingMeta ? '可直接修改显示标题、备注和自定义标签' : '需要时可自定义平台内显示信息' }}</span>
                    </div>

                    <div v-if="isEditingMeta" class="meta-editor-form">
                      <label>
                        <span>显示标题</span>
                        <input v-model.trim="metaDraft.title" class="text-input" type="text" placeholder="例如：早班火车 Solo 教学" />
                      </label>
                      <label>
                        <span>作者 / 备注来源</span>
                        <input v-model.trim="metaDraft.author" class="text-input" type="text" placeholder="例如：B站收藏 / 某某老师" />
                      </label>
                      <label>
                        <span>分类</span>
                        <input v-model.trim="metaDraft.category" class="text-input" type="text" placeholder="例如：歌曲教学 / Solo 参考" />
                      </label>
                      <label>
                        <span>介绍 / 备注</span>
                        <textarea v-model.trim="metaDraft.description" class="text-input meta-textarea" placeholder="写一点你想保留的说明，比如这条视频适合练哪一段、讲了什么重点。"></textarea>
                      </label>
                      <label>
                        <span>自定义标签</span>
                        <input v-model.trim="metaDraft.tags" class="text-input" type="text" placeholder="用逗号分隔，比如：早班火车,Solo,主拍" />
                      </label>
                      <div class="meta-editor-actions">
                        <button class="ghost-btn" :disabled="savingMeta" @click="cancelMetaEditor">取消</button>
                        <button class="play-btn" :disabled="savingMeta || !metaDraft.title" @click="saveMetaEditor">保存</button>
                      </div>
                    </div>

                    <div v-else class="meta-editor-preview">
                      <p><strong>当前标题：</strong>{{ selectedVideo.title }}</p>
                      <p><strong>当前介绍：</strong>{{ selectedVideo.description || '暂无整理备注' }}</p>
                    </div>
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </div>
      </teleport>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import seedIndex from '../../../backend/data/index.json'

const STORAGE_KEY = 'guitar-platform-collected-videos'
const PLAY_COUNT_STORAGE_KEY = 'guitar-platform-video-play-counts'
const PENDING_VIDEO_ID_KEY = 'guitar-platform-pending-video-id'

const loading = ref(true)
const error = ref('')
const searchQuery = ref('')
const selectedKey = ref('')
const videos = ref([])
const scanning = ref(false)
const rebuildingIntelligence = ref(false)
const generatingTranscript = ref(false)
const batchGeneratingTranscript = ref(false)
const deleting = ref(false)
const savingMeta = ref(false)
const intelligenceSummary = ref(null)
const recentKeys = ref(loadRecentKeys())
const playCounts = ref(loadPlayCounts())
const videoPlayerRef = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const playbackRate = ref(1)
const loopStart = ref(null)
const loopEnd = ref(null)
const speeds = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
const isEditingMeta = ref(false)
const metaDraft = ref({
  title: '',
  author: '',
  category: '',
  description: '',
})

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
    summary: video.summary || '',
    learningFocus: video.learning_focus || '',
    recommendedFor: video.recommended_for || '',
    keyPoints: video.key_points || [],
    transcriptPreview: video.transcript_preview || '',
    transcriptAvailable: Boolean(video.transcript_available),
    thumbnail: video.thumbnail || '',
    thumbnailUrl: video.thumbnail ? mediaUrl('collected', video.thumbnail) : '',
    url: video.path ? videoStreamUrl(video) : '',
    playCount: playCounts.value[video.id] || 0,
  }))
)

const filteredVideos = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return allVideos.value

  return allVideos.value.filter(item =>
    [item.title, item.subtitle, item.author, item.category, item.summary, item.learningFocus, item.recommendedFor, ...(item.keyPoints || []), ...(item.tags || [])]
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

const transcriptReadyCount = computed(() =>
  allVideos.value.filter(item => item.transcriptAvailable || item.transcriptPreview).length
)

const transcriptPendingCount = computed(() =>
  Math.max(0, allVideos.value.length - transcriptReadyCount.value)
)

const transcriptCoverageLabel = computed(() =>
  `${transcriptReadyCount.value}/${allVideos.value.length || 0}`
)

watch(() => selectedKey.value, async () => {
  const video = selectedVideo.value
  currentTime.value = 0
  duration.value = 0
  isPlaying.value = false
  loopStart.value = null
  loopEnd.value = null
  if (!video?.path) return
  bumpPlayCount(video.id)
  syncMetaDraft(video)
  await nextTick()
  if (videoPlayerRef.value) {
    videoPlayerRef.value.playbackRate = playbackRate.value
  }
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
    await loadIntelligenceSummary()
    const pendingVideoId = consumePendingVideoId()
    if (pendingVideoId) {
      const pendingVideo = allVideos.value.find(item => item.id === pendingVideoId)
      if (pendingVideo) {
        selectVideo(pendingVideo)
      }
    }
    loading.value = false
  }
}

async function loadIntelligenceSummary() {
  try {
    const response = await fetch('/api/videos/intelligence-summary')
    if (!response.ok) throw new Error('内容整理概览加载失败')
    intelligenceSummary.value = await response.json()
  } catch {
    intelligenceSummary.value = null
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
    await loadIntelligenceSummary()
    if (allVideos.value.length > 0) {
      selectedKey.value = ''
    }
  } catch (err) {
    error.value = err.message
  } finally {
    scanning.value = false
  }
}

async function rebuildIntelligence() {
  rebuildingIntelligence.value = true
  error.value = ''
  try {
    const response = await fetch('/api/videos/rebuild-intelligence', {
      method: 'POST',
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '刷新内容理解失败')
    videos.value = data.videos || []
    await loadIntelligenceSummary()
  } catch (err) {
    error.value = err.message
  } finally {
    rebuildingIntelligence.value = false
  }
}

async function generateTranscript() {
  if (!selectedVideo.value || generatingTranscript.value) return
  generatingTranscript.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/videos/${selectedVideo.value.id}/generate-transcript`, {
      method: 'POST',
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '生成 transcript 失败')
    videos.value = videos.value.map(item => item.id === data.video.id ? data.video : item)
    await loadIntelligenceSummary()
  } catch (err) {
    error.value = err.message
  } finally {
    generatingTranscript.value = false
  }
}

async function generatePendingTranscripts() {
  if (batchGeneratingTranscript.value || transcriptPendingCount.value === 0) return
  batchGeneratingTranscript.value = true
  error.value = ''
  try {
    const response = await fetch('/api/videos/generate-transcripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit: 3 }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '批量生成 transcript 失败')
    videos.value = data.videos || videos.value
    await loadIntelligenceSummary()
    if (data.failures?.length) {
      error.value = `有 ${data.failures.length} 条生成失败，请稍后重试。`
    }
  } catch (err) {
    error.value = err.message
  } finally {
    batchGeneratingTranscript.value = false
  }
}

function openPriorityVideo(videoId) {
  const item = allVideos.value.find(video => video.id === videoId)
  if (!item) return
  selectVideo(item)
}

async function deleteSelectedVideo() {
  if (!selectedVideo.value || deleting.value || isFilePreview()) return
  const confirmed = window.confirm(`确定删除视频“${selectedVideo.value.title}”吗？删除后会同时清理封面。`)
  if (!confirmed) return

  deleting.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/videos/${selectedVideo.value.id}`, {
      method: 'DELETE',
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '删除失败')

    recentKeys.value = recentKeys.value.filter(key => key !== selectedVideo.value.key)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(recentKeys.value))
    }

    videos.value = data.videos || []
    selectedKey.value = ''
  } catch (err) {
    error.value = err.message
  } finally {
    deleting.value = false
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
  currentTime.value = 0
  duration.value = 0
  isPlaying.value = false
  loopStart.value = null
  loopEnd.value = null
  isEditingMeta.value = false
}

function syncMetaDraft(video) {
  metaDraft.value = {
    title: video?.title || '',
    author: video?.author || '',
    category: video?.category || '',
    description: video?.description || '',
    tags: Array.isArray(video?.tags) ? video.tags.join(', ') : '',
  }
}

function openMetaEditor() {
  if (isEditingMeta.value) {
    cancelMetaEditor()
    return
  }
  syncMetaDraft(selectedVideo.value)
  isEditingMeta.value = true
}

function cancelMetaEditor() {
  isEditingMeta.value = false
  syncMetaDraft(selectedVideo.value)
}

async function saveMetaEditor() {
  if (!selectedVideo.value || !metaDraft.value.title || savingMeta.value) return
  savingMeta.value = true
  error.value = ''
  try {
    const response = await fetch(`/api/videos/${selectedVideo.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...metaDraft.value,
        tags: String(metaDraft.value.tags || '')
          .split(/[，,]/)
          .map(item => item.trim())
          .filter(Boolean),
      }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '保存失败')

    videos.value = videos.value.map(item => item.id === data.id ? data : item)
    isEditingMeta.value = false
  } catch (err) {
    error.value = err.message
  } finally {
    savingMeta.value = false
  }
}

function handleVideoReady(event) {
  duration.value = event.target.duration || 0
  event.target.playbackRate = playbackRate.value
}

function handleVideoProgress(event) {
  const player = event.target
  currentTime.value = player.currentTime || 0
  if (
    loopStart.value !== null
    && loopEnd.value !== null
    && loopEnd.value > loopStart.value
    && player.currentTime >= loopEnd.value
  ) {
    player.currentTime = loopStart.value
  }
}

async function togglePlay() {
  const player = videoPlayerRef.value
  if (!player) return
  if (player.paused) {
    await player.play()
  } else {
    player.pause()
  }
}

function seekVideoRange(event) {
  const player = videoPlayerRef.value
  if (!player || !duration.value) return
  player.currentTime = Math.max(0, Math.min(duration.value, Number(event.target.value)))
}

function setLoopStart() {
  const player = videoPlayerRef.value
  if (!player) return
  loopStart.value = clampVideoTime(player.currentTime)
  if (loopEnd.value !== null && loopEnd.value <= loopStart.value) {
    loopEnd.value = null
  }
}

function setLoopEnd() {
  const player = videoPlayerRef.value
  if (!player) return
  const end = clampVideoTime(player.currentTime)
  if (loopStart.value !== null && end <= loopStart.value) {
    loopStart.value = Math.max(0, end - 0.5)
  }
  loopEnd.value = end
}

function clearLoop() {
  loopStart.value = null
  loopEnd.value = null
}

function setSpeed(speed) {
  playbackRate.value = speed
  if (videoPlayerRef.value) {
    videoPlayerRef.value.playbackRate = speed
  }
}

function clampVideoTime(time) {
  const value = Number.isFinite(time) ? time : 0
  if (!duration.value) return Math.max(0, value)
  return Math.max(0, Math.min(duration.value, value))
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
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

function loadPlayCounts() {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.localStorage.getItem(PLAY_COUNT_STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function consumePendingVideoId() {
  if (typeof window === 'undefined') return ''
  try {
    const pending = window.localStorage.getItem(PENDING_VIDEO_ID_KEY) || ''
    if (pending) {
      window.localStorage.removeItem(PENDING_VIDEO_ID_KEY)
    }
    return pending
  } catch {
    return ''
  }
}

function persistPlayCounts() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(PLAY_COUNT_STORAGE_KEY, JSON.stringify(playCounts.value))
}

function bumpPlayCount(videoId) {
  if (!videoId) return
  playCounts.value = {
    ...playCounts.value,
    [videoId]: Number(playCounts.value[videoId] || 0) + 1,
  }
  persistPlayCounts()
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

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.learning-layout {
  display: grid;
  grid-template-columns: 272px 1fr;
  gap: 12px;
  min-height: 680px;
}

.sidebar,
.video-shelf {
  background: #16213e;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar {
  position: sticky;
  top: 12px;
  max-height: calc(100vh - 40px);
  overflow: auto;
  padding: 14px;
}

.sidebar-header h2 {
  font-size: 18px;
  line-height: 1.2;
}

.sidebar-header p {
  font-size: 12px;
  line-height: 1.45;
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

.video-card-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 0;
  min-height: 22px;
}

.video-card-highlights span {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(249, 115, 22, 0.12);
  color: #fdba74;
  font-size: 11px;
}

.search-panel,
.resume-list {
  display: grid;
  gap: 10px;
}

.search-panel,
.nav-block {
  margin-top: 16px;
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

.sidebar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.priority-list {
  display: grid;
  gap: 8px;
  margin-top: 12px;
}

.priority-title {
  color: #fdba74;
  font-size: 12px;
}

.priority-card {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(249, 115, 22, 0.2);
  border-radius: 11px;
  padding: 9px 10px;
  background: rgba(249, 115, 22, 0.06);
  color: #e5e7eb;
  cursor: pointer;
}

.priority-card strong {
  display: block;
  color: #f8fafc;
  margin-bottom: 4px;
}

.priority-card p {
  color: #cbd5e1;
  font-size: 12px;
  line-height: 1.55;
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
  border-radius: 10px;
  padding: 9px 11px;
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
  gap: 14px;
}

.video-shelf {
  padding: 14px;
}

.video-modal-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.82fr);
  gap: 14px;
  align-items: start;
}

.video-modal-main,
.video-modal-side {
  min-width: 0;
}

.video-modal-side {
  display: grid;
  gap: 12px;
}

.section-header h3 {
  font-size: 20px;
}

.section-header p {
  font-size: 12px;
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

.modal-actions {
  display: flex;
  gap: 10px;
}

.danger-btn {
  border: 1px solid rgba(248, 113, 113, 0.58);
  border-radius: 999px;
  background: rgba(127, 29, 29, 0.28);
  color: #fecaca;
  padding: 8px 14px;
  cursor: pointer;
  white-space: nowrap;
}

.danger-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
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
  gap: 10px;
}

.detail-strip-stack {
  grid-template-columns: 1fr;
}

.practice-controls {
  display: grid;
  gap: 10px;
  margin: -2px 0 16px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #0f1730;
}

.practice-topbar,
.practice-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.practice-topbar {
  justify-content: space-between;
  color: #dbe3f4;
  font-size: 14px;
}

.seek-slider {
  width: 100%;
  accent-color: #f97316;
}

.practice-actions button {
  border: 1px solid rgba(249, 115, 22, 0.4);
  background: transparent;
  color: #f97316;
  border-radius: 999px;
  padding: 8px 14px;
  cursor: pointer;
}

.practice-actions button.active {
  background: #f97316;
  color: #fff7ed;
}

.speed-row span {
  color: #95a2bf;
  font-size: 13px;
}

.detail-strip div {
  background: #0f1730;
  border-radius: 12px;
  padding: 10px 12px;
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

.meta-editor-card {
  margin-top: 14px;
  padding: 14px;
  border-radius: 14px;
  background: #0f1730;
  display: grid;
  gap: 10px;
}

.intelligence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.intelligence-grid-single {
  grid-template-columns: 1fr;
  margin-top: 0;
}

.intelligence-card {
  margin-top: 0;
}

.intelligence-copy {
  color: #dbe3f4;
  font-size: 13px;
  line-height: 1.7;
}

.intelligence-points {
  display: grid;
  gap: 8px;
  padding-left: 18px;
  color: #dbe3f4;
  font-size: 13px;
  line-height: 1.6;
}

.transcript-preview {
  color: #cbd5e1;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 9px;
  background: rgba(255, 255, 255, 0.06);
  color: #f8fafc;
  font-size: 12px;
}

.meta-editor-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.meta-editor-header h4 {
  color: #f4f5f7;
}

.meta-editor-header span,
.meta-editor-preview p {
  color: #95a2bf;
  font-size: 12px;
  line-height: 1.5;
}

.meta-editor-form {
  display: grid;
  gap: 12px;
}

.meta-editor-form label {
  display: grid;
  gap: 6px;
  color: #dbe3f4;
  font-size: 13px;
}

.meta-textarea {
  min-height: 96px;
  resize: vertical;
}

.meta-editor-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(172px, 1fr));
  gap: 12px;
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
  min-height: 108px;
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
  gap: 5px;
  padding: 10px 11px 11px;
}

.video-card-body strong {
  display: -webkit-box;
  min-height: 36px;
  overflow: hidden;
  color: #f4f5f7;
  font-size: 13px;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.video-card-body p {
  min-height: 18px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
}

.video-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: #94a3b8;
  font-size: 11px;
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
  width: min(960px, calc(100vw - 48px));
  max-height: calc(100vh - 56px);
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 16px;
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
  max-height: min(62vh, 720px);
}

@media (max-width: 960px) {
  .learning-layout,
  .detail-strip,
  .intelligence-grid,
  .video-modal-layout {
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
