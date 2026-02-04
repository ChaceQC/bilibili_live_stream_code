<script setup>
import { ref, watch, nextTick } from 'vue';
import { useBridge } from '@/api/bridge';

// 接收父组件传入的实时直播状态
defineProps(['liveState']);
const { state } = useBridge();

// 复制状态管理 { key: boolean }
const copyStatus = ref({});
const logsContainer = ref(null);

const copyToClipboard = async (text, type) => {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    // 设置成功状态
    copyStatus.value[type] = true;
    // 1秒后恢复 (缩短时间)
    setTimeout(() => {
      copyStatus.value[type] = false;
    }, 1000);
  } catch (err) {
    console.error('复制失败', err);
  }
};

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

    <div v-if="liveState.isLive" class="card highlight">
      <div class="field-group">
        <div class="label">服务器地址 (URL)</div>
        <div class="input-row">
          <input type="text" readonly :value="liveState.addr" class="gemini-input readonly">
          <button class="btn btn-secondary btn-sm" @click="copyToClipboard(liveState.addr, 'addr')">
            <span class="btn-content">{{ copyStatus['addr'] ? '已复制' : '复制' }}</span>
          </button>
        </div>
      </div>

      <div class="field-group">
        <div class="label">推流码 (Stream Key)</div>
        <div class="input-row">
          <input type="password" readonly :value="liveState.code" class="gemini-input readonly">
          <button class="btn btn-secondary btn-sm" @click="copyToClipboard(liveState.code, 'code')">
            <span class="btn-content">{{ copyStatus['code'] ? '已复制' : '复制' }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-else class="card" style="text-align:center;color:#888;padding:40px;">
      暂未开始直播
    </div>

    <div class="logs" ref="logsContainer">
      <div v-for="(l,i) in state.logs" :key="i" class="log-item">{{ l }}</div>
    </div>
  </div>
</template>

<style scoped>
.highlight { background: #E8F0FE; border: none; }
.field-group { margin-bottom: 16px; }
.field-group:last-child { margin-bottom: 0; }
.label { font-size: 12px; color: #0B57D0; margin-bottom: 6px; font-weight: 600; }

.input-row { display: flex; gap: 8px; align-items: center; }
.gemini-input.readonly {
  background: white;
  color: #555;
  border: 1px solid #d0d7de;
  cursor: text;
  font-family: monospace;
  flex: 1;
}

.btn-sm {
  padding: 0 12px;
  height: 38px;
  min-width: 80px; /* 固定最小宽度，防止文字切换时抖动 */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-content {
  white-space: nowrap; /* 强制不换行 */
}

.logs {
  background: #1E1E1E; color: #81C995;
  padding: 15px; border-radius: 12px;
  height: 300px; overflow-y: auto;
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
