<template>
  <div class="learning-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div>
          <h2>系统教材</h2>
          <p>按章节快速定位，直接开课。</p>
        </div>
      </div>

      <label class="search-panel">
        <span>快速定位</span>
        <input
          v-model.trim="searchQuery"
          type="text"
          class="text-input"
          placeholder="搜索课程、章节或关键词"
        />
      </label>

      <div class="series-switcher">
        <button
          v-for="series in seriesTabs"
          :key="series.name"
          :class="['series-tab', { active: activeSeries === series.name }]"
          @click="selectSeries(series.name)"
        >
          <strong>{{ series.name }}</strong>
          <small>{{ series.chapterCount }} 章 · {{ series.count }} 节</small>
        </button>
      </div>

      <div class="nav-block">
        <div class="nav-block-header">
          <h3>继续学习</h3>
          <span>{{ recentHistory.length }}</span>
        </div>
        <div v-if="recentHistory.length" class="resume-list">
          <button
            v-for="item in recentHistory"
            :key="item.key"
            :class="['resume-card', { active: selectedKey === item.key }]"
            @click="openRecentItem(item)"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.subtitle }}</p>
            <div class="resume-meta">
              <span>{{ item.chapterLabel || item.group }}</span>
              <span>{{ formatTime(item.position || 0) }}</span>
            </div>
          </button>
        </div>
        <div v-else class="empty-side-copy">
          开始看课后，这里会记住上次位置。
        </div>
      </div>

    </aside>

    <section class="content">
      <div class="content-grid">
        <div v-if="activeSeriesStats" class="series-overview">
          <div class="series-overview-copy">
            <span class="panel-tag">系统教程</span>
            <h2>{{ activeSeriesStats.name }}</h2>
            <p>
              共 {{ activeSeriesStats.chapterCount }} 章 · {{ activeSeriesStats.count }} 节课，
              已学习 {{ activeSeriesStats.watchedCount }} 节
            </p>
          </div>
          <div class="series-overview-progress">
            <div class="progress-summary">
              <strong>{{ activeSeriesProgress }}%</strong>
              <span>整体进度</span>
            </div>
            <div class="overview-progress-track">
              <div class="overview-progress-fill" :style="{ width: `${activeSeriesProgress}%` }"></div>
            </div>
            <button
              class="play-btn"
              :disabled="!resumeCourseForSeries"
              @click="goToCourse(resumeCourseForSeries)"
            >
              {{ activeSeriesStats.watchedCount ? '继续学习' : '开始第一课' }}
            </button>
          </div>
        </div>

        <div class="study-workspace">
          <div class="browser-panel">
            <div v-if="searchQuery.trim()" class="search-results-panel">
              <div class="section-header">
                <div>
                  <h3>搜索结果</h3>
                  <p>点卡片直接打开课程，左侧目录保持原来的结构导航。</p>
                </div>
                <div class="search-results-actions">
                  <span>{{ searchResults.length }} 节</span>
                  <button class="ghost-btn" @click="searchQuery = ''">清除搜索</button>
                </div>
              </div>

              <div v-if="searchResults.length" class="course-result-grid">
                <button
                  v-for="course in searchResults"
                  :key="`search-${course.key}`"
                  :class="['course-result-card', { active: selectedKey === course.key }]"
                  @click="selectSearchResult(course)"
                >
                  <div class="course-result-copy">
                    <strong>{{ course.title }}</strong>
                    <p>{{ course.group }} / {{ course.chapterLabel }}</p>
                  </div>
                  <div class="course-result-meta">
                    <span v-if="courseProgress(course)">{{ progressLabel(course) }}</span>
                    <span v-else>未开始</span>
                  </div>
                </button>
              </div>
              <div v-else class="state-box compact-state">
                没有找到匹配的课程，试试换个关键词。
              </div>
            </div>

            <div v-else class="structure-browser">
              <div class="section-header">
                <div>
                  <h3>{{ activeSeries || '教材目录' }}</h3>
                  <p>左侧浏览全章节结构，右侧直接定位到具体课时。</p>
                </div>
                <div class="search-results-actions">
                  <span>{{ courseTree.length }} 章</span>
                </div>
              </div>

              <div v-if="courseTree.length" class="course-map-layout">
                <nav class="chapter-rail" aria-label="章节导航">
                  <button
                    v-for="(chapter, index) in courseTree"
                    :key="chapter.key"
                    :class="['chapter-rail-item', { active: activeFilter === chapter.key }]"
                    @click="selectFilter(chapter.key)"
                  >
                    <span class="chapter-index">{{ String(index + 1).padStart(2, '0') }}</span>
                    <span class="chapter-rail-copy">
                      <strong>{{ chapter.label }}</strong>
                      <small>{{ chapter.watchedCount }}/{{ chapter.count }} 已学</small>
                    </span>
                    <span class="chapter-rail-progress">
                      {{ chapterProgress(chapter) }}%
                    </span>
                  </button>
                </nav>

                <div class="chapter-courses-panel">
                  <div v-if="activeChapter" class="section-header chapter-detail-header">
                    <div>
                      <h3>{{ activeChapter.label }}</h3>
                      <p>点击课时后，右侧会立即预览，不需要滚到页面底部。</p>
                    </div>
                    <div class="search-results-actions">
                      <span>{{ activeChapter.courses.length }} 节</span>
                    </div>
                  </div>

                  <div v-if="activeChapter" class="lesson-list">
                    <button
                      v-for="(course, index) in activeChapter.courses"
                      :key="`chapter-course-${course.key}`"
                      :class="['lesson-row', { active: selectedKey === course.key }]"
                      @click="selectVideo(course)"
                    >
                      <span class="lesson-order">{{ String(index + 1).padStart(2, '0') }}</span>
                      <span class="lesson-main">
                        <strong>{{ course.title }}</strong>
                        <small>
                          {{ course.learningFocus || course.summary || course.subtitle || '系统课时' }}
                        </small>
                      </span>
                      <span class="lesson-tags">
                        <em v-if="hasMaterials(course)">有资料</em>
                        <em v-if="course.transcriptAvailable">有笔记</em>
                      </span>
                      <span class="lesson-status">
                        {{ progressLabel(course) }}
                      </span>
                    </button>
                  </div>
                  <div v-else class="state-box compact-state">
                    选择左侧章节查看课时。
                  </div>
                </div>
              </div>
              <div v-else class="state-box compact-state">
                当前没有可展示的系统教材。
              </div>
            </div>
          </div>

          <div v-if="previewCollapsed && selectedVideo" class="preview-collapsed-card">
            <div>
              <span>已选择</span>
              <strong>{{ selectedVideo.title }}</strong>
            </div>
            <button class="play-btn" @click="previewCollapsed = false">打开预览</button>
          </div>

          <div v-else class="player-panel">
            <div v-if="!selectedVideo" class="state-box">
            先在右侧选择一章，再点开具体课程开始学习
            </div>
            <template v-else>
            <div class="player-header">
              <div>
                <span class="panel-tag">即时预览</span>
                <h3>{{ selectedVideo.title }}</h3>
                <p>{{ selectedVideo.subtitle }}</p>
              </div>
              <div class="player-header-actions">
                <button
                  v-if="resumeInfo"
                  class="ghost-btn"
                  @click="resumePlayback"
                >
                  继续看到 {{ formatTime(resumeInfo.position) }}
                </button>
                <button class="ghost-btn" @click="continuePreviewPlayback">继续播放</button>
                <button class="ghost-btn" @click="previewExpanded = true">放大</button>
                <button class="ghost-btn" @click="previewCollapsed = true">收起</button>
              </div>
            </div>

            <div
              ref="videoFrameRef"
              class="video-frame custom-video-frame"
              @click="handleVideoFrameClick"
            >
              <video
                v-if="selectedVideo.path"
                ref="videoPlayerRef"
                :src="selectedVideo.url"
                :muted="previewMuted"
                autoplay
                playsinline
                @loadedmetadata="handleVideoReady"
                @timeupdate="handleVideoProgress"
                @play="isPlaying = true"
                @pause="isPlaying = false"
              ></video>
              <div
                v-if="selectedVideo.path"
                class="player-controls"
                @click.stop
              >
                <button
                  class="player-icon-btn"
                  type="button"
                  :aria-label="isPlaying ? '暂停' : '播放'"
                  @click="togglePlay"
                >
                  {{ isPlaying ? '❚❚' : '▶' }}
                </button>
                <span class="player-time">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
                <input
                  class="player-seek"
                  type="range"
                  min="0"
                  :max="duration || 0"
                  step="0.1"
                  :value="currentTime"
                  :disabled="!duration"
                  aria-label="视频进度"
                  @input="seekVideoRange"
                  @pointerup="blurActivePlaybackControl"
                />
                <button
                  class="player-icon-btn"
                  type="button"
                  :aria-label="previewMuted ? '取消静音' : '静音'"
                  @click="toggleMute"
                >
                  {{ previewMuted ? '静' : '音' }}
                </button>
                <div class="player-speed-controls" aria-label="播放速度">
                  <button
                    class="player-mini-btn"
                    type="button"
                    aria-label="降低播放速度"
                    @click="adjustSpeed(-PLAYBACK_RATE_STEP)"
                  >
                    -
                  </button>
                  <span>{{ playbackRate.toFixed(2) }}x</span>
                  <button
                    class="player-mini-btn"
                    type="button"
                    aria-label="提高播放速度"
                    @click="adjustSpeed(PLAYBACK_RATE_STEP)"
                  >
                    +
                  </button>
                </div>
                <button
                  class="player-icon-btn"
                  type="button"
                  :aria-label="isFullscreen ? '退出全屏' : '全屏'"
                  @click="toggleFullscreen"
                >
                  {{ isFullscreen ? '⤢' : '⛶' }}
                </button>
              </div>
              <div v-else class="state-box">当前视频未配置媒体路径</div>
            </div>

            <div v-if="selectedVideo.type === 'course'" class="resume-strip">
              <span v-if="resumeInfo">已记录进度：{{ formatTime(resumeInfo.position) }}</span>
              <span v-else>当前课程还没有学习进度记录</span>
              <span v-if="recentHistory[0]?.key === selectedVideo.key">已加入最近学习</span>
            </div>

            <div v-if="selectedVideo.type === 'course' && currentChapterCourses.length" class="course-nav-card">
              <div class="course-nav-top">
                <div>
                  <strong>{{ selectedVideo.chapterLabel }}</strong>
                  <p>第 {{ currentCourseIndex + 1 }} / {{ currentChapterCourses.length }} 节</p>
                </div>
                <span class="course-order">顺序学习</span>
              </div>
              <div class="course-nav-actions">
                <button class="ghost-btn" :disabled="!previousCourse" @click="goToCourse(previousCourse)">
                  上一节
                </button>
                <button class="ghost-btn" :disabled="!nextCourse" @click="goToCourse(nextCourse)">
                  下一节
                </button>
              </div>
            </div>

            <div class="detail-layout">
              <div class="detail-main">
                <div v-if="hasMaterials(selectedVideo)" class="materials-card">
                  <div class="materials-header">
                    <h4>随课资料</h4>
                    <span>直接打开谱面和伴奏</span>
                  </div>

                  <div class="materials-grid">
                    <div v-if="selectedVideo.materials?.pdf?.length" class="material-group">
                      <strong>PDF</strong>
                      <a
                        v-for="path in selectedVideo.materials.pdf"
                        :key="path"
                        class="material-link"
                        :href="courseLibraryUrl(path)"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {{ fileName(path) }}
                      </a>
                    </div>

                    <div v-if="selectedVideo.materials?.gp?.length" class="material-group">
                      <strong>GP</strong>
                      <a
                        v-for="path in selectedVideo.materials.gp"
                        :key="path"
                        class="material-link"
                        :href="courseLibraryUrl(path)"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {{ fileName(path) }}
                      </a>
                    </div>

                    <div v-if="selectedVideo.materials?.audio?.length" class="material-group">
                      <strong>伴奏 / 音频</strong>
                      <a
                        v-for="path in selectedVideo.materials.audio"
                        :key="path"
                        class="material-link"
                        :href="courseLibraryUrl(path)"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {{ fileName(path) }}
                      </a>
                    </div>
                  </div>
                </div>
              </div>

              <aside class="detail-side">
                <div class="detail-card detail-card-compact">
                  <h4>分类信息</h4>
                  <ul>
                    <li><span>分组</span><strong>{{ selectedVideo.group }}</strong></li>
                    <li><span>来源</span><strong>系统课程</strong></li>
                    <li><span>作者</span><strong>{{ selectedVideo.author || '未填写' }}</strong></li>
                    <li><span>标签</span><strong>{{ selectedVideo.tags?.join(' / ') || '暂无标签' }}</strong></li>
                  </ul>
                  <div class="secondary-danger-zone">
                    <button
                      class="danger-btn subtle-danger-btn"
                      :disabled="deletingCourse"
                      @click="deleteSelectedCourse"
                    >
                      {{ deletingCourse ? '删除中...' : '删除课时' }}
                    </button>
                  </div>
                </div>
              </aside>
            </div>
            </template>
          </div>
        </div>
      </div>

      <teleport to="body">
        <div
          v-if="previewExpanded && selectedVideo"
          class="preview-modal"
          role="dialog"
          aria-modal="true"
          @click.self="previewExpanded = false"
        >
          <div class="preview-modal-card">
            <div class="player-header">
              <div>
                <span class="panel-tag">放大播放</span>
                <h3>{{ selectedVideo.title }}</h3>
                <p>{{ selectedVideo.subtitle }}</p>
              </div>
              <div class="player-header-actions">
                <button class="ghost-btn" @click="previewExpanded = false">回到目录</button>
              </div>
            </div>
            <div
              ref="previewVideoFrameRef"
              class="video-frame preview-modal-frame custom-video-frame"
              @click="handleVideoFrameClick"
            >
              <video
                v-if="selectedVideo.path"
                ref="previewVideoPlayerRef"
                :src="selectedVideo.url"
                autoplay
                playsinline
                :muted="previewMuted"
                @loadedmetadata="handleVideoReady"
                @timeupdate="handleVideoProgress"
                @play="isPlaying = true"
                @pause="isPlaying = false"
              ></video>
              <div
                v-if="selectedVideo.path"
                class="player-controls"
                @click.stop
              >
                <button
                  class="player-icon-btn"
                  type="button"
                  :aria-label="isPlaying ? '暂停' : '播放'"
                  @click="togglePlay"
                >
                  {{ isPlaying ? '❚❚' : '▶' }}
                </button>
                <span class="player-time">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
                <input
                  class="player-seek"
                  type="range"
                  min="0"
                  :max="duration || 0"
                  step="0.1"
                  :value="currentTime"
                  :disabled="!duration"
                  aria-label="视频进度"
                  @input="seekVideoRange"
                  @pointerup="blurActivePlaybackControl"
                />
                <button
                  class="player-icon-btn"
                  type="button"
                  :aria-label="previewMuted ? '取消静音' : '静音'"
                  @click="toggleMute"
                >
                  {{ previewMuted ? '静' : '音' }}
                </button>
                <div class="player-speed-controls" aria-label="播放速度">
                  <button
                    class="player-mini-btn"
                    type="button"
                    aria-label="降低播放速度"
                    @click="adjustSpeed(-PLAYBACK_RATE_STEP)"
                  >
                    -
                  </button>
                  <span>{{ playbackRate.toFixed(2) }}x</span>
                  <button
                    class="player-mini-btn"
                    type="button"
                    aria-label="提高播放速度"
                    @click="adjustSpeed(PLAYBACK_RATE_STEP)"
                  >
                    +
                  </button>
                </div>
                <button
                  class="player-icon-btn"
                  type="button"
                  :aria-label="isFullscreen ? '退出全屏' : '全屏'"
                  @click="toggleFullscreen"
                >
                  {{ isFullscreen ? '⤢' : '⛶' }}
                </button>
              </div>
              <div v-else class="state-box">当前视频未配置媒体路径</div>
            </div>
          </div>
        </div>
      </teleport>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { loadLocalSeedIndex } from '../utils/localSeedIndex'

const STORAGE_KEY = 'guitar-platform-learning-state'
const MAX_RECENT_ITEMS = 8
const PENDING_COURSE_ID_KEY = 'guitar-platform-pending-course-id'
const COACH_MODEL_STORAGE_KEY = 'guitar-platform-coach-model'

const loading = ref(true)
const error = ref('')
const activeFilter = ref('all')
const activeSeries = ref('')
const searchQuery = ref('')
const selectedKey = ref('')
const transcript = ref('')
const transcriptLoading = ref(false)
const generatingTranscript = ref(false)
const rebuildingIntelligence = ref(false)
const batchGeneratingTranscript = ref(false)
const courses = ref([])
const intelligenceSummary = ref(null)
const showQA = ref(false)
const qaInput = ref('')
const qaLoading = ref(false)
const qaMessagesRef = ref(null)
const qaMessages = ref([
  {
    role: 'assistant',
    content: '我是小霞。打开课程后，你可以直接问我这节课里的重点、难点和练习方法。',
  },
])
const practiceLoading = ref(false)
const practiceLevel = ref('入门')
const practiceResult = ref(null)
const videoFrameRef = ref(null)
const videoPlayerRef = ref(null)
const previewVideoFrameRef = ref(null)
const previewVideoPlayerRef = ref(null)
const isPlaying = ref(false)
const isFullscreen = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const playbackRate = ref(1)
const previewCollapsed = ref(false)
const previewExpanded = ref(false)
const previewMuted = ref(true)
const recentState = ref(loadPersistedState())
const deletingCourse = ref(false)
const relatedSongs = ref([])
const relatedSongsLoading = ref(false)

const MIN_PLAYBACK_RATE = 0.6
const MAX_PLAYBACK_RATE = 1.5
const PLAYBACK_RATE_STEP = 0.05

const allVideos = computed(() => {
  return courses.value.map(course => ({
    key: `course:${course.id}`,
    id: course.id,
    type: 'course',
    title: course.title,
    subtitle: course.description || course.level || '系统课程',
    group: course.series || '未分类课程',
    chapter: course.level || '未分章节',
    chapterLabel: course.level || '未分章节',
    source: 'local-course',
    author: '',
    tags: course.tags || [],
    path: course.video_path || '',
    materials: course.materials || {},
    summary: course.summary || '',
    learningFocus: course.learning_focus || '',
    recommendedFor: course.recommended_for || '',
    keyPoints: course.key_points || [],
    transcriptPreview: course.transcript_preview || '',
    transcriptAvailable: Boolean(course.transcript_available),
    url: course.video_path ? courseVideoUrl(course) : '',
  }))
})

const chapterFilters = computed(() => {
  const chapterGroups = new Map()

  for (const item of allVideos.value) {
    if (item.type !== 'course') continue
    const key = `${item.group}|||${item.chapterLabel}`
    const current = chapterGroups.get(key) || {
      key: `chapter:${item.group}|||${item.chapterLabel}`,
      label: item.chapterLabel,
      series: item.group,
      count: 0,
      watchedCount: 0,
    }
    current.count += 1
    if (isWatched(item)) {
      current.watchedCount += 1
    }
    chapterGroups.set(key, current)
  }

  return Array.from(chapterGroups.values())
    .sort((a, b) => `${a.series}/${a.label}`.localeCompare(`${b.series}/${b.label}`, 'zh-Hans-CN'))
})

const seriesTabs = computed(() => {
  const seriesMap = new Map()

  for (const item of allVideos.value) {
    const current = seriesMap.get(item.group) || {
      name: item.group,
      count: 0,
      watchedCount: 0,
      chapters: new Set(),
    }
    current.count += 1
    current.chapters.add(item.chapterLabel)
    if (isWatched(item)) {
      current.watchedCount += 1
    }
    seriesMap.set(item.group, current)
  }

  return Array.from(seriesMap.values())
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-Hans-CN'))
    .map(series => ({
      ...series,
      chapterCount: series.chapters.size,
    }))
})

const activeSeriesStats = computed(() => {
  return seriesTabs.value.find(series => series.name === activeSeries.value) || seriesTabs.value[0] || null
})

const activeSeriesProgress = computed(() => {
  const stats = activeSeriesStats.value
  if (!stats?.count) return 0
  return Math.round((stats.watchedCount / stats.count) * 100)
})

const courseTree = computed(() => {
  const chapterMap = new Map()

  for (const item of allVideos.value) {
    if (item.type !== 'course') continue
    if (activeSeries.value && item.group !== activeSeries.value) continue

    const chapterKey = `${item.group}|||${item.chapterLabel}`
    const chapter = chapterMap.get(chapterKey) || {
      key: `chapter:${chapterKey}`,
      label: item.chapterLabel,
      count: 0,
      watchedCount: 0,
      courses: [],
    }

    chapter.count += 1
    if (isWatched(item)) {
      chapter.watchedCount += 1
    }
    chapter.courses.push(item)
    chapterMap.set(chapterKey, chapter)
  }

  return Array.from(chapterMap.values())
    .sort((a, b) => a.label.localeCompare(b.label, 'zh-Hans-CN'))
    .map(chapter => ({
      ...chapter,
      courses: chapter.courses.sort((a, b) => compareCourseItems(a, b)),
    }))
})

const searchResults = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) return []

  return allVideos.value.filter(item => {
    const haystacks = [
      item.title,
      item.subtitle,
      item.group,
      item.chapterLabel,
      item.author,
      ...(item.tags || []),
    ]
    return haystacks.some(value => (value || '').toLowerCase().includes(keyword))
  }).sort((a, b) => compareCourseItems(a, b))
})

const activeChapter = computed(() => {
  if (!activeFilter.value || activeFilter.value === 'all') return null
  return courseTree.value.find(chapter => chapter.key === activeFilter.value) || null
})

const resumeCourseForSeries = computed(() => {
  if (!activeSeries.value) return allVideos.value[0] || null

  const recentInSeries = recentHistory.value.find(item => item.group === activeSeries.value)
  if (recentInSeries) return recentInSeries

  const firstUnwatched = allVideos.value
    .filter(item => item.group === activeSeries.value && !isWatched(item))
    .sort((a, b) => compareCourseItems(a, b))[0]
  if (firstUnwatched) return firstUnwatched

  return allVideos.value
    .filter(item => item.group === activeSeries.value)
    .sort((a, b) => compareCourseItems(a, b))[0] || null
})

watch(courseTree, tree => {
  if (!tree.length) return
  if (!activeFilter.value || activeFilter.value === 'all' || !tree.some(chapter => chapter.key === activeFilter.value)) {
    activeFilter.value = tree[0].key
  }
}, { immediate: true })

const transcriptReadyCount = computed(() =>
  allVideos.value.filter(item => item.transcriptAvailable || item.transcriptPreview).length
)

const transcriptPendingCount = computed(() =>
  Math.max(0, allVideos.value.length - transcriptReadyCount.value)
)

const transcriptCoverageLabel = computed(() =>
  `${transcriptReadyCount.value}/${allVideos.value.length || 0}`
)

const selectedVideo = computed(() => {
  return allVideos.value.find(item => item.key === selectedKey.value) || null
})

const recentHistory = computed(() => {
  return (recentState.value.recent || [])
    .map(entry => {
      const item = allVideos.value.find(video => video.key === entry.key)
      if (!item) return null
      return {
        ...item,
        position: entry.position || 0,
      }
    })
    .filter(Boolean)
})

const resumeInfo = computed(() => {
  if (!selectedVideo.value) return null
  return recentState.value.progress?.[selectedVideo.value.key] || null
})

const currentChapterCourses = computed(() => {
  if (!selectedVideo.value || selectedVideo.value.type !== 'course') return []
  return allVideos.value
    .filter(item =>
      item.type === 'course'
      && item.group === selectedVideo.value.group
      && item.chapterLabel === selectedVideo.value.chapterLabel
    )
    .sort((a, b) => compareCourseItems(a, b))
})

const currentCourseIndex = computed(() => {
  if (!selectedVideo.value || selectedVideo.value.type !== 'course') return -1
  return currentChapterCourses.value.findIndex(item => item.key === selectedVideo.value.key)
})

const previousCourse = computed(() => {
  if (currentCourseIndex.value <= 0) return null
  return currentChapterCourses.value[currentCourseIndex.value - 1] || null
})

const nextCourse = computed(() => {
  if (currentCourseIndex.value < 0) return null
  return currentChapterCourses.value[currentCourseIndex.value + 1] || null
})

watch([activeFilter, activeSeries, searchQuery], () => {
  persistState({
    ...recentState.value,
    ui: {
      activeFilter: activeFilter.value,
      activeSeries: activeSeries.value,
      searchQuery: searchQuery.value,
    },
  })
})

watch(selectedVideo, async video => {
  currentTime.value = 0
  duration.value = 0
  isPlaying.value = false
  isFullscreen.value = false
  if (!video?.path) return
  await nextTick()
  const player = videoPlayerRef.value
  const progress = recentState.value.progress?.[video.key]
  if (player && progress?.position) {
    player.currentTime = progress.position
  }
})

watch(previewExpanded, async expanded => {
  await nextTick()
  const sourcePlayer = expanded ? videoPlayerRef.value : previewVideoPlayerRef.value
  const targetPlayer = expanded ? previewVideoPlayerRef.value : videoPlayerRef.value
  if (!sourcePlayer || !targetPlayer) return
  const wasPlaying = isPlaying.value || !sourcePlayer.paused
  targetPlayer.currentTime = sourcePlayer.currentTime || currentTime.value || 0
  targetPlayer.muted = previewMuted.value
  targetPlayer.playbackRate = playbackRate.value
  sourcePlayer.pause()
  if (wasPlaying) {
    targetPlayer.play().catch(() => {})
  }
})

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const courseRes = await fetch('/api/courses')

    if (!courseRes.ok) throw new Error('课程列表加载失败')

    courses.value = await courseRes.json()
  } catch (err) {
    const seedIndex = await loadLocalSeedIndex()
    courses.value = seedIndex.courses || []
    error.value = ''
  } finally {
    hydrateUiState()
    if (!activeSeries.value && seriesTabs.value.length) {
      activeSeries.value = seriesTabs.value[0].name
    }

    const pendingCourseId = consumePendingCourseId()
    if (pendingCourseId) {
      const pendingCourse = allVideos.value.find(item => item.id === pendingCourseId)
      if (pendingCourse) {
        await selectVideo(pendingCourse)
        loading.value = false
        return
      }
    }

    if (selectedKey.value && allVideos.value.find(item => item.key === selectedKey.value)) {
      await selectVideo(allVideos.value.find(item => item.key === selectedKey.value))
    } else if (recentHistory.value.length > 0) {
      await selectVideo(recentHistory.value[0])
    } else if (allVideos.value.length > 0) {
      await selectVideo(allVideos.value[0])
    }
    loading.value = false
  }
}

async function deleteSelectedCourse() {
  if (!selectedVideo.value || selectedVideo.value.type !== 'course' || deletingCourse.value || isFilePreview()) {
    return
  }

  const confirmed = window.confirm(`确定删除课时“${selectedVideo.value.title}”吗？相关笔记和随课资料也会一起删除。`)
  if (!confirmed) return

  deletingCourse.value = true
  error.value = ''
  const deletedKey = selectedVideo.value.key

  try {
    const response = await fetch(`/api/courses/${selectedVideo.value.id}`, {
      method: 'DELETE',
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '删除失败')

    courses.value = data.courses || []
    removeCourseState(deletedKey)
    transcript.value = ''

    if (selectedKey.value === deletedKey) {
      selectedKey.value = ''
      const fallback = recentHistory.value[0] || allVideos.value[0] || null
      if (fallback) {
        await selectVideo(fallback)
      }
    }

    if (activeSeries.value && !seriesTabs.value.find(series => series.name === activeSeries.value)) {
      activeSeries.value = seriesTabs.value[0]?.name || ''
    }
  } catch (err) {
    error.value = err.message
  } finally {
    deletingCourse.value = false
  }
}

function selectSeries(seriesName) {
  activeSeries.value = seriesName
  activeFilter.value = 'all'
  const current = selectedVideo.value
  if (!current || current.group !== seriesName) {
    const firstCourse = allVideos.value
      .filter(item => item.group === seriesName)
      .sort((a, b) => compareCourseItems(a, b))[0]
    if (firstCourse) {
      selectVideo(firstCourse)
    }
  }
}

function selectFilter(key) {
  activeFilter.value = key
  const [series, chapter] = key.slice('chapter:'.length).split('|||')
  if (!selectedVideo.value || selectedVideo.value.group !== series || selectedVideo.value.chapterLabel !== chapter) {
    const firstCourse = allVideos.value
      .filter(item => item.group === series && item.chapterLabel === chapter)
      .sort((a, b) => compareCourseItems(a, b))[0]
    if (firstCourse) {
      selectVideo(firstCourse)
    }
  }
}

function selectSearchResult(item) {
  activeSeries.value = item.group
  activeFilter.value = `chapter:${item.group}|||${item.chapterLabel}`
  selectVideo(item)
}

async function selectVideo(item) {
  activeSeries.value = item.group
  activeFilter.value = `chapter:${item.group}|||${item.chapterLabel}`
  selectedKey.value = item.key
  previewCollapsed.value = false
  previewMuted.value = true
  rememberVideo(item)
  resetAssistantState(item.type)
  await nextTick()
  startPreviewPlayback()
}

function resetAssistantState(type) {
  showQA.value = false
  qaInput.value = ''
  practiceResult.value = null
  practiceLevel.value = '入门'
  qaMessages.value = [
    {
      role: 'assistant',
      content: type === 'course'
        ? '我是小霞。打开课程后，你可以直接问我这节课里的重点、难点和练习方法。'
        : '当前内容是收藏视频，后续会补适用于收藏视频的整理与问答能力。',
    },
  ]
}

async function scrollQaToBottom() {
  await nextTick()
  if (qaMessagesRef.value) {
    qaMessagesRef.value.scrollTop = qaMessagesRef.value.scrollHeight
  }
}

function sourceLabel(source) {
  const labels = {
    'local-course': '系统课程',
    xiaohongshu: '小红书',
    bilibili: '哔哩哔哩',
    youtube: 'YouTube',
  }
  return labels[source] || source || '未分类来源'
}

function openRelatedSong(songId) {
  if (!songId || typeof window === 'undefined') return
  window.localStorage.setItem('guitar-platform-pending-song-id', songId)
  window.dispatchEvent(new CustomEvent('guitar-platform-navigate', { detail: { tab: 'songs' } }))
}

function hasMaterials(video) {
  const materials = video?.materials || {}
  return Object.values(materials).some(list => Array.isArray(list) && list.length > 0)
}

function courseLibraryUrl(path) {
  return mediaUrl('courses', path)
}

function courseVideoUrl(course) {
  if (isFilePreview()) {
    return courseLibraryUrl(course.video_path)
  }
  return `/api/courses/${course.id}/stream`
}

function fileName(path) {
  return path.split('/').pop() || path
}

function rememberVideo(item, position = null) {
  const nextRecent = [
    {
      key: item.key,
      position: position ?? recentState.value.progress?.[item.key]?.position ?? 0,
    },
    ...(recentState.value.recent || []).filter(entry => entry.key !== item.key),
  ].slice(0, MAX_RECENT_ITEMS)

  const nextProgress = {
    ...(recentState.value.progress || {}),
  }

  if (position !== null) {
    nextProgress[item.key] = {
      position,
      updatedAt: new Date().toISOString(),
    }
  } else if (!nextProgress[item.key]) {
    nextProgress[item.key] = {
      position: 0,
      updatedAt: new Date().toISOString(),
    }
  }

  persistState({
    ...recentState.value,
    selectedKey: item.key,
    recent: nextRecent,
    progress: nextProgress,
  })
}

function removeCourseState(key) {
  const nextProgress = { ...(recentState.value.progress || {}) }
  delete nextProgress[key]

  const nextSelectedKey = recentState.value.selectedKey === key ? '' : recentState.value.selectedKey
  persistState({
    ...recentState.value,
    selectedKey: nextSelectedKey,
    recent: (recentState.value.recent || []).filter(entry => entry.key !== key),
    progress: nextProgress,
  })
}

function activeVideoPlayer() {
  return previewExpanded.value && previewVideoPlayerRef.value
    ? previewVideoPlayerRef.value
    : videoPlayerRef.value
}

function activeVideoFrame() {
  return previewExpanded.value && previewVideoFrameRef.value
    ? previewVideoFrameRef.value
    : videoFrameRef.value
}

function syncOtherPlayer(sourcePlayer) {
  const otherPlayer = sourcePlayer === videoPlayerRef.value ? previewVideoPlayerRef.value : videoPlayerRef.value
  if (!otherPlayer || otherPlayer === sourcePlayer) return
  otherPlayer.pause()
  if (Number.isFinite(sourcePlayer.currentTime)) {
    otherPlayer.currentTime = sourcePlayer.currentTime
  }
  otherPlayer.muted = previewMuted.value
  otherPlayer.playbackRate = playbackRate.value
}

function handleVideoProgress(event) {
  currentTime.value = event.target.currentTime || 0
  duration.value = Number.isFinite(event.target.duration) ? event.target.duration : duration.value
  const current = selectedVideo.value
  if (!current?.path) return
  const position = Math.floor(event.target.currentTime || 0)
  const previous = recentState.value.progress?.[current.key]?.position || 0
  if (Math.abs(position - previous) < 5) return
  rememberVideo(current, position)
}

function handleVideoReady(event) {
  const player = event?.target || activeVideoPlayer()
  if (!player) return
  duration.value = Number.isFinite(player.duration) ? player.duration : 0
  const position = resumeInfo.value?.position || 0
  if (player && position > 0 && position < player.duration - 3) {
    player.currentTime = position
  }
  player.muted = previewMuted.value
  player.playbackRate = playbackRate.value
  player.play().catch(() => {})
}

function resumePlayback() {
  const player = activeVideoPlayer()
  const position = resumeInfo.value?.position || 0
  if (!player || !position) return
  player.currentTime = position
  currentTime.value = position
  player.play().catch(() => {})
}

function startPreviewPlayback() {
  const player = videoPlayerRef.value
  if (!player || previewCollapsed.value) return
  player.muted = previewMuted.value
  player.playbackRate = playbackRate.value
  player.play().catch(() => {})
}

function continuePreviewPlayback() {
  previewCollapsed.value = false
  previewMuted.value = false
  const player = activeVideoPlayer()
  if (!player) return
  player.muted = false
  player.playbackRate = playbackRate.value
  player.play().catch(() => {})
}

async function togglePlay() {
  const player = activeVideoPlayer()
  if (!player) return
  if (player.paused) {
    await player.play().catch(() => {})
  } else {
    player.pause()
  }
}

function seekBy(deltaSeconds) {
  const player = activeVideoPlayer()
  if (!player) return
  const duration = Number.isFinite(player.duration) ? player.duration : 0
  const nextTime = Math.max(0, Math.min(duration || Number.MAX_SAFE_INTEGER, (player.currentTime || 0) + deltaSeconds))
  player.currentTime = nextTime
  currentTime.value = nextTime
}

function seekVideoRange(event) {
  const player = activeVideoPlayer()
  if (!player || !duration.value) return
  const nextTime = Math.max(0, Math.min(duration.value, Number(event.target.value)))
  player.currentTime = nextTime
  currentTime.value = nextTime
  syncOtherPlayer(player)
}

function setSpeed(speed) {
  playbackRate.value = clampPlaybackRate(speed)
  ;[videoPlayerRef.value, previewVideoPlayerRef.value].forEach(player => {
    if (player) player.playbackRate = playbackRate.value
  })
  blurActivePlaybackControl()
}

function adjustSpeed(delta) {
  setSpeed(playbackRate.value + delta)
}

function clampPlaybackRate(speed) {
  const value = Number.isFinite(speed) ? speed : 1
  return Number(Math.max(MIN_PLAYBACK_RATE, Math.min(MAX_PLAYBACK_RATE, value)).toFixed(2))
}

function toggleMute() {
  previewMuted.value = !previewMuted.value
  ;[videoPlayerRef.value, previewVideoPlayerRef.value].forEach(player => {
    if (player) player.muted = previewMuted.value
  })
  blurActivePlaybackControl()
}

function isVideoFrameTarget(target) {
  if (!target || target === activeVideoFrame() || target === activeVideoPlayer()) return true
  return target instanceof HTMLElement && target.closest('.player-controls') === null
}

function handleVideoFrameClick(event) {
  if (!selectedVideo.value || !activeVideoPlayer() || !isVideoFrameTarget(event.target)) return
  togglePlay()
}

function getFullscreenElement() {
  if (typeof document === 'undefined') return null
  return document.fullscreenElement || document.webkitFullscreenElement || null
}

async function toggleFullscreen() {
  const frame = activeVideoFrame()
  if (!frame) return

  if (getFullscreenElement()) {
    const exitFullscreen = document.exitFullscreen || document.webkitExitFullscreen
    if (exitFullscreen) await exitFullscreen.call(document)
  } else {
    const requestFullscreen = frame.requestFullscreen || frame.webkitRequestFullscreen
    if (requestFullscreen) await requestFullscreen.call(frame)
  }
  blurActivePlaybackControl()
}

function syncFullscreenState() {
  isFullscreen.value = getFullscreenElement() === activeVideoFrame()
  blurActivePlaybackControl()
}

function openRecentItem(item) {
  activeSeries.value = item.group
  activeFilter.value = `chapter:${item.group}|||${item.chapterLabel}`
  selectVideo(item)
}

function goToCourse(item) {
  if (!item) return
  activeSeries.value = item.group
  activeFilter.value = `chapter:${item.group}|||${item.chapterLabel}`
  selectVideo(item)
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function courseProgress(item) {
  return recentState.value.progress?.[item.key] || null
}

function progressPercent(item) {
  const seconds = courseProgress(item)?.position || 0
  if (!seconds) return 0
  return Math.min(100, Math.max(8, Math.round((seconds / 600) * 100)))
}

function progressLabel(item) {
  const seconds = courseProgress(item)?.position || 0
  if (!seconds) return '未开始'
  return `看到 ${formatTime(seconds)}`
}

function chapterProgress(chapter) {
  if (!chapter?.count) return 0
  return Math.round((chapter.watchedCount / chapter.count) * 100)
}

function isWatched(item) {
  const seconds = courseProgress(item)?.position || 0
  return seconds >= 30
}

function compareCourseItems(a, b) {
  const orderA = extractCourseOrder(a.title)
  const orderB = extractCourseOrder(b.title)
  if (orderA !== orderB) return orderA - orderB
  return a.title.localeCompare(b.title, 'zh-Hans-CN')
}

function extractCourseOrder(title) {
  const match = title.match(/^(\d{1,3})[\s\-_.、]/) || title.match(/^(\d{1,3})/)
  if (match) return Number(match[1])
  const bracketMatch = title.match(/P(\d{1,3})/i)
  if (bracketMatch) return Number(bracketMatch[1]) + 1000
  return Number.MAX_SAFE_INTEGER
}

function hydrateUiState() {
  const savedUi = recentState.value.ui || {}
  if (savedUi.activeFilter) {
    activeFilter.value = savedUi.activeFilter
  }
  if (savedUi.activeSeries) {
    activeSeries.value = savedUi.activeSeries
  }
  if (savedUi.searchQuery) {
    searchQuery.value = savedUi.searchQuery
  }
  if (recentState.value.selectedKey) {
    selectedKey.value = recentState.value.selectedKey
    const selected = allVideos.value.find(item => item.key === recentState.value.selectedKey)
    if (selected) {
      activeSeries.value = selected.group
    }
  }
}

function loadPersistedState() {
  if (typeof window === 'undefined') {
    return { recent: [], progress: {}, ui: {}, selectedKey: '' }
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return { recent: [], progress: {}, ui: {}, selectedKey: '' }
    }
    const parsed = JSON.parse(raw)
    return {
      recent: Array.isArray(parsed.recent) ? parsed.recent : [],
      progress: parsed.progress || {},
      ui: parsed.ui || {},
      selectedKey: parsed.selectedKey || '',
    }
  } catch {
    return { recent: [], progress: {}, ui: {}, selectedKey: '' }
  }
}

function consumePendingCourseId() {
  if (typeof window === 'undefined') return ''
  try {
    const pending = window.localStorage.getItem(PENDING_COURSE_ID_KEY) || ''
    if (pending) {
      window.localStorage.removeItem(PENDING_COURSE_ID_KEY)
    }
    return pending
  } catch {
    return ''
  }
}

function persistState(nextState) {
  recentState.value = nextState
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState))
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

function blurActivePlaybackControl() {
  if (typeof document === 'undefined') return
  const activeElement = document.activeElement
  if (activeElement instanceof HTMLElement) {
    activeElement.blur()
  }
}

function isPlaybackShortcut(event) {
  return event.code === 'Space'
    || event.key === ' '
    || event.key === 'Spacebar'
    || event.key === 'ArrowLeft'
    || event.key === 'ArrowRight'
}

function claimPlaybackShortcut(event) {
  event.preventDefault()
  event.stopPropagation()
  event.stopImmediatePropagation?.()
}

function handleGlobalVideoKeydown(event) {
  if (!selectedVideo.value || !activeVideoPlayer()) return
  if (!isPlaybackShortcut(event)) return

  if (event.code === 'Space' || event.key === ' ' || event.key === 'Spacebar') {
    claimPlaybackShortcut(event)
    blurActivePlaybackControl()
    if (event.repeat) return
    togglePlay()
    return
  }

  if (event.key === 'ArrowLeft') {
    claimPlaybackShortcut(event)
    blurActivePlaybackControl()
    seekBy(-5)
    return
  }

  if (event.key === 'ArrowRight') {
    claimPlaybackShortcut(event)
    blurActivePlaybackControl()
    seekBy(5)
  }
}

function handleGlobalVideoKeyup(event) {
  if (!selectedVideo.value || !activeVideoPlayer() || !isPlaybackShortcut(event)) return
  claimPlaybackShortcut(event)
  blurActivePlaybackControl()
}

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalVideoKeydown, true)
  window.removeEventListener('keyup', handleGlobalVideoKeyup, true)
  document.removeEventListener('fullscreenchange', syncFullscreenState)
  document.removeEventListener('webkitfullscreenchange', syncFullscreenState)
  const player = activeVideoPlayer()
  if (selectedVideo.value && player) {
    rememberVideo(selectedVideo.value, Math.floor(player.currentTime || 0))
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleGlobalVideoKeydown, true)
  window.addEventListener('keyup', handleGlobalVideoKeyup, true)
  document.addEventListener('fullscreenchange', syncFullscreenState)
  document.addEventListener('webkitfullscreenchange', syncFullscreenState)
  loadData()
})
</script>

<style scoped>
.learning-layout {
  display: grid;
  grid-template-columns: 268px 1fr;
  gap: 10px;
  min-height: 680px;
}

.sidebar,
.video-list,
.player-panel {
  background: #16213e;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar {
  position: sticky;
  top: 12px;
  max-height: calc(100vh - 40px);
  overflow: auto;
  padding: 12px;
}

.sidebar-header h2 {
  font-size: 17px;
  line-height: 1.2;
}

.sidebar-header p {
  font-size: 11.5px;
  line-height: 1.45;
}

.sidebar-header h2,
.nav-block-header h3,
.section-header h3,
.player-header h3,
.detail-card h4 {
  color: #f4f5f7;
}

.sidebar-header p,
.nav-block-header span,
.section-header span,
.player-header p,
.video-card p,
.empty-copy {
  color: #95a2bf;
}

.search-panel {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  color: #dbe3f4;
  font-size: 12.5px;
}

.series-switcher {
  position: sticky;
  top: 0;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
  margin-top: 12px;
  padding: 6px 0;
  background: #16213e;
}

.series-tab {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 12px 12px;
  background: #0f1730;
  color: #e5e7eb;
  text-align: left;
  cursor: pointer;
}

.series-tab.active {
  border-color: rgba(249, 115, 22, 0.72);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
}

.series-tab strong,
.series-tab small {
  display: block;
}

.series-tab small {
  margin-top: 5px;
  color: #95a2bf;
  font-size: 11px;
}

.filter-list {
  display: grid;
  gap: 10px;
  margin-top: 20px;
}

.chapter-list {
  max-height: 280px;
  overflow: auto;
  padding-right: 4px;
}

.course-tree {
  display: grid;
  gap: 6px;
  max-height: 420px;
  overflow: auto;
  padding-right: 4px;
}

.series-node,
.chapter-node {
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  background: #0f1730;
  overflow: hidden;
}

.chapter-node {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
}

.series-summary,
.chapter-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  list-style: none;
  cursor: pointer;
  padding: 10px 12px;
}

.series-summary {
  background: rgba(255, 255, 255, 0.02);
}

.series-summary::-webkit-details-marker,
.chapter-summary::-webkit-details-marker {
  display: none;
}

.chapter-children {
  display: grid;
  gap: 8px;
  padding: 0 12px 12px;
}

.course-children {
  display: grid;
  gap: 6px;
  padding: 0 10px 10px;
}

.course-leaf {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 9px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  color: #e5e7eb;
  cursor: pointer;
}

.course-leaf.active {
  border-color: rgba(249, 115, 22, 0.65);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.05));
}

.course-leaf span,
.course-leaf small {
  display: block;
}

.course-leaf small {
  margin-top: 3px;
  color: #95a2bf;
  font-size: 10.5px;
}

.resume-list {
  display: grid;
  gap: 8px;
}

.nav-block {
  margin-top: 14px;
}

.nav-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.import-card {
  display: grid;
  gap: 10px;
  margin-top: 18px;
  padding: 14px;
  border-radius: 14px;
  background: #0f1730;
}

.import-card h3 {
  color: #f4f5f7;
  font-size: 15px;
}

.import-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

.text-input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  background: #101a34;
  color: #e5e7eb;
}

.text-input::placeholder {
  color: #7e8aa7;
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

.filter-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 10px 12px;
  background: #0f1730;
  color: #d9dfeb;
  cursor: pointer;
}

.filter-main {
  display: grid;
  text-align: left;
  gap: 2px;
}

.filter-main small {
  color: #95a2bf;
  font-size: 11px;
}

.filter-btn.active {
  border-color: #f97316;
  background: #1e2747;
}

.filter-count {
  color: #f97316;
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.study-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 0.42fr);
  gap: 14px;
  align-items: start;
}

.browser-panel {
  min-width: 0;
}

.series-overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 0.34fr);
  gap: 16px;
  align-items: center;
  padding: 18px;
  border-radius: 16px;
  background:
    linear-gradient(135deg, rgba(249, 115, 22, 0.16), rgba(14, 165, 233, 0.08)),
    #16213e;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.series-overview-copy {
  min-width: 0;
}

.series-overview-copy h2 {
  margin-top: 10px;
  color: #f8fafc;
  font-size: 24px;
  line-height: 1.25;
}

.series-overview-copy p {
  margin-top: 7px;
  color: #cbd5e1;
  font-size: 13px;
  line-height: 1.6;
}

.series-overview-progress {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.72);
}

.progress-summary {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.progress-summary strong {
  color: #fdba74;
  font-size: 24px;
  line-height: 1;
}

.progress-summary span {
  color: #95a2bf;
  font-size: 12px;
}

.overview-progress-track {
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
}

.overview-progress-fill {
  height: 100%;
  min-width: 4px;
  border-radius: inherit;
  background: linear-gradient(90deg, #f97316, #38bdf8);
}

.play-btn {
  border: 0;
  border-radius: 999px;
  padding: 10px 15px;
  background: linear-gradient(135deg, #f97316, #38bdf8);
  color: #08111f;
  font-weight: 800;
  cursor: pointer;
}

.play-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.structure-browser {
  display: grid;
  gap: 14px;
  padding: 14px;
  border-radius: 16px;
  background: #16213e;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.chapter-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.chapter-card {
  display: grid;
  gap: 8px;
  width: 100%;
  text-align: left;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #0f1730;
  color: #eef1f6;
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.chapter-card:hover {
  border-color: rgba(249, 115, 22, 0.45);
  transform: translateY(-1px);
}

.chapter-card.active {
  border-color: rgba(249, 115, 22, 0.72);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.05));
}

.chapter-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.chapter-card-top strong {
  color: #f8fafc;
  font-size: 14px;
  line-height: 1.35;
}

.chapter-card-top span {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(249, 115, 22, 0.12);
  color: #fdba74;
  font-size: 11px;
  white-space: nowrap;
}

.chapter-card p {
  color: #95a2bf;
  font-size: 12px;
  line-height: 1.5;
}

.chapter-card small {
  color: #cbd5e1;
  font-size: 11px;
}

.chapter-courses-panel {
  display: grid;
  gap: 12px;
}

.course-map-layout {
  display: grid;
  grid-template-columns: minmax(240px, 0.32fr) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}

.chapter-rail {
  position: sticky;
  top: 12px;
  display: grid;
  gap: 7px;
  max-height: calc(100vh - 210px);
  overflow: auto;
  padding-right: 4px;
}

.chapter-rail-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 11px;
  padding: 10px;
  background: #0f1730;
  color: #eef1f6;
  text-align: left;
  cursor: pointer;
}

.chapter-rail-item:hover {
  border-color: rgba(56, 189, 248, 0.45);
}

.chapter-rail-item.active {
  border-color: rgba(249, 115, 22, 0.72);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.16), rgba(56, 189, 248, 0.08));
}

.chapter-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.07);
  color: #fdba74;
  font-size: 12px;
  font-weight: 800;
}

.chapter-rail-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.chapter-rail-copy strong {
  overflow: hidden;
  color: #f8fafc;
  font-size: 12.5px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-rail-copy small,
.chapter-rail-progress {
  color: #95a2bf;
  font-size: 11px;
}

.chapter-rail-progress {
  color: #7dd3fc;
  white-space: nowrap;
}

.chapter-detail-header {
  margin-bottom: 0;
}

.lesson-list {
  display: grid;
  gap: 8px;
}

.lesson-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 62px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  padding: 10px 12px;
  background: #0f1730;
  color: #eef1f6;
  text-align: left;
  cursor: pointer;
}

.lesson-row:hover {
  border-color: rgba(56, 189, 248, 0.45);
}

.lesson-row.active {
  border-color: rgba(249, 115, 22, 0.72);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(255, 255, 255, 0.04));
}

.lesson-order {
  color: #fdba74;
  font-size: 12px;
  font-weight: 800;
}

.lesson-main {
  display: grid;
  gap: 4px;
  min-width: 0;
}

.lesson-main strong {
  overflow: hidden;
  color: #f8fafc;
  font-size: 13px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lesson-main small {
  display: block;
  overflow: hidden;
  color: #95a2bf;
  font-size: 11.5px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lesson-tags {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  flex-wrap: wrap;
}

.lesson-tags em {
  border-radius: 999px;
  padding: 4px 7px;
  background: rgba(56, 189, 248, 0.12);
  color: #7dd3fc;
  font-size: 10.5px;
  font-style: normal;
  white-space: nowrap;
}

.lesson-status {
  min-width: 72px;
  color: #fdba74;
  font-size: 11.5px;
  text-align: right;
  white-space: nowrap;
}

.search-results-panel {
  padding: 14px;
  border-radius: 16px;
  background: #16213e;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.search-results-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #95a2bf;
  font-size: 12px;
}

.course-result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
}

.course-result-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
  gap: 10px;
  width: 100%;
  text-align: left;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #0f1730;
  color: #eef1f6;
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.course-result-card:hover {
  border-color: rgba(249, 115, 22, 0.45);
  transform: translateY(-1px);
}

.course-result-card.active {
  border-color: rgba(249, 115, 22, 0.72);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.05));
}

.course-result-copy {
  min-width: 0;
}

.course-result-copy strong {
  display: block;
  color: #f8fafc;
  font-size: 13.5px;
  line-height: 1.4;
}

.course-result-copy p {
  margin-top: 5px;
  color: #95a2bf;
  font-size: 11.5px;
  line-height: 1.5;
}

.course-result-meta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.course-result-meta span {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 5px 9px;
  background: rgba(249, 115, 22, 0.12);
  color: #fdba74;
  font-size: 11px;
  white-space: nowrap;
}

.compact-state {
  min-height: 88px;
  font-size: 12px;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
  gap: 12px;
  margin-top: 12px;
  align-items: start;
}

.detail-main,
.detail-side {
  min-width: 0;
}

.detail-main {
  display: grid;
  gap: 12px;
}

.detail-side {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 12px;
}

.video-list {
  padding: 18px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 14px;
}

.video-card {
  width: 100%;
  text-align: left;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 14px;
  border: 1px solid transparent;
  background: #0f1730;
  color: #eef1f6;
  cursor: pointer;
}

.video-card.active {
  border-color: rgba(249, 115, 22, 0.7);
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.18), rgba(255, 255, 255, 0.04));
}

.resume-card {
  width: 100%;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 11px;
  padding: 10px 11px;
  background: #0f1730;
  color: #eef1f6;
  cursor: pointer;
}

.resume-card.active {
  border-color: rgba(249, 115, 22, 0.7);
}

.resume-card p,
.empty-side-copy {
  color: #95a2bf;
  font-size: 12px;
}

.resume-meta,
.resume-strip {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  color: #a9b5cf;
  font-size: 12px;
}

.resume-meta {
  margin-top: 8px;
}

.resume-strip {
  margin: -4px 0 14px;
  font-size: 11.5px;
}

.course-nav-card {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #0f1730;
}

.course-nav-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.course-nav-top strong {
  color: #f4f5f7;
}

.course-nav-top p,
.course-order {
  color: #95a2bf;
  font-size: 13px;
}

.course-nav-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.video-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin-top: 10px;
  font-size: 12px;
  color: #a9b5cf;
}

.video-progress {
  margin-top: 10px;
}

.video-progress span {
  display: inline-block;
  color: #fdba74;
  font-size: 12px;
  margin-bottom: 6px;
}

.mini-progress-track {
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #f97316, #fb7185);
}

.video-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
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

.meta {
  font-size: 12px;
  color: #95a2bf;
}

.player-panel {
  position: sticky;
  top: 12px;
  padding: 12px;
  max-height: calc(100vh - 24px);
  overflow: auto;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
}

.video-frame {
  margin: 14px 0 16px;
  border-radius: 14px;
  overflow: hidden;
  background: #0a1022;
}

.custom-video-frame {
  position: relative;
  cursor: pointer;
}

.video-frame video {
  width: 100%;
  display: block;
  background: #000;
}

.video-frame video:focus,
.video-frame video:focus-visible {
  outline: none;
}

.player-controls {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 34px 10px 10px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.78), rgba(0, 0, 0, 0));
  color: #f8fafc;
  cursor: default;
  box-sizing: border-box;
}

.player-icon-btn {
  flex: 0 0 auto;
  display: inline-grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.58);
  color: #fff;
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
  cursor: pointer;
}

.player-icon-btn:hover {
  background: rgba(249, 115, 22, 0.92);
}

.player-icon-btn:focus,
.player-icon-btn:focus-visible,
.player-seek:focus,
.player-seek:focus-visible {
  outline: none;
}

.player-time {
  flex: 0 1 auto;
  min-width: 72px;
  font-weight: 800;
  color: #f8fafc;
  font-size: 12px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.55);
  white-space: nowrap;
}

.player-seek {
  order: 2;
  flex: 1 0 100%;
  width: 100%;
  min-width: 0;
  accent-color: #ff7a1a;
  cursor: pointer;
}

.player-speed-controls {
  flex: 0 0 auto;
  display: inline-grid;
  grid-template-columns: 24px 48px 24px;
  align-items: center;
  gap: 4px;
  min-width: 100px;
  color: #f8fafc;
  font-weight: 800;
  font-size: 12px;
  text-align: center;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.55);
}

.player-mini-btn {
  display: inline-grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.58);
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  line-height: 1;
  cursor: pointer;
}

.player-mini-btn:hover {
  background: rgba(249, 115, 22, 0.92);
}

.player-mini-btn:focus,
.player-mini-btn:focus-visible {
  outline: none;
}

.custom-video-frame:fullscreen {
  width: 100vw;
  height: 100vh;
  margin: 0;
  border-radius: 0;
  display: grid;
  place-items: center;
  background: #000;
}

.custom-video-frame:fullscreen video {
  width: 100vw;
  height: 100vh;
  max-height: none;
}

.custom-video-frame:fullscreen .player-controls {
  padding: 56px 28px 24px;
}

.custom-video-frame:-webkit-full-screen {
  width: 100vw;
  height: 100vh;
  margin: 0;
  border-radius: 0;
  display: grid;
  place-items: center;
  background: #000;
}

.custom-video-frame:-webkit-full-screen video {
  width: 100vw;
  height: 100vh;
  max-height: none;
}

.custom-video-frame:-webkit-full-screen .player-controls {
  padding: 56px 28px 24px;
}

.preview-collapsed-card {
  position: sticky;
  top: 12px;
  display: grid;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: #16213e;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
}

.preview-collapsed-card span,
.preview-collapsed-card strong {
  display: block;
}

.preview-collapsed-card span {
  color: #95a2bf;
  font-size: 12px;
}

.preview-collapsed-card strong {
  margin-top: 4px;
  color: #f8fafc;
  font-size: 14px;
  line-height: 1.45;
}

.preview-modal {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: rgba(2, 6, 23, 0.82);
  backdrop-filter: blur(14px);
}

.preview-modal-card {
  width: min(1180px, 100%);
  max-height: calc(100vh - 56px);
  overflow: auto;
  border-radius: 18px;
  padding: 16px;
  background: #16213e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 24px 90px rgba(0, 0, 0, 0.44);
}

.preview-modal-frame video {
  max-height: calc(100vh - 190px);
  object-fit: contain;
}

.detail-card-wide {
  min-width: 0;
}

.detail-card-compact ul {
  display: grid;
  gap: 0;
}

.intelligence-grid {
  margin-top: 18px;
}

.materials-card {
  margin-top: 12px;
  background: #0f1730;
  border-radius: 12px;
  padding: 12px;
}

.materials-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.materials-header h4 {
  color: #f4f5f7;
}

.materials-header span {
  color: #95a2bf;
  font-size: 13px;
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.material-group {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.material-group strong {
  color: #fdba74;
}

.material-link {
  color: #e5e7eb;
  text-decoration: none;
  padding: 8px 10px;
  border-radius: 10px;
  background: #16213e;
  word-break: break-word;
}

.material-link:hover {
  background: #1f2d52;
}

.assistant-section {
  display: grid;
  gap: 12px;
  margin-top: 0;
}

.assistant-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.assistant-btn {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #fb7185, #f97316);
  color: #fff7ed;
  font-weight: 700;
  cursor: pointer;
}

.assistant-btn.secondary {
  background: rgba(249, 115, 22, 0.16);
  color: #fdba74;
  border: 1px solid rgba(249, 115, 22, 0.45);
}

.assistant-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.assistant-card {
  background: #0f1730;
  border-radius: 12px;
  padding: 12px;
}

.assistant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.assistant-header h4 {
  color: #f4f5f7;
}

.assistant-header span {
  color: #95a2bf;
  font-size: 13px;
}

.qa-messages {
  max-height: 320px;
  overflow-y: auto;
  display: grid;
  gap: 12px;
  margin-bottom: 12px;
}

.qa-message {
  display: flex;
}

.qa-message.user {
  justify-content: flex-end;
}

.qa-message.assistant {
  justify-content: flex-start;
}

.qa-bubble {
  max-width: min(720px, 100%);
  padding: 12px 14px;
  border-radius: 14px;
  color: #e5e7eb;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  background: #16213e;
}

.qa-message.user .qa-bubble {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.92), rgba(251, 113, 133, 0.92));
  color: #fff7ed;
}

.qa-input-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.practice-card {
  display: grid;
  gap: 10px;
}

.practice-level {
  width: 140px;
}

.practice-list {
  display: grid;
  gap: 10px;
  padding-left: 18px;
  color: #e5e7eb;
  line-height: 1.65;
}

.practice-tips {
  padding: 14px;
  border-radius: 14px;
  background: rgba(249, 115, 22, 0.08);
}

.practice-tips h5 {
  color: #fdba74;
  margin-bottom: 8px;
}

.practice-tips pre {
  color: #e5e7eb;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.detail-card {
  background: #0f1730;
  border-radius: 12px;
  padding: 12px;
}

.detail-card p {
  color: #d9dfeb;
  line-height: 1.6;
  font-size: 12.5px;
}

.detail-card ul {
  list-style: none;
}

.detail-card li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: #d9dfeb;
}

.detail-card li:last-child {
  border-bottom: 0;
}

.detail-card span {
  color: #95a2bf;
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
  border-radius: 12px;
  padding: 11px 12px;
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

.linked-song-list {
  display: grid;
  gap: 8px;
}

.linked-song-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 11px;
  background: rgba(8, 14, 28, 0.76);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.linked-song-copy {
  min-width: 0;
}

.linked-song-copy strong {
  display: block;
  color: #f8fafc;
  font-size: 12.5px;
  line-height: 1.35;
}

.linked-song-copy p {
  margin-top: 2px;
  color: #cbd5e1;
  font-size: 11.5px;
}

.linked-song-copy span {
  display: block;
  margin-top: 4px;
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.45;
}

.detail-hints {
  margin-top: 10px;
}

.detail-hints span {
  color: #fdba74;
  font-size: 11px;
  line-height: 1.5;
}

.key-point-list {
  display: grid;
  gap: 8px;
  padding-left: 18px;
  color: #d9dfeb;
  line-height: 1.6;
}

.transcript-preview-card {
  margin-top: 14px;
}

.transcript-card {
  min-height: 220px;
}

.transcript-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.transcript-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.player-header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.ghost-btn {
  border: 1px solid rgba(249, 115, 22, 0.5);
  border-radius: 999px;
  background: transparent;
  color: #f97316;
  padding: 5px 11px;
  cursor: pointer;
}

.danger-btn {
  border: 1px solid rgba(248, 113, 113, 0.58);
  border-radius: 999px;
  background: rgba(127, 29, 29, 0.28);
  color: #fecaca;
  padding: 5px 11px;
  cursor: pointer;
  white-space: nowrap;
}

.danger-btn:disabled,
.ghost-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.secondary-danger-zone {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.subtle-danger-btn {
  opacity: 0.78;
}

.subtle-danger-btn:hover {
  opacity: 1;
}

.transcript {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12.5px;
  line-height: 1.65;
  color: #d9dfeb;
  max-height: 360px;
  overflow: auto;
  padding-right: 4px;
}

.state-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  border-radius: 12px;
  background: #0f1730;
  color: #95a2bf;
  text-align: center;
}

.state-box.error {
  color: #fda4af;
}

@media (max-width: 960px) {
  .learning-layout,
  .content-grid,
  .study-workspace,
  .series-overview,
  .course-map-layout,
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .chapter-rail {
    position: static;
    max-height: none;
  }

  .player-panel,
  .preview-collapsed-card {
    position: static;
    max-height: none;
  }

  .preview-modal {
    padding: 12px;
  }

  .lesson-row {
    grid-template-columns: auto minmax(0, 1fr);
    align-items: start;
  }

  .lesson-tags,
  .lesson-status {
    grid-column: 2;
    justify-content: flex-start;
    text-align: left;
  }

  .lesson-main strong,
  .lesson-main small {
    white-space: normal;
  }

  .detail-side {
    position: static;
  }

  .import-grid {
    grid-template-columns: 1fr;
  }

  .qa-input-row {
    grid-template-columns: 1fr;
  }
}
</style>
