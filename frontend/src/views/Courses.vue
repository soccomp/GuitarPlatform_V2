<template>
  <div class="courses-view">
    <div class="course-list">
      <h2>课程列表</h2>
      <div v-for="course in courses" :key="course.id" @click="selectCourse(course)">
        <CourseCard :course="course" :selected="selectedCourse?.id === course.id" />
      </div>
      <p v-if="courses.length === 0" class="empty">暂无课程</p>
    </div>
    <div class="course-detail">
      <template v-if="selectedCourse">
        <h2>{{ selectedCourse.title }}</h2>
        <p class="description">{{ selectedCourse.description }}</p>
        <div class="transcript" v-if="transcript">
          <h3>课程内容</h3>
          <pre>{{ transcript }}</pre>
        </div>
      </template>
      <p v-else class="empty">请选择一个课程</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import CourseCard from '../components/CourseCard.vue'

const courses = ref([])
const selectedCourse = ref(null)
const transcript = ref('')

async function fetchCourses() {
  const res = await fetch('/api/courses')
  courses.value = await res.json()
}

async function selectCourse(course) {
  selectedCourse.value = course
  const res = await fetch(`/api/courses/${course.id}/transcript`)
  const data = await res.json()
  transcript.value = data.content || '暂无 transcript 内容'
}

onMounted(fetchCourses)
</script>

<style scoped>
.courses-view {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  height: calc(100vh - 120px);
}

.course-list {
  background: #16213e;
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
}

.course-list h2 {
  margin-bottom: 16px;
  color: #e94560;
}

.course-detail {
  background: #16213e;
  border-radius: 12px;
  padding: 24px;
  overflow-y: auto;
}

.course-detail h2 {
  color: #e94560;
  margin-bottom: 8px;
}

.description {
  color: #aaa;
  margin-bottom: 24px;
}

.transcript h3 {
  color: #eee;
  margin-bottom: 12px;
}

.transcript pre {
  background: #0f3460;
  padding: 16px;
  border-radius: 8px;
  white-space: pre-wrap;
  line-height: 1.6;
}

.empty {
  color: #666;
  text-align: center;
  margin-top: 48px;
}
</style>