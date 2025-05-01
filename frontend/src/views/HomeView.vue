<template>
  <div class="home">
    <h1>剧本杀游戏</h1>
    
    <div class="selection-container">
      <el-checkbox v-model="isAllAI">全AI模式</el-checkbox>
      <el-checkbox v-model="isAllHuman">全自然用户模式</el-checkbox>
      <el-input-number 
        v-model="aiCount" 
        :min="0" 
        :max="10"
        :disabled="isAllHuman"
        placeholder="AI平台数量"
      />
    </div>

    <div class="button-container">
      <el-button type="primary" @click="showRandomScripts">默认随机剧本</el-button>
      <el-button type="success" @click="showUploadScript">用户上传剧本</el-button>
      <el-button type="warning" @click="showDecryptScript">解密随机剧本</el-button>
    </div>

    <!-- 随机剧本分类选择 -->
    <el-dialog
      v-model="showRandomDialog"
      title="选择剧本类型"
      width="30%"
    >
      <el-button 
        v-for="category in scriptCategories" 
        :key="category.value"
        @click="handleCategorySelect(category.value)"
      >
        {{ category.label }}
      </el-button>
    </el-dialog>

    <!-- 上传剧本选项 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传剧本"
      width="30%"
    >
      <el-button @click="showTextInput">直接输入文字</el-button>
      <el-button @click="showFileUpload">上传文件</el-button>
    </el-dialog>

    <!-- 文本输入对话框 -->
    <el-dialog
      v-model="showTextInputDialog"
      title="输入剧本内容"
      width="50%"
    >
      <el-input
        type="textarea"
        v-model="scriptContent"
        :rows="10"
        placeholder="请输入剧本内容（最多3000字）"
      />
      <template #footer>
        <el-button @click="showTextInputDialog = false">返回</el-button>
        <el-button type="primary" @click="submitScript">确认</el-button>
      </template>
    </el-dialog>

    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="showFileUploadDialog"
      title="上传剧本文件"
      width="50%"
    >
      <el-upload
        class="upload-demo"
        drag
        action="/api/scripts/upload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .txt, .doc, .docx 格式的文件
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const isAllAI = ref(false)
const isAllHuman = ref(false)
const aiCount = ref(0)
const showRandomDialog = ref(false)
const showUploadDialog = ref(false)
const showTextInputDialog = ref(false)
const scriptContent = ref('')
const showFileUploadDialog = ref(false)

const scriptCategories = [
  { label: '古风类', value: 'ancient' },
  { label: '都市类', value: 'urban' },
  { label: '灵异类', value: 'supernatural' },
  { label: '二次元类', value: 'anime' },
  { label: '搞笑类', value: 'comedy' },
  { label: '解密类', value: 'mystery' },
  { label: '失恋了随便玩玩类', value: 'casual' }
]

const showRandomScripts = () => {
  showRandomDialog.value = true
}

const showUploadScript = () => {
  showUploadDialog.value = true
}

const showDecryptScript = () => {
  // TODO: 实现解密剧本功能
}

const handleCategorySelect = async (category) => {
  showRandomDialog.value = false
  try {
    const response = await axios.post('/api/scripts/generate', {
      category: category,
      count: 5
    })
    if (response.data && response.data.length > 0) {
      router.push({
        path: '/scripts',
        query: {
          category: category
        }
      })
    }
  } catch (error) {
    console.error('生成剧本失败:', error)
    ElMessage.error('生成剧本失败，请稍后重试')
  }
}

const showTextInput = () => {
  showUploadDialog.value = false
  showTextInputDialog.value = true
}

const showFileUpload = () => {
  showUploadDialog.value = false
  showFileUploadDialog.value = true
}

const beforeUpload = (file) => {
  const isText = file.type === 'text/plain'
  const isDoc = file.type === 'application/msword' || 
                file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  
  if (!isText && !isDoc) {
    ElMessage.error('只能上传文本文件或Word文档！')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  ElMessage.success('上传成功')
  showFileUploadDialog.value = false
  router.push('/scripts')
}

const handleUploadError = () => {
  ElMessage.error('上传失败，请重试')
}

const submitScript = async () => {
  if (scriptContent.value.length > 3000) {
    ElMessage.error('剧本内容不能超过3000字')
    return
  }
  // TODO: 调用后端API上传剧本
  showTextInputDialog.value = false
  router.push('/game')
}
</script>

<style scoped>
.home {
  padding: 20px;
  text-align: center;
}

.selection-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.button-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
  gap: 20px;
}

h1 {
  color: #409EFF;
  margin-bottom: 30px;
}
</style> 