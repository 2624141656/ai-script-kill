<template>
  <div class="scripts">
    <h1>剧本列表</h1>
    
    <div class="filter-container">
      <el-select v-model="selectedCategory" placeholder="选择剧本类型">
        <el-option
          v-for="category in scriptCategories"
          :key="category.value"
          :label="category.label"
          :value="category.value"
        />
      </el-select>
    </div>

    <div class="script-list">
      <el-card v-for="script in scripts" :key="script.id" class="script-card">
        <template #header>
          <div class="card-header">
            <span>{{ script.title }}</span>
            <el-tag :type="getCategoryTagType(script.category)">
              {{ getCategoryLabel(script.category) }}
            </el-tag>
          </div>
        </template>
        <div class="script-content">
          <p>{{ script.content }}</p>
        </div>
        <div class="card-footer">
          <el-button type="primary" @click="startGame(script)">开始游戏</el-button>
          <el-button type="warning" @click="decryptScript(script)">解密剧本</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const scripts = ref([])
const selectedCategory = ref('')
const scriptCategories = [
  { label: '古风类', value: 'ancient' },
  { label: '都市类', value: 'urban' },
  { label: '灵异类', value: 'supernatural' },
  { label: '二次元类', value: 'anime' },
  { label: '搞笑类', value: 'comedy' },
  { label: '解密类', value: 'mystery' },
  { label: '失恋了随便玩玩类', value: 'casual' }
]

const getCategoryLabel = (category) => {
  const found = scriptCategories.find(c => c.value === category)
  return found ? found.label : category
}

const getCategoryTagType = (category) => {
  const types = {
    ancient: 'success',
    urban: 'info',
    supernatural: 'warning',
    anime: 'danger',
    comedy: 'success',
    mystery: 'warning',
    casual: 'info'
  }
  return types[category] || 'info'
}

const fetchScripts = async () => {
  try {
    const response = await axios.get('/api/scripts', {
      params: {
        category: selectedCategory.value
      }
    })
    scripts.value = response.data
  } catch (error) {
    console.error('获取剧本列表失败:', error)
  }
}

const startGame = (script) => {
  router.push({
    path: '/game',
    query: {
      scriptId: script.id
    }
  })
}

const decryptScript = async (script) => {
  try {
    const response = await axios.post(`/api/scripts/decrypt`, {
      script_id: script.id
    })
    script.content = response.data.content
  } catch (error) {
    console.error('解密剧本失败:', error)
  }
}

onMounted(() => {
  fetchScripts()
})
</script>

<style scoped>
.scripts {
  padding: 20px;
}

.filter-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
}

.script-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 20px;
}

.script-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.script-content {
  margin: 10px 0;
  max-height: 200px;
  overflow-y: auto;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}
</style> 