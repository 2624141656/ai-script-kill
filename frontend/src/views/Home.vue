<template>
  <div class="home">
    <h1>剧本杀 AI 助手</h1>
    <el-button type="primary" @click="$router.push('/login')">登录</el-button>
    <el-button @click="$router.push('/register')">注册</el-button>
  </div>
</template>

<script setup>
// 组件逻辑
</script>

<style scoped>
.home {
  text-align: center;
  padding: 20px;
}
</style> 