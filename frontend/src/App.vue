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
      <Courses v-if="currentTab === 'courses'" />
      <Songs v-else-if="currentTab === 'songs'" />
      <Videos v-else-if="currentTab === 'videos'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Courses from './views/Courses.vue'
import Songs from './views/Songs.vue'
import Videos from './views/Videos.vue'

const currentTab = ref('courses')
const tabs = [
  { id: 'courses', label: '📚 课程学习' },
  { id: 'songs',   label: '🎵 歌曲练习' },
  { id: 'videos',  label: '📹 收藏视频' },
]
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0f0f1a;
  color: #eee;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  min-height: 100vh;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 16px;
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header h1 {
  font-size: 28px;
  color: #e94560;
  margin-bottom: 16px;
}

.nav {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.nav button {
  background: #16213e;
  color: #ccc;
  border: 2px solid #16213e;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav button:hover {
  border-color: #e94560;
  color: #fff;
}

.nav button.active {
  background: #1a1a2e;
  border-color: #e94560;
  color: #e94560;
}

.main {
  min-height: 500px;
}
</style>
