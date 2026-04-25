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

        <!-- 操作按钮 -->
        <div class="action-row">
          <button class="btn-ask" @click="showQA = !showQA">
            🎓 小霞问答
          </button>
          <button class="btn-practice" @click="generatePractice">
            🎸 练习任务
          </button>
        </div>

        <!-- Transcript -->
        <div class="transcript-section">
          <h3>📝 课程笔记</h3>
          <div v-if="transcriptLoading" class="loading">加载笔记中...</div>
          <pre v-else class="transcript">{{ transcript || '(暂无笔记)' }}</pre>
        </div>
      </div>
    </section>

    <!-- 小霞问答浮层 -->
    <div v-if="showQA && selected" class="qa-overlay" @click.self="showQA = false">
      <div class="qa-panel">
        <div class="qa-header">
          <span>🎓 小霞问答</span>
          <button class="btn-close" @click="showQA = false">✕</button>
        </div>

        <!-- 历史消息 -->
        <div class="qa-messages" ref="msgContainer">
          <div
            v-for="(msg, i) in qaHistory"
            :key="i"
            :class="['qa-msg', msg.role]"
          >
            <div class="msg-bubble">{{ msg.content }}</div>
          </div>
          <div v-if="qaLoading" class="qa-msg assistant">
            <div class="msg-bubble loading">小霞思考中...</div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="qa-input-row">
          <input
            v-model="qaInput"
            class="qa-input"
            :disabled="qaLoading"
            placeholder="关于这节课，问小霞任何问题..."
            @keydown.enter="sendQuestion"
          />
          <button class="btn-send" :disabled="qaLoading || !qaInput.trim()" @click="sendQuestion">
            发送
          </button>
        </div>
      </div>
    </div>

    <!-- 练习任务弹窗 -->
    <div v-if="showPractice" class="qa-overlay" @click.self="showPractice = false">
      <div class="qa-panel practice-panel">
        <div class="qa-header">
          <span>🎸 今日练习</span>
          <button class="btn-close" @click="showPractice = false">✕</button>
        </div>
        <div class="practice-content">
          <div v-if="practiceLoading" class="loading">小霞正在生成练习任务...</div>
          <div v-else-if="practiceResult">
            <div
              v-for="(task, i) in practiceResult.tasks"
              :key="i"
              class="practice-task"
            >
              <span class="task-num">{{ i + 1 }}</span>
              <span>{{ task }}</span>
            </div>
            <div v-if="practiceResult.tips" class="practice-tips">
              <h4>💡 小霞贴士</h4>
              <pre>{{ practiceResult.tips }}</pre>
            </div>
          </div>
        </div>
        <div class="qa-input-row">
          <select v-model="practiceLevel" class="level-select">
            <option value="入门">入门</option>
            <option value="进阶">进阶</option>
            <option value="高级">高级</option>
          </select>
          <button class="btn-send" @click="generatePractice">重新生成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import CourseCard from '../components/CourseCard.vue'

// ─── State ────────────────────────────────────────────────────────────────────
const courses = ref([])
const selectedId = ref(null)
const transcript = ref('')
const loading = ref(true)
const error = ref('')
const transcriptLoading = ref(false)

// Q&A
const showQA = ref(false)
const qaInput = ref('')
const qaHistory = ref([
  {
    role: 'assistant',
    content: '你好！我是小霞，这节课有任何不懂的地方，直接问我。'
  }
])
const qaLoading = ref(false)
const msgContainer = ref(null)

// Practice
const showPractice = ref(false)
const practiceLoading = ref(false)
const practiceResult = ref(null)
const practiceLevel = ref('入门')

// ─── Computed ─────────────────────────────────────────────────────────────────
const selected = computed(() =>
  courses.value.find(c => c.id === selectedId.value) || null
)

const videoUrl = computed(() => {
  if (!selected.value?.video_path) return ''
  return `/library/courses/${selected.value.video_path}`
})

// ─── Load Courses ──────────────────────────────────────────────────────────────
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

// ─── Select Course ─────────────────────────────────────────────────────────────
async function selectCourse(course) {
  selectedId.value = course.id
  transcriptLoading.value = true
  transcript.value = ''
  // Reset Q&A history when switching courses
  qaHistory.value = [
    { role: 'assistant', content: `你好！我是小霞，这节课有任何不懂的地方，直接问我。` }
  ]
  try {
    const res = await fetch(`/api/courses/${course.id}/transcript`)
    if (!res.ok) throw new Error('加载笔记失败')
    const data = await res.json()
    transcript.value = data.content || ''
  } catch (e) {
    transcript.value = '加载失败：' + e.message
  } finally {
    transcriptLoading.value = false
  }
}

// ─── Q&A ──────────────────────────────────────────────────────────────────────
async function sendQuestion() {
  const q = qaInput.value.trim()
  if (!q || qaLoading.value) return

  qaHistory.value.push({ role: 'user', content: q })
  qaInput.value = ''
  qaLoading.value = true
  scrollToBottom()

  try {
    const res = await fetch(`/api/courses/${selectedId.value}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, transcript: transcript.value })
    })
    if (!res.ok) throw new Error('小霞回答失败')
    const data = await res.json()
    qaHistory.value.push({ role: 'assistant', content: data.answer })
  } catch (e) {
    qaHistory.value.push({
      role: 'assistant',
      content: `抱歉，小霞出了点问题：${e.message}`
    })
  } finally {
    qaLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

// ─── Practice ─────────────────────────────────────────────────────────────────
async function generatePractice() {
  showPractice.value = true
  practiceLoading.value = true
  practiceResult.value = null
  try {
    const topic = selected.value?.title || '吉他基础练习'
    const res = await fetch('/api/courses/generate-practice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, level: practiceLevel.value })
    })
    if (!res.ok) throw new Error('生成失败')
    practiceResult.value = await res.json()
  } catch (e) {
    practiceResult.value = {
      tasks: [`生成失败：${e.message}`],
      tips: ''
    }
  } finally {
    practiceLoading.value = false
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────
loadCourses()
</script>

<style scoped>
.courses-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  min-height: 600px;
  position: relative;
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

.action-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.btn-ask,
.btn-practice {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  font-size: 14px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-ask {
  background: #e94560;
  color: #fff;
}

.btn-practice {
  background: #0f3460;
  color: #e94560;
  border: 1px solid #e94560;
}

.btn-ask:hover,
.btn-practice:hover {
  opacity: 0.85;
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
  max-height: 300px;
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

/* ─── Q&A 浮层 ─────────────────────────────────────────────────────────────── */
.qa-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  padding: 20px;
}

.qa-panel {
  width: 420px;
  height: 580px;
  background: #1a1a2e;
  border-radius: 16px 16px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 -4px 32px rgba(0, 0, 0, 0.5);
}

.practice-panel {
  height: 500px;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #16213e;
  color: #e94560;
  font-weight: bold;
  font-size: 15px;
}

.btn-close {
  background: none;
  border: none;
  color: #888;
  font-size: 18px;
  cursor: pointer;
}

.btn-close:hover {
  color: #e94560;
}

.qa-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-msg {
  display: flex;
}

.qa-msg.user {
  justify-content: flex-end;
}

.qa-msg.assistant {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.user .msg-bubble {
  background: #e94560;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.assistant .msg-bubble {
  background: #0f3460;
  color: #ccc;
  border-bottom-left-radius: 4px;
}

.msg-bubble.loading {
  color: #888;
  font-style: italic;
}

.qa-input-row {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #16213e;
  border-top: 1px solid #0f3460;
}

.qa-input {
  flex: 1;
  background: #0f3460;
  border: none;
  border-radius: 8px;
  padding: 10px 14px;
  color: #eee;
  font-size: 14px;
  outline: none;
}

.qa-input:focus {
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.3);
}

.qa-input::placeholder {
  color: #555;
}

.btn-send {
  background: #e94560;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.level-select {
  background: #0f3460;
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  color: #eee;
  font-size: 14px;
  cursor: pointer;
}

/* ─── 练习内容 ─────────────────────────────────────────────────────────────── */
.practice-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.practice-task {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #0f3460;
  color: #ccc;
  font-size: 14px;
  line-height: 1.5;
}

.task-num {
  color: #e94560;
  font-weight: bold;
  flex-shrink: 0;
}

.practice-tips {
  margin-top: 16px;
  background: #0f3460;
  border-radius: 8px;
  padding: 12px;
}

.practice-tips h4 {
  color: #e94560;
  margin-bottom: 8px;
  font-size: 14px;
}

.practice-tips pre {
  color: #aaa;
  font-size: 13px;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .courses-layout {
    grid-template-columns: 1fr;
  }

  .qa-panel {
    width: 100%;
    height: 70vh;
  }
}
</style>
