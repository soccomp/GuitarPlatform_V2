<template>
  <div id="app">
    <nav class="top-nav">
      <h1>🎸 吉他学习平台 v2</h1>
      <div class="nav-links">
        <button @click="currentView = 'courses'" :class="{ active: currentView === 'courses' }">课程学习</button>
        <button @click="currentView = 'songs'" :class="{ active: currentView === 'songs' }">歌曲练习</button>
        <button @click="currentView = 'videos'" :class="{ active: currentView === 'videos' }">收藏视频</button>
      </div>
    </nav>
    <main>
      <Courses v-if="currentView === 'courses'" />
      <Songs v-else-if="currentView === 'songs'" />
      <Videos v-else-if="currentView === 'videos'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Courses from './views/Courses.vue'
import Songs from './views/Songs.vue'
import Videos from './views/Videos.vue'

const currentView = ref('courses')
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #1a1a2e;
  color: #eee;
}

#app {
  min-height: 100vh;
}

.top-nav {
  background: #16213e;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

.top-nav h1 {
  font-size: 20px;
  color: #e94560;
}

.nav-links {
  display: flex;
  gap: 12px;
}

.nav-links button {
  background: transparent;
  border: 1px solid #e94560;
  color: #e94560;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-links button.active,
.nav-links button:hover {
  background: #e94560;
  color: #fff;
}

main {
  padding: 24px;
}
</style>