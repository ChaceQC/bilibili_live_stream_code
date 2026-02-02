<script setup>
import { ref } from 'vue';
import { useBridge } from '@/api/bridge';

// 接收父组件传入的实时直播状态
defineProps(['liveState']);
const { state } = useBridge();

// 复制状态管理 { key: boolean }
const copyStatus = ref({});

const copyToClipboard = async (text, type) => {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    // 设置成功状态
    copyStatus.value[type] = true;
    // 2秒后恢复
    setTimeout(() => {
      copyStatus.value[type] = false;
    }, 2000);
  } catch (err) {
    console.error('复制失败', err);
    alert('复制失败，请手动复制');
  }
};
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
            {{ copyStatus['addr'] ? '已复制' : '复制' }}
          </button>
        </div>
      </div>

      <div class="field-group">
        <div class="label">推流码 (Stream Key)</div>
        <div class="input-row">
          <input type="password" readonly :value="liveState.code" class="gemini-input readonly">
          <button class="btn btn-secondary btn-sm" @click="copyToClipboard(liveState.code, 'code')">
            {{ copyStatus['code'] ? '已复制' : '复制' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="card" style="text-align:center;color:#888;padding:40px;">
      暂未开始直播
    </div>

    <div class="logs">
      <div v-for="(l,i) in state.logs" :key="i">{{ l }}</div>
    </div>
  </div>
</template>

<style scoped>
.highlight { background: #E8F0FE; border: none; }
.field-group { margin-bottom: 16px; }
.field-group:last-child { margin-bottom: 0; }
.label { font-size: 12px; color: #0B57D0; margin-bottom: 6px; font-weight: 600; }

.input-row { display: flex; gap: 8px; }
.gemini-input.readonly {
  background: white;
  color: #555;
  border: 1px solid #d0d7de;
  cursor: text;
  font-family: monospace;
}

.btn-sm { padding: 8px 16px; min-width: 70px; }

.logs {
  background: #1E1E1E; color: #81C995;
  padding: 15px; border-radius: 12px;
  height: 300px; overflow-y: auto;
  font-family: monospace; font-size: 12px;
  margin-top: 20px;
}
</style>