<script setup>
import { ref, watch, nextTick } from 'vue';
import { useBridge } from '@/api/bridge';

// 接收父组件传入的实时直播状态
defineProps(['liveState']);
const { state } = useBridge();

const logsContainer = ref(null);

// 监听日志变化，自动滚动到底部
watch(() => state.logs.length, () => {
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTop = logsContainer.value.scrollHeight;
    }
  });
});
</script>

<template>
  <div class="panel fade-in">
    <h2>控制台</h2>

    <div class="logs" ref="logsContainer">
      <div v-for="(l,i) in state.logs" :key="i" class="log-item">{{ l }}</div>
    </div>
  </div>
</template>

<style scoped>
.logs {
  background: #1E1E1E; color: #81C995;
  padding: 15px; border-radius: 12px;
  height: 100%; overflow-y: auto;
  font-family: monospace; font-size: 12px;
  margin-top: 20px;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.2);
}

.log-item {
  margin-bottom: 4px;
  line-height: 1.4;
  border-left: 2px solid transparent;
  padding-left: 8px;
  word-break: break-all; /* 防止长日志撑开容器 */
}
.log-item:hover {
  background: rgba(255,255,255,0.05);
  border-left-color: #81C995;
}
</style>
