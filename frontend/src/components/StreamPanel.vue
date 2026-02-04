<script setup>
import { ref, onMounted, inject, computed } from 'vue';
import { useBridge } from '@/api/bridge';
import QRCode from 'qrcode';

const props = defineProps(['formData', 'liveState']);
const emit = defineEmits(['stream-start', 'stream-stop', 'update-form']);
const showModal = inject('showModal');

const { getPartitions, updateSettings, toggleLive } = useBridge();
const partitions = ref({});
const loading = ref(false);

const showVerify = ref(false);
const verifyQr = ref('');

onMounted(async () => {
  partitions.value = await getPartitions();
});

const updateLocal = (key, val) => {
  emit('update-form', key, val);
};

// 单独手动更新按钮
const doManualUpdate = async (type) => {
  if (type === 'title') {
    if(!props.formData.title) return showModal('错误', '标题不能为空', 'error');
    const res = await updateSettings('title', props.formData.title);
    if (res.success) showModal('成功', '直播标题已更新', 'success');
    else showModal('失败', res.msg, 'error');
  } else if (type === 'area') {
    if(!props.formData.area || !props.formData.subArea) return showModal('错误', '请选择完整分区', 'error');
    const res = await updateSettings('area', props.formData.area, props.formData.subArea);
    if (res.success) showModal('成功', '直播分区已更新', 'success');
    else showModal('失败', res.msg, 'error');
  }
};

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const doToggle = async () => {
  loading.value = true;

  if (props.liveState.isLive) {
    const res = await toggleLive(false);
    if (res.success) {
      emit('stream-stop');
      showModal('提示', '直播已停止', 'success');
    } else {
      showModal('停止失败', res.msg, 'error');
    }
  } else {
    try {
      // 1. 自动更新分区
      // if (props.formData.area && props.formData.subArea) {
      //   const areaRes = await updateSettings('area', props.formData.area, props.formData.subArea);
      //   if (!areaRes.success) {
      //     throw new Error(`分区更新失败: ${areaRes.msg}`);
      //   }
      //   await sleep(2000); // 间隔 0.5s
      // }

      // 2. 自动更新标题
      if (props.formData.title) {
        const titleRes = await updateSettings('title', props.formData.title);
        if (!titleRes.success) {
          throw new Error(`标题更新失败: ${titleRes.msg}`);
        }
        await sleep(200); // 间隔 0.2s
      }

      // 3. 发起开播请求
      const res = await toggleLive(true, props.formData.area, props.formData.subArea);
      if (res.success) {
        emit('stream-start', res.data);
        showModal('成功', '开播成功！推流码已生成', 'success');
      } else if (res.needFaceVerify) {
        verifyQr.value = await QRCode.toDataURL(res.qrUrl, {width: 200, margin: 2});
        showVerify.value = true;
      } else {
        showModal('开播失败', res.msg, 'error');
      }
    } catch (e) {
      showModal('错误', e.message, 'error');
    }
  }
  loading.value = false;
};

const subPartitions = computed(() => {
  return partitions.value[props.formData.area] || [];
});
</script>

<template>
  <div class="panel fade-in">
    <div class="header-section">
      <h2 class="title">直播配置</h2>
      <p class="subtitle">设置您的直播间标题与分区</p>
    </div>

    <div class="card config-card">
      <div class="input-group">
        <label class="label">直播标题</label>
        <div class="row">
          <input
            :value="formData.title"
            @input="updateLocal('title', $event.target.value)"
            class="gemini-input"
            placeholder="输入吸引人的标题..."
          >
          <button class="btn btn-secondary action-btn" @click="doManualUpdate('title')" title="仅更新标题">
            更新
          </button>
        </div>
      </div>

      <div class="input-group" style="margin-top: 20px;">
        <label class="label">直播分区</label>
        <div class="row multi-select">
          <select :value="formData.area" @change="updateLocal('area', $event.target.value)" class="gemini-input select-box">
            <option value="" disabled>选择主分区</option>
            <option v-for="(v,k) in partitions" :key="k" :value="k">{{k}}</option>
          </select>
          <select :value="formData.subArea" @change="updateLocal('subArea', $event.target.value)" class="gemini-input select-box">
            <option value="" disabled>选择子分区</option>
            <option v-for="s in subPartitions" :key="s" :value="s">{{s}}</option>
          </select>
          <button class="btn btn-secondary action-btn" @click="doManualUpdate('area')" title="仅更新分区">
            同步
          </button>
        </div>
      </div>
    </div>

    <div class="action-section">
      <button
        class="btn start-btn"
        :class="liveState.isLive ? 'btn-stop' : 'btn-start'"
        @click="doToggle"
        :disabled="loading"
      >
        <span v-if="loading" class="loader"></span>
        <template v-else>
          <span class="icon">{{ liveState.isLive ? '⏹' : '▶' }}</span>
          {{ liveState.isLive ? '停止直播' : '开始直播' }}
        </template>
      </button>
      <p v-if="!liveState.isLive" class="hint">
        <span class="info-icon">i</span> 点击开始将自动同步标题
      </p>
    </div>
  </div>

  <!-- 人脸认证弹窗 -->
  <Teleport to="body">
    <div v-if="showVerify" class="modal-overlay" @click.self="showVerify=false">
      <div class="modal verify-modal">
        <div class="modal-header">
          <h3>需要人脸认证</h3>
          <button class="close-btn" @click="showVerify=false">×</button>
        </div>
        <div class="qr-container">
          <div class="qr-box">
            <img v-if="verifyQr" :src="verifyQr">
          </div>
          <div class="qr-overlay" v-if="!verifyQr">加载中...</div>
        </div>
        <p class="verify-tip">请使用 <strong>Bilibili App</strong> 扫码完成认证</p>
        <button class="btn btn-primary full-width" @click="showVerify=false">我已完成认证</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.panel {
  max-width: 600px;
  margin: 0 auto;
}

.header-section {
  margin-bottom: 24px;
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 4px 0;
}

.subtitle {
  font-size: 14px;
  color: var(--text-sub);
  margin: 0;
}

.config-card {
  padding: 24px;
  border: 1px solid #e0e3e7;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-sub);
  margin-left: 4px;
}

.row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.multi-select {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
}

.select-box {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23444746' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.action-btn {
  padding: 10px 16px;
  border-radius: 8px;
  white-space: nowrap;
  font-size: 13px;
}

.action-section {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.start-btn {
  width: 100%;
  max-width: 280px;
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: var(--transition);
  color: white;
  border: none;
}

.btn-start {
  background-color: #669DF6; /* 浅蓝色 */
  box-shadow: 0 4px 14px rgba(102, 157, 246, 0.3);
}

.btn-start:hover {
  background-color: #5189E0;
  transform: translateY(-1px);
}

.btn-stop {
  background-color: #F28B82; /* 浅红色/珊瑚色 */
  box-shadow: 0 4px 14px rgba(242, 139, 130, 0.3);
}

.btn-stop:hover {
  background-color: #EE675C;
  transform: translateY(-1px);
}

.icon {
  font-size: 18px;
}

.hint {
  font-size: 12px;
  color: var(--text-sub);
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-size: 10px;
  font-style: normal;
}

/* 弹窗美化 */
.verify-modal {
  width: 340px;
  padding: 0;
  overflow: hidden;
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  line-height: 1;
}

.qr-container {
  padding: 30px;
  background: #f8f9fa;
  position: relative;
}

.qr-box {
  background: white;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  margin: 0 auto;
}

.verify-tip {
  padding: 0 20px;
  margin: 20px 0;
  font-size: 14px;
  color: #444;
}

.full-width {
  width: calc(100% - 40px);
  margin: 0 20px 20px 20px;
  height: 44px;
}

.loader {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
