<script setup>
import { ref, computed } from 'vue';

// 接收父组件传入的实时直播状态
// liveState 结构: { isLive: boolean, rtmp1: {addr, code}, rtmp2: {addr, code}, srt: {addr, code} }
const props = defineProps(['liveState']);

// 当前选中的协议标签
const activeTab = ref('rtmp1');

// 推流码显示状态
const showCode = ref(false);

// 复制状态管理 { key: boolean }
const copyStatus = ref({});

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

// 根据当前选中的标签获取对应的数据
const currentData = computed(() => {
  if (activeTab.value === 'rtmp1') return props.liveState.rtmp1;
  if (activeTab.value === 'rtmp2') return props.liveState.rtmp2;
  if (activeTab.value === 'srt') return props.liveState.srt;
  return {};
});
</script>

<template>
  <div class="panel fade-in">
    <h2>推流码</h2>

    <div v-if="liveState.isLive" class="card highlight">

      <!-- 选项卡 -->
      <div class="tabs">
        <div
          class="tab-item"
          :class="{ active: activeTab === 'rtmp1' }"
          @click="activeTab = 'rtmp1'"
        >
          RTMP-1 (默认)
        </div>
        <div
          class="tab-item"
          :class="{ active: activeTab === 'rtmp2' }"
          @click="activeTab = 'rtmp2'"
        >
          RTMP-2 (备用)
        </div>
        <div
          class="tab-item"
          :class="{ active: activeTab === 'srt' }"
          @click="activeTab = 'srt'"
        >
          SRT (低延迟)
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="tab-content">
        <div class="field-group">
          <div class="label">服务器地址</div>
          <div class="input-row">
            <input type="text" readonly :value="currentData?.addr || '无数据'" class="gemini-input readonly">
            <button class="btn btn-secondary btn-sm" @click="copyToClipboard(currentData?.addr, `${activeTab}_addr`)" :disabled="!currentData?.addr">
              <span class="btn-content">{{ copyStatus[`${activeTab}_addr`] ? '已复制' : '复制' }}</span>
            </button>
          </div>
        </div>
        <div class="field-group">
          <div class="label">推流码</div>
          <div class="input-row input-with-icon">
            <input :type="showCode ? 'text' : 'password'" readonly :value="currentData?.code || '无数据'" class="gemini-input readonly">

            <!-- 嵌入式显示/隐藏按钮 -->
            <div class="eye-icon" @click="currentData?.code && (showCode = !showCode)" :class="{ disabled: !currentData?.code }">
               <!-- 使用 SVG 图标代替 emoji -->
               <svg v-if="showCode" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
               <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
            </div>

            <button class="btn btn-secondary btn-sm" @click="copyToClipboard(currentData?.code, `${activeTab}_code`)" :disabled="!currentData?.code">
              <span class="btn-content">{{ copyStatus[`${activeTab}_code`] ? '已复制' : '复制' }}</span>
            </button>
          </div>
        </div>
      </div>

    </div>

    <div v-else class="card" style="text-align:center;color:#888;padding:40px;">
      暂未开始直播
    </div>
  </div>
</template>

<style scoped>
.highlight { background: #E8F0FE; border: none; padding: 0; overflow: hidden; }

/* 选项卡样式 */
.tabs {
  display: flex;
  background: rgba(0,0,0,0.03);
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 0;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-item:hover {
  background: rgba(0,0,0,0.02);
  color: #333;
}

.tab-item.active {
  color: #0B57D0;
  font-weight: 600;
  border-bottom-color: #0B57D0;
}

/* 内容区域样式 */
.tab-content {
  padding: 20px;
}

.field-group { margin-bottom: 16px; }
.field-group:last-child { margin-bottom: 0; }
.label { font-size: 12px; color: #555; margin-bottom: 6px; font-weight: 500; }

.input-row { display: flex; gap: 8px; align-items: center; position: relative; }
.gemini-input.readonly {
  background: white;
  color: #555;
  border: 1px solid #d0d7de;
  cursor: text;
  font-family: monospace;
  flex: 1;
  font-size: 12px;
  padding-right: 32px; /* 为图标留出空间 */
}

/* 嵌入式图标样式 */
.input-with-icon {
  position: relative;
}

.eye-icon {
  position: absolute;
  right: 90px; /* 调整位置，在复制按钮左侧 */
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #888;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  z-index: 2;
}

.eye-icon:hover {
  color: #333;
}

.eye-icon.disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-sm {
  padding: 0 12px;
  height: 34px;
  min-width: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-content {
  white-space: nowrap;
}
</style>
