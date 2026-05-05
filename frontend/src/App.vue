<template>
  <div class="app">
    <header class="header">
      <div class="header-main">
        <h1>吉他学习平台</h1>
      </div>
      <div class="header-tools">
        <div v-if="coachStatus" class="global-coach-status">
          <span :class="['global-coach-light', coachStatus.state]"></span>
          <strong>{{ selectedCoachModelLabel }}</strong>
          <span class="global-coach-inline-status">{{ coachStatus.connected ? '已连接' : '未连接' }}</span>
          <span class="global-coach-inline-mode">{{ coachStatus.mode === 'remote_node' ? '4080 节点' : '本地预览' }}</span>
          <select v-model="selectedCoachModel" class="global-coach-model-select" @change="persistCoachModel">
            <option v-for="item in coachModels" :key="item.value" :value="item.value">
              {{ item.label }}
            </option>
          </select>
        </div>
        <nav class="nav">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="{ active: currentTab === tab.id }"
          @click="currentTab = tab.id"
        >
          {{ tab.label }}
        </button>
        </nav>
      </div>
    </header>
    <main class="main">
      <SystemCourses v-if="currentTab === 'courses'" />
      <LearningVideos v-else-if="currentTab === 'learning'" />
      <Songs v-else-if="currentTab === 'songs'" />
    </main>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import SystemCourses from './views/SystemCourses.vue'
import LearningVideos from './views/LearningVideos.vue'
import Songs from './views/Songs.vue'

const COACH_MODEL_STORAGE_KEY = 'guitar-platform-coach-model'
const COACH_MODELS = [
  { value: 'qwen3:8b', label: 'Qwen 3 8B' },
  { value: 'deepseek-r1:8b', label: 'DeepSeek R1 8B' },
]

const currentTab = ref('courses')
const coachStatus = ref(null)
const coachModels = COACH_MODELS
const selectedCoachModel = ref(loadCoachModel())
let coachStatusTimer = null
const tabs = [
  { id: 'courses', label: '🌲 系统教材' },
  { id: 'learning', label: '🎬 学习视频' },
  { id: 'songs', label: '🎵 歌曲练习' },
]

function loadCoachModel() {
  return window.localStorage.getItem(COACH_MODEL_STORAGE_KEY) || 'deepseek-r1:8b'
}

function persistCoachModel() {
  window.localStorage.setItem(COACH_MODEL_STORAGE_KEY, selectedCoachModel.value)
  if (coachStatus.value) {
    coachStatus.value = {
      ...coachStatus.value,
      coach_model: selectedCoachModel.value,
    }
  }
  window.dispatchEvent(new CustomEvent('guitar-platform-coach-model-change', { detail: { model: selectedCoachModel.value } }))
}

const selectedCoachModelLabel = computed(() => {
  return coachModels.find(item => item.value === selectedCoachModel.value)?.label || selectedCoachModel.value
})

function handleNavigate(event) {
  const tab = event?.detail?.tab
  if (tab && tabs.some(item => item.id === tab)) {
    currentTab.value = tab
  }
}

async function loadCoachStatus() {
  try {
    const response = await fetch('/api/coach/status')
    if (!response.ok) throw new Error('大模型状态加载失败')
    coachStatus.value = await response.json()
    coachStatus.value.coach_model = selectedCoachModel.value
  } catch (error) {
    coachStatus.value = {
      configured: false,
      mode: 'local_preview',
      coach_model: selectedCoachModel.value,
      connected: false,
      state: 'unreachable',
      status_text: error.message || '大模型状态暂时不可用',
      node_name: '',
    }
  }
}

onMounted(() => {
  window.addEventListener('guitar-platform-navigate', handleNavigate)
  persistCoachModel()
  loadCoachStatus()
  coachStatusTimer = window.setInterval(loadCoachStatus, 30000)
})

onBeforeUnmount(() => {
  window.removeEventListener('guitar-platform-navigate', handleNavigate)
  if (coachStatusTimer) {
    window.clearInterval(coachStatusTimer)
    coachStatusTimer = null
  }
})
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background:
    radial-gradient(circle at top, rgba(249, 115, 22, 0.18), transparent 30%),
    linear-gradient(180deg, #0b1020 0%, #111827 100%);
  color: #eee;
  font-family: 'Avenir Next', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  min-height: 100vh;
}

.app {
  max-width: 1280px;
  margin: 0 auto;
  padding: 14px 14px 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  padding: 4px 0;
}

.header-main {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 0 0 auto;
}

.header-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
}

.header h1 {
  font-size: 22px;
  color: #fff7ed;
  letter-spacing: 0.01em;
}

.global-coach-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 26px;
  max-width: 100%;
  padding: 3px 7px;
  border-radius: 999px;
  background: rgba(8, 14, 28, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: #cbd5e1;
  overflow: hidden;
  flex: 1 1 auto;
}

.global-coach-light {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  flex: 0 0 auto;
  background: #64748b;
  box-shadow: 0 0 0 2px rgba(100, 116, 139, 0.14);
}

.global-coach-light.connected {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.16);
}

.global-coach-light.unreachable,
.global-coach-light.not_configured {
  background: #f59e0b;
  box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.16);
}

.global-coach-status strong {
  flex: 0 0 auto;
  color: #f8fafc;
  font-size: 11px;
  font-weight: 600;
}

.global-coach-inline-status,
.global-coach-inline-mode,
.global-coach-inline-node {
  flex: 0 0 auto;
  border-radius: 999px;
  background: rgba(15, 23, 48, 0.86);
  color: #cbd5e1;
  padding: 2px 6px;
  font-size: 9.5px;
  line-height: 1;
}

.global-coach-inline-copy {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #94a3b8;
  font-size: 11px;
}

.global-coach-model-select {
  border-radius: 999px;
  border: 1px solid rgba(249, 115, 22, 0.2);
  background: rgba(15, 23, 48, 0.95);
  color: #fff7ed;
  padding: 2px 7px;
  font-size: 9.5px;
  line-height: 1.2;
  flex: 0 0 auto;
}

.nav {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  flex: 0 0 auto;
}

.nav button {
  background: rgba(15, 23, 48, 0.9);
  color: #d1d5db;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  padding: 8px 13px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav button:hover {
  border-color: #f97316;
  color: #fff;
}

.nav button.active {
  background: #f97316;
  border-color: #f97316;
  color: #fff7ed;
}

.main {
  min-height: 680px;
}

@media (max-width: 760px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-tools {
    width: 100%;
    align-items: flex-start;
    flex-direction: column;
  }

  .global-coach-status {
    display: flex;
    width: 100%;
  }
}
</style>
