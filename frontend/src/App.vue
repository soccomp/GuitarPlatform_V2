<template>
  <div class="app">
    <header class="header">
      <h1>🎸 吉他学习平台 v2</h1>
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
    </header>
    <main class="main">
      <SystemCourses v-if="currentTab === 'courses'" />
      <LearningVideos v-else-if="currentTab === 'learning'" />
      <Songs v-else-if="currentTab === 'songs'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SystemCourses from './views/SystemCourses.vue'
import LearningVideos from './views/LearningVideos.vue'
import Songs from './views/Songs.vue'

const currentTab = ref('courses')
const tabs = [
  { id: 'courses', label: '🌲 系统教材' },
  { id: 'learning', label: '🎬 学习视频' },
  { id: 'songs', label: '🎵 歌曲练习' },
]
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
  max-width: 1340px;
  margin: 0 auto;
  padding: 24px 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding: 12px 0;
}

.header h1 {
  font-size: 30px;
  color: #fff7ed;
}

.nav {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.nav button {
  background: rgba(15, 23, 48, 0.9);
  color: #d1d5db;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 15px;
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
}
</style>
