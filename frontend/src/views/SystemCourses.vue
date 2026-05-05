<template>
  <div class="learning-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div>
          <h2>系统教材</h2>
          <p>按章节快速定位，直接开课。</p>
        </div>
        <button class="ghost-btn" :disabled="rebuildingIntelligence" @click="rebuildIntelligence">
          {{ rebuildingIntelligence ? '整理中...' : '刷新内容理解' }}
        </button>
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

      <div class="nav-block">
        <div class="nav-block-header">
          <h3>内容整理</h3>
          <span>{{ transcriptCoverageLabel }}</span>
        </div>
        <div class="resume-list">
          <div class="resume-card info-card">
            <strong>总计 {{ allVideos.length }} 节</strong>
            <p>已整理 {{ transcriptReadyCount }} 节，待补 {{ transcriptPendingCount }} 节。</p>
          </div>
          <button
            class="resume-card action-card"
            :disabled="batchGeneratingTranscript || transcriptPendingCount === 0"
            @click="generatePendingTranscripts"
          >
            <strong>{{ batchGeneratingTranscript ? '批量生成中...' : '批量补 transcript' }}</strong>
            <p>优先补最值得先进入知识库的课程。</p>
          </button>
        </div>
        <div v-if="intelligenceSummary?.prioritized_items?.length" class="priority-list">
          <div class="priority-title">优先补这几节</div>
          <button
            v-for="item in intelligenceSummary.prioritized_items"
            :key="`priority-course-${item.id}`"
            class="priority-card"
            @click="openPriorityCourse(item.id)"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.reason }}</p>
          </button>
        </div>
      </div>

      <div class="nav-block">
        <div class="nav-block-header">
          <h3>{{ activeSeries || '教材目录' }}</h3>
          <span>{{ courseTree.length }}</span>
        </div>
        <div v-if="courseTree.length" class="course-tree">
          <details
            v-for="chapter in courseTree"
            :key="chapter.key"
            class="chapter-node"
            :open="selectedVideo?.group === activeSeries && selectedVideo?.chapterLabel === chapter.label"
          >
            <summary class="chapter-summary" @click="selectFilter(chapter.key)">
              <div class="filter-main">
                <span>{{ chapter.label }}</span>
                <small v-if="chapter.watchedCount">{{ chapter.watchedCount }} 节已学</small>
              </div>
              <span class="filter-count">{{ chapter.count }}</span>
            </summary>

            <div class="course-children">
              <button
                v-for="course in chapter.courses"
                :key="course.key"
                :class="['course-leaf', { active: selectedKey === course.key }]"
                @click="selectVideo(course)"
              >
                <span>{{ course.title }}</span>
                <small v-if="courseProgress(course)">{{ progressLabel(course) }}</small>
              </button>
            </div>
          </details>
        </div>
        <div v-else class="empty-side-copy">
          当前没有可展示的系统教材。
        </div>
      </div>

    </aside>

    <section class="content">
      <div class="content-grid">
        <div class="player-panel">
          <div v-if="!selectedVideo" class="state-box">
            从左侧教材树选择一节课开始学习
          </div>
          <template v-else>
            <div class="player-header">
              <div>
                <span class="panel-tag">系统课程</span>
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
                <button
                  class="danger-btn"
                  :disabled="deletingCourse"
                  @click="deleteSelectedCourse"
                >
                  {{ deletingCourse ? '删除中...' : '删除课时' }}
                </button>
              </div>
            </div>

            <div class="video-frame">
              <video
                v-if="selectedVideo.path"
                ref="videoPlayerRef"
                :src="selectedVideo.url"
                controls
                controlsList="nodownload"
                @loadedmetadata="handleVideoReady"
                @timeupdate="handleVideoProgress"
              ></video>
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
                <div class="detail-card detail-card-wide">
                  <h4>课程摘要</h4>
                  <p>{{ selectedVideo.summary || selectedVideo.subtitle || '当前还没有课程摘要。' }}</p>
                  <div class="detail-hints">
                    <span>{{ selectedVideo.recommendedFor || '补完文字内容后，这里会更准。' }}</span>
                  </div>
                </div>

                <div class="detail-card transcript-card detail-card-wide">
                  <div class="transcript-header">
                    <h4>课程笔记</h4>
                    <div class="transcript-actions">
                      <button
                        class="ghost-btn"
                        :disabled="generatingTranscript"
                        @click="loadTranscript(selectedVideo.id)"
                      >
                        刷新
                      </button>
                      <button
                        class="assistant-btn secondary"
                        :disabled="generatingTranscript || transcriptLoading"
                        @click="generateTranscript"
                      >
                        {{ generatingTranscript ? '生成中...' : (transcript ? '重新生成 transcript' : '生成 transcript') }}
                      </button>
                    </div>
                  </div>
                  <div v-if="transcriptLoading" class="empty-copy">
                    {{ generatingTranscript ? 'Whisper 正在整理当前课程 transcript...' : '加载笔记中...' }}
                  </div>
                  <pre v-else class="transcript">{{ transcript || "当前课程暂无 transcript" }}</pre>
                </div>

                <div v-if="selectedVideo.transcriptAvailable || selectedVideo.transcriptPreview" class="detail-card transcript-preview-card">
                  <h4>文字内容预览</h4>
                  <p>{{ selectedVideo.transcriptPreview || '当前还没有可用的文字内容预览。' }}</p>
                </div>

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
                    <li><span>学习重点</span><strong>{{ selectedVideo.learningFocus || '待整理' }}</strong></li>
                    <li><span>标签</span><strong>{{ selectedVideo.tags?.join(' / ') || '暂无标签' }}</strong></li>
                  </ul>
                </div>

                <div class="detail-card detail-card-wide">
                  <h4>适合怎么用</h4>
                  <p>{{ selectedVideo.recommendedFor || '当前信息还不够，补 transcript 后会更准。' }}</p>
                </div>

                <div class="detail-card detail-card-wide">
                  <h4>关键点</h4>
                  <ul v-if="selectedVideo.keyPoints?.length" class="key-point-list">
                    <li v-for="(point, index) in selectedVideo.keyPoints" :key="`${selectedVideo.id}-point-${index}`">
                      {{ point }}
                    </li>
                  </ul>
                  <p v-else>当前还没有提炼出关键点。</p>
                </div>

                <div v-if="selectedVideo.type === 'course'" class="detail-card detail-card-wide">
                  <h4>适合回到这些歌验证</h4>
                  <div v-if="relatedSongsLoading" class="empty-copy">正在整理这节课更适合回到哪些歌验证...</div>
                  <div v-else-if="relatedSongs.length" class="linked-song-list">
                    <article
                      v-for="song in relatedSongs"
                      :key="`course-song-${song.id}`"
                      class="linked-song-card"
                    >
                      <div class="linked-song-copy">
                        <strong>{{ song.title }}</strong>
                        <p>{{ song.artist || '歌曲练习' }}</p>
                        <span>{{ song.reason }}</span>
                      </div>
                      <button class="ghost-btn" @click="openRelatedSong(song.id)">去练这首歌</button>
                    </article>
                  </div>
                  <p v-else class="empty-copy">这节课当前还没有明确命中的歌曲，后面补完 transcript 和标签后会更准。</p>
                </div>

                <div class="assistant-section">
                  <div class="assistant-actions">
                    <button class="assistant-btn" @click="showQA = !showQA">
                      {{ showQA ? '收起小霞问答' : '打开小霞问答' }}
                    </button>
                    <button class="assistant-btn secondary" :disabled="practiceLoading" @click="generatePractice">
                      {{ practiceLoading ? '生成中...' : '生成练习任务' }}
                    </button>
                  </div>

                  <div v-if="showQA" class="assistant-card">
                    <div class="assistant-header">
                      <h4>小霞问答</h4>
                      <span>基于当前课程内容回答</span>
                    </div>

                    <div class="qa-messages" ref="qaMessagesRef">
                      <div
                        v-for="(message, index) in qaMessages"
                        :key="index"
                        :class="['qa-message', message.role]"
                      >
                        <div class="qa-bubble">{{ message.content }}</div>
                      </div>
                      <div v-if="qaLoading" class="qa-message assistant">
                        <div class="qa-bubble">小霞整理课程内容中...</div>
                      </div>
                    </div>

                    <div class="qa-input-row">
                      <input
                        v-model="qaInput"
                        class="text-input"
                        type="text"
                        placeholder="比如：老师这里说的和弦转换关键点是什么？"
                        :disabled="qaLoading"
                        @keydown.enter="sendQuestion"
                      />
                      <button class="assistant-btn" :disabled="qaLoading || !qaInput.trim()" @click="sendQuestion">
                        发送
                      </button>
                    </div>
                  </div>

                  <div v-if="practiceResult" class="assistant-card practice-card">
                    <div class="assistant-header">
                      <h4>今日练习任务</h4>
                      <select v-model="practiceLevel" class="text-input practice-level" @change="generatePractice">
                        <option value="入门">入门</option>
                        <option value="进阶">进阶</option>
                        <option value="高级">高级</option>
                      </select>
                    </div>

                    <div v-if="practiceLoading" class="empty-copy">小霞正在生成更贴合课程的练习计划...</div>
                    <template v-else>
                      <ol class="practice-list">
                        <li v-for="(task, index) in practiceResult.tasks" :key="index">{{ task }}</li>
                      </ol>
                      <div v-if="practiceResult.tips" class="practice-tips">
                        <h5>小霞贴士</h5>
                        <pre>{{ practiceResult.tips }}</pre>
                      </div>
                    </template>
                  </div>
                </div>
              </aside>
            </div>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import seedIndex from '../../../backend/data/index.json'

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
const videoPlayerRef = ref(null)
const recentState = ref(loadPersistedState())
const deletingCourse = ref(false)
const relatedSongs = ref([])
const relatedSongsLoading = ref(false)

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

const courseTree = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  const chapterMap = new Map()

  for (const item of allVideos.value) {
    if (item.type !== 'course') continue
    if (activeSeries.value && item.group !== activeSeries.value) continue

    const haystacks = [
      item.title,
      item.subtitle,
      item.group,
      item.chapterLabel,
      item.summary,
      item.learningFocus,
      item.recommendedFor,
      ...(item.keyPoints || []),
      ...(item.tags || []),
    ]
    const matches = !keyword || haystacks.some(value => (value || '').toLowerCase().includes(keyword))
    if (!matches) continue

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

const filteredVideos = computed(() => {
  let items = allVideos.value

  if (activeSeries.value) {
    items = items.filter(item => item.group === activeSeries.value)
  }
  if (activeFilter.value.startsWith('chapter:')) {
    const [series, chapter] = activeFilter.value.slice('chapter:'.length).split('|||')
    items = items.filter(item => item.group === series && item.chapterLabel === chapter)
  }

  const keyword = searchQuery.value.trim().toLowerCase()
  if (!keyword) {
    return items
  }

  return items.filter(item => {
    const haystacks = [
      item.title,
      item.subtitle,
      item.group,
      item.chapterLabel,
      item.author,
      item.summary,
      item.learningFocus,
      item.recommendedFor,
      ...(item.keyPoints || []),
      ...(item.tags || []),
    ]
    return haystacks.some(value => (value || '').toLowerCase().includes(keyword))
  })
})

const currentFilterLabel = computed(() => {
  const current = chapterFilters.value.find(item => item.key === activeFilter.value)
  if (current?.label) return current.label
  return searchQuery.value.trim() ? `搜索：${searchQuery.value.trim()}` : '系统教材'
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
  if (!video?.path) return
  await nextTick()
  const player = videoPlayerRef.value
  const progress = recentState.value.progress?.[video.key]
  if (player && progress?.position) {
    player.currentTime = progress.position
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
    courses.value = seedIndex.courses || []
    error.value = ''
  } finally {
    await loadIntelligenceSummary()
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

async function loadIntelligenceSummary() {
  try {
    const response = await fetch('/api/courses/intelligence-summary')
    if (!response.ok) throw new Error('内容整理概览加载失败')
    intelligenceSummary.value = await response.json()
  } catch {
    intelligenceSummary.value = null
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
    const firstCourse = filteredVideos.value[0]
    if (firstCourse) {
      selectVideo(firstCourse)
    }
  }
}

function selectFilter(key) {
  activeFilter.value = key
  if (!filteredVideos.value.find(item => item.key === selectedKey.value) && filteredVideos.value.length > 0) {
    selectVideo(filteredVideos.value[0])
  }
}

async function selectVideo(item) {
  activeSeries.value = item.group
  selectedKey.value = item.key
  transcript.value = ''
  relatedSongs.value = []
  rememberVideo(item)
  resetAssistantState(item.type)
  if (item.type === 'course') {
    await loadTranscript(item.id)
    await loadRelatedSongs(item.id)
  }
}

async function loadTranscript(courseId) {
  transcriptLoading.value = true
  try {
    if (isFilePreview()) {
      transcript.value = ''
      return
    }
    const response = await fetch(`/api/courses/${courseId}/transcript`)
    if (!response.ok) throw new Error('课程笔记加载失败')
    const data = await response.json()
    transcript.value = data.content || ''
  } catch (err) {
    transcript.value = `加载失败：${err.message}`
  } finally {
    transcriptLoading.value = false
  }
}

async function generateTranscript() {
  if (!selectedVideo.value || selectedVideo.value.type !== 'course' || generatingTranscript.value || isFilePreview()) {
    return
  }

  generatingTranscript.value = true
  transcriptLoading.value = true
  transcript.value = ''

  try {
    const response = await fetch(`/api/courses/${selectedVideo.value.id}/generate-transcript?coach_model=${encodeURIComponent(currentCoachModel())}`, {
      method: 'POST',
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '生成 transcript 失败')

    transcript.value = data.content || ''
    if (data.course?.id) {
      courses.value = courses.value.map(item => item.id === data.course.id ? data.course : item)
    }
    await loadIntelligenceSummary()
  } catch (err) {
    transcript.value = `生成失败：${err.message}`
  } finally {
    generatingTranscript.value = false
    transcriptLoading.value = false
  }
}

async function generatePendingTranscripts() {
  if (batchGeneratingTranscript.value || transcriptPendingCount.value === 0) return

  batchGeneratingTranscript.value = true
  error.value = ''
  try {
    const response = await fetch('/api/courses/generate-transcripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ limit: 3, coach_model: currentCoachModel() }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '批量生成 transcript 失败')
    courses.value = data.courses || courses.value
    await loadIntelligenceSummary()
    if (data.failures?.length) {
      error.value = `有 ${data.failures.length} 节课程生成失败，请稍后重试。`
    }
  } catch (err) {
    error.value = err.message
  } finally {
    batchGeneratingTranscript.value = false
  }
}

async function rebuildIntelligence() {
  rebuildingIntelligence.value = true
  error.value = ''
  try {
    const response = await fetch('/api/courses/rebuild-intelligence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ coach_model: currentCoachModel() }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || '刷新内容理解失败')
    courses.value = data.courses || []
    await loadIntelligenceSummary()
  } catch (err) {
    error.value = err.message
  } finally {
    rebuildingIntelligence.value = false
  }
}

function currentCoachModel() {
  if (typeof window === 'undefined') return 'deepseek-r1:8b'
  return window.localStorage.getItem(COACH_MODEL_STORAGE_KEY) || 'deepseek-r1:8b'
}

async function openPriorityCourse(courseId) {
  const target = allVideos.value.find(item => item.id === courseId)
  if (!target) return
  await selectVideo(target)
}

async function loadRelatedSongs(courseId) {
  if (!courseId || isFilePreview()) {
    relatedSongs.value = []
    return
  }
  relatedSongsLoading.value = true
  try {
    const response = await fetch(`/api/courses/${courseId}/related-songs`)
    if (!response.ok) throw new Error('关联歌曲加载失败')
    relatedSongs.value = await response.json()
  } catch {
    relatedSongs.value = []
  } finally {
    relatedSongsLoading.value = false
  }
}

async function sendQuestion() {
  if (!selectedVideo.value || selectedVideo.value.type !== 'course') return
  if (!qaInput.value.trim() || qaLoading.value) return

  const question = qaInput.value.trim()
  qaMessages.value.push({ role: 'user', content: question })
  qaInput.value = ''
  qaLoading.value = true
  await scrollQaToBottom()

  try {
    const response = await fetch(`/api/courses/${selectedVideo.value.id}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        transcript: transcript.value,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || '小霞回答失败')
    }
    qaMessages.value.push({ role: 'assistant', content: data.answer })
  } catch (err) {
    qaMessages.value.push({
      role: 'assistant',
      content: `这次回答失败了：${err.message}`,
    })
  } finally {
    qaLoading.value = false
    await scrollQaToBottom()
  }
}

async function generatePractice() {
  if (!selectedVideo.value || selectedVideo.value.type !== 'course') return

  practiceLoading.value = true
  if (!practiceResult.value) {
    practiceResult.value = { tasks: [], tips: '' }
  }

  try {
    const response = await fetch('/api/courses/generate-practice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: selectedVideo.value.title,
        level: practiceLevel.value,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || '生成练习任务失败')
    }
    practiceResult.value = data
  } catch (err) {
    practiceResult.value = {
      tasks: [`生成失败：${err.message}`],
      tips: '',
    }
  } finally {
    practiceLoading.value = false
  }
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

function handleVideoProgress(event) {
  const current = selectedVideo.value
  if (!current?.path) return
  const position = Math.floor(event.target.currentTime || 0)
  const previous = recentState.value.progress?.[current.key]?.position || 0
  if (Math.abs(position - previous) < 5) return
  rememberVideo(current, position)
}

function handleVideoReady() {
  const player = videoPlayerRef.value
  const position = resumeInfo.value?.position || 0
  if (player && position > 0 && position < player.duration - 3) {
    player.currentTime = position
  }
}

function resumePlayback() {
  const player = videoPlayerRef.value
  const position = resumeInfo.value?.position || 0
  if (!player || !position) return
  player.currentTime = position
  player.play().catch(() => {})
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

onBeforeUnmount(() => {
  if (selectedVideo.value && videoPlayerRef.value) {
    rememberVideo(selectedVideo.value, Math.floor(videoPlayerRef.value.currentTime || 0))
  }
})

onMounted(() => {
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
  grid-template-columns: repeat(auto-fit, minmax(128px, 1fr));
  gap: 6px;
  margin-top: 12px;
  padding: 6px 0;
  background: #16213e;
}

.series-tab {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9px;
  padding: 8px 9px;
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
  margin-top: 3px;
  color: #95a2bf;
  font-size: 10.5px;
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
  padding: 12px;
}

.video-frame {
  margin: 14px 0 16px;
  border-radius: 14px;
  overflow: hidden;
  background: #0a1022;
}

.video-frame video {
  width: 100%;
  display: block;
  background: #000;
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
  .detail-layout {
    grid-template-columns: 1fr;
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
