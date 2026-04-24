<template>
  <div class="course-card" :class="{ selected }">
    <h3>{{ course.title }}</h3>
    <p>{{ course.description }}</p>
  </div>
</template>

<script setup>
defineProps({
  course: Object,
  selected: Boolean
})
</script>

<style scoped>
.course-card {
  background: #0f3460;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.course-card:hover {
  border-color: #e94560;
}

.course-card.selected {
  border-color: #e94560;
  background: #1a1a2e;
}

.course-card h3 {
  color: #eee;
  font-size: 15px;
  margin-bottom: 6px;
}

.course-card p {
  color: #888;
  font-size: 13px;
}
</style>