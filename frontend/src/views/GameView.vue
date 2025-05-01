<template>
  <div class="game">
    <div class="game-header">
      <h1>{{ script?.title }}</h1>
      <div class="game-controls">
        <el-button type="primary" @click="startGame">开始游戏</el-button>
        <el-button type="info" @click="exitGame">退出游戏</el-button>
      </div>
    </div>

    <div class="game-content">
      <div class="game-info">
        <el-card class="script-info">
          <template #header>
            <div class="card-header">
              <span>剧本信息</span>
            </div>
          </template>
          <div class="script-content">
            <p>{{ script?.content }}</p>
          </div>
        </el-card>

        <el-card class="game-status">
          <template #header>
            <div class="card-header">
              <span>游戏状态</span>
            </div>
          </template>
          <div class="status-content">
            <p>当前阶段：{{ gameSession?.phase }}</p>
            <p>当前回合：{{ gameSession?.round_number }}</p>
            <p>当前发言者：{{ gameSession?.current_speaker }}</p>
          </div>
        </el-card>
      </div>

      <div class="game-chat">
        <el-card class="chat-messages">
          <template #header>
            <div class="card-header">
              <span>聊天记录</span>
            </div>
          </template>
          <div class="messages-content">
            <div v-for="(message, index) in messages" :key="index" class="message-item">
              <span class="message-sender">{{ message.sender }}:</span>
              <span class="message-content">{{ message.content }}</span>
            </div>
          </div>
        </el-card>

        <div class="chat-input">
          <el-input
            v-model="newMessage"
            placeholder="输入消息..."
            @keyup.enter="sendMessage"
          >
            <template #append>
              <el-button @click="sendMessage">发送</el-button>
            </template>
          </el-input>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const script = ref(null)
const gameSession = ref(null)
const messages = ref([])
const newMessage = ref('')
let messagePolling = null

const fetchScript = async () => {
  try {
    const response = await axios.get(`/api/scripts/${route.query.scriptId}`)
    script.value = response.data
  } catch (error) {
    console.error('获取剧本失败:', error)
    ElMessage.error('获取剧本失败')
  }
}

const startGame = async () => {
  try {
    const response = await axios.post('/api/game/start', {
      script_id: route.query.scriptId,
      ai_count: 0,
      is_all_ai: false
    })
    gameSession.value = response.data
    startMessagePolling()
  } catch (error) {
    console.error('开始游戏失败:', error)
    ElMessage.error('开始游戏失败')
  }
}

const sendMessage = async () => {
  if (!newMessage.value.trim()) return
  
  try {
    await axios.post(`/api/game/${gameSession.value.id}/message`, {
      content: newMessage.value,
      sender: 'user'
    })
    newMessage.value = ''
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
  }
}

const startMessagePolling = () => {
  messagePolling = setInterval(async () => {
    try {
      const response = await axios.get(`/api/game/${gameSession.value.id}`)
      gameSession.value = response.data
      messages.value = response.data.messages || []
    } catch (error) {
      console.error('获取游戏状态失败:', error)
    }
  }, 2000)
}

const exitGame = () => {
  if (messagePolling) {
    clearInterval(messagePolling)
  }
  router.push('/scripts')
}

onMounted(() => {
  fetchScript()
})

onUnmounted(() => {
  if (messagePolling) {
    clearInterval(messagePolling)
  }
})
</script>

<style scoped>
.game {
  padding: 20px;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.game-content {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 20px;
}

.game-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.script-content {
  max-height: 300px;
  overflow-y: auto;
}

.game-chat {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.messages-content {
  height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.message-item {
  margin-bottom: 10px;
}

.message-sender {
  font-weight: bold;
  margin-right: 10px;
}

.chat-input {
  margin-top: auto;
}
</style> 