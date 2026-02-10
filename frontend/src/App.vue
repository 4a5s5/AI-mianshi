<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <!-- PC端侧边栏 -->
      <aside v-if="!isMobile" class="sidebar">
        <div class="logo">
          <h1>AI面试助手</h1>
        </div>
        <el-menu
          :default-active="currentRoute"
          router
          class="sidebar-menu"
        >
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-sub-menu index="practice">
            <template #title>
              <el-icon><Microphone /></el-icon>
              <span>练习中心</span>
            </template>
            <el-menu-item index="/practice/single">单题练习</el-menu-item>
            <el-menu-item index="/practice/paper">套卷练习</el-menu-item>
          </el-sub-menu>
          <el-menu-item index="/repository">
            <el-icon><Folder /></el-icon>
            <span>题库管理</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>历史记录</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 主内容区 -->
      <main class="main-content" :class="{ 'mobile': isMobile }">
        <router-view />
      </main>

      <!-- 移动端底部导航 -->
      <nav v-if="isMobile" class="mobile-tabbar">
        <router-link to="/" class="tab-item" :class="{ active: currentRoute === '/' }">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </router-link>
        <router-link to="/practice/single" class="tab-item" :class="{ active: currentRoute.startsWith('/practice') }">
          <el-icon><Microphone /></el-icon>
          <span>练习</span>
        </router-link>
        <router-link to="/repository" class="tab-item" :class="{ active: currentRoute === '/repository' }">
          <el-icon><Folder /></el-icon>
          <span>题库</span>
        </router-link>
        <router-link to="/history" class="tab-item" :class="{ active: currentRoute === '/history' }">
          <el-icon><Clock /></el-icon>
          <span>记录</span>
        </router-link>
        <router-link to="/settings" class="tab-item" :class="{ active: currentRoute === '/settings' }">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </router-link>
      </nav>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import {
  HomeFilled,
  Microphone,
  Folder,
  Clock,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const currentRoute = computed(() => route.path)

const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.sidebar {
  width: 220px;
  background-color: #fff;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 1000;
}

.logo {
  padding: 20px;
  border-bottom: 1px solid #e6e6e6;
}

.logo h1 {
  font-size: 18px;
  color: #409eff;
  margin: 0;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.main-content {
  flex: 1;
  padding: 20px;
  margin-left: 220px;
}

.main-content.mobile {
  margin-left: 0;
  padding: 15px;
  padding-bottom: 70px;
}

.mobile-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: #fff;
  border-top: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 100;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: #909399;
  font-size: 12px;
}

.tab-item .el-icon {
  font-size: 22px;
  margin-bottom: 2px;
}

.tab-item.active {
  color: #409eff;
}
</style>
