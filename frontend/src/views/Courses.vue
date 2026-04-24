<template>
  <div class="courses-layout">
    <!-- 左侧：课程列表 -->
    <aside class="sidebar">
      <h2>课程列表</h2>
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else>
        <CourseCard
          v-for="course in courses"
          :key="course.id"
          :course="course"
          :selected="selectedId === course.id"
          @click="selectCourse(course)"
        />
        <p v-if="courses.length === 0" class="empty">暂无课程</p>
      </div>
    </aside>

    <!-- 右侧：课程详情 -->
    <section class="detail">
      <div v-if="!selected" class="placeholder">
        <p>👈 请选择一门课程</p>
      </div>
      <div v-else>
        <h2>{{ selected.title }}</h2>
        <p class="desc">{{ selected.description }}</p>

        <!-- 视频播放器 -->
        <div v-if="selected.video_path" class="video-wrap">
          <video
            :src="videoUrl"
            controls
            controlsList="nodownload"
          ></video>
        </div>

        <!-- Transcript -->
        <div class="transcript-section">
          <h3>📝 课程笔记</h3>
          <div v-if="transcriptLoading" class="loading">加载笔记中...</div>
          <pre v-else class="transcript">{{ transcript }}</pre>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import CourseCard from '../components/CourseCard.vue'

const courses = ref([])
const selectedId = ref(null)
const transcript = ref('')
const loading = ref(true)
const error = ref('')
const transcriptLoading = ref(false)

const selected = computed(() =>
  courses.value.find(c => c.id === selectedId.value) || null
)

const videoUrl = computed(() => {
  if (!selected.value?.video_path) return ''
  return `/library/courses/${selected.value.video_path}`
})

async function loadCourses() {
  try {
    const res = await fetch('/api/courses')
    if (!res.ok) throw new Error('加载课程列表失败')
    courses.value = await res.json()
    if (courses.value.length > 0 && !selectedId.value) {
      selectCourse(courses.value[0])
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function selectCourse(course) {
  selectedId.value = course.id
  transcriptLoading.value = true
  transcript.value = ''
  try {
    const res = await fetch(`/api/courses/${course.id}/transcript`)
    if (!res.ok) throw new Error('加载笔记失败')
    const data = await res.json()
    transcript.value = data.content || '(暂无笔记)'
  } catch (e) {
    transcript.value = '加载失败：' + e.message
  } finally {
    transcriptLoading.value = false
  }
}

loadCourses()
</script>

<style scoped>
.courses-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  min-height: 600px;
}

.sidebar {
  background: #16213e;
  border-radius: 12px;
  padding: 20px;
}

.sidebar h2 {
  color: #e94560;
  font-size: 18px;
  margin-bottom: 16px;
}

.detail {
  background: #16213e;
  border-radius: 12px;
  padding: 24px;
}

.detail h2 {
  color: #eee;
  font-size: 22px;
  margin-bottom: 8px;
}

.desc {
  color: #888;
  margin-bottom: 20px;
}

.video-wrap {
  margin-bottom: 24px;
}

.video-wrap video {
  width: 100%;
  border-radius: 8px;
  background: #000;
}

.transcript-section h3 {
  color: #e94560;
  margin-bottom: 12px;
}

.transcript {
  background: #0f3460;
  border-radius: 8px;
  padding: 16px;
  color: #ccc;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #555;
  font-size: 18px;
}

.loading {
  color: #888;
  text-align: center;
  padding: 20px;
}

.error {
  color: #e94560;
  padding: 12px;
}

.empty {
  color: #555;
  text-align: center;
  padding: 20px;
}

@media (max-width: 768px) {
  .courses-layout {
    grid-template-columns: 1fr;
  }
}
</style>
