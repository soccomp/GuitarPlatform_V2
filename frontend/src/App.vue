<template>
  <div class="app">
    <header class="header">
      <div class="header-main">
        <h1>吉他学习平台</h1>
      </div>
      <div class="header-tools">
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
import { onBeforeUnmount, onMounted, ref } from 'vue'
import SystemCourses from './views/SystemCourses.vue'
import LearningVideos from './views/LearningVideos.vue'
import Songs from './views/Songs.vue'

const currentTab = ref('courses')
const tabs = [
  { id: 'courses', label: '🌲 系统教材' },
  { id: 'learning', label: '🎬 学习视频' },
  { id: 'songs', label: '🎵 歌曲练习' },
]

function handleNavigate(event) {
  const tab = event?.detail?.tab
  if (tab && tabs.some(item => item.id === tab)) {
    currentTab.value = tab
  }
}

onMounted(() => {
  window.addEventListener('guitar-platform-navigate', handleNavigate)
})

onBeforeUnmount(() => {
  window.removeEventListener('guitar-platform-navigate', handleNavigate)
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

.nav {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
}

.nav button {
  border: 0;
  border-radius: 999px;
  padding: 9px 14px;
  color: #cbd5f5;
  background: transparent;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.nav button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav button.active {
  background: linear-gradient(135deg, #f97316, #fb7185);
  color: #111827;
  font-weight: 700;
}

.main {
  min-height: 80vh;
}

@media (max-width: 900px) {
  .header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-main,
  .header-tools {
    width: 100%;
  }

  .header-tools {
    flex-direction: column;
    align-items: stretch;
  }

  .nav {
    width: 100%;
    overflow-x: auto;
  }
}
</style>
