<script setup>
import { ref, onMounted, inject } from 'vue';
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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 单独手动更新按钮（保留原有逻辑，会有成功弹窗）
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

const doToggle = async () => {
  loading.value = true;

  if (props.liveState.isLive) {
    // --- 停止直播逻辑 ---
    const res = await toggleLive(false);
    if (res.success) {
      emit('stream-stop');
      showModal('提示', '直播已停止', 'success');
    } else {
      showModal('停止失败', res.msg, 'error');
    }
  } else {
    // --- 开始直播逻辑 ---

    // 1. 自动更新标题 (如果已填写)
    if (props.formData.title) {
      const res = await updateSettings('title', props.formData.title);
      if (!res.success) {
        // 如果标题更新失败，询问是否继续，或者直接报错停止
        // 这里选择报错但不阻断（有些情况可能只是没变化），或者你可以选择 return 阻断
        console.warn("自动更新标题失败:", res.msg);
      }
    }

    // await sleep(500);
    //
    // // 2. 自动更新分区 (如果已填写)
    // if (props.formData.area && props.formData.subArea) {
    //   const res = await updateSettings('area', props.formData.area, props.formData.subArea);
    //   if (!res.success) {
    //     console.warn("自动更新分区失败:", res.msg);
    //   }
    // }

    // 3. 发起开播请求
    const res = await toggleLive(true);
    if (res.success) {
      emit('stream-start', res.data);
      showModal('成功', '开播成功！推流码已生成', 'success');
    } else if (res.needFaceVerify) {
      verifyQr.value = await QRCode.toDataURL(res.qrUrl, { width: 200, margin: 2 });
      showVerify.value = true;
    } else {
      showModal('开播失败', res.msg, 'error');
    }
  }
  loading.value = false;
};
</script>

<template>
  <div class="panel fade-in">
    <h2>直播配置</h2>
    <div class="card">
      <div class="row">
        <input :value="formData.title" @input="updateLocal('title', $event.target.value)" class="gemini-input" placeholder="直播标题">
        <button class="btn btn-secondary" @click="doManualUpdate('title')">更新</button>
      </div>
      <div class="row" style="margin-top:10px">
        <select :value="formData.area" @change="updateLocal('area', $event.target.value)" class="gemini-input">
          <option value="" disabled>选择主分区</option>
          <option v-for="(v,k) in partitions" :key="k" :value="k">{{k}}</option>
        </select>
        <select :value="formData.subArea" @change="updateLocal('subArea', $event.target.value)" class="gemini-input">
          <option value="" disabled>选择子分区</option>
          <option v-for="s in partitions[formData.area]" :key="s" :value="s">{{s}}</option>
        </select>
        <button class="btn btn-secondary" @click="doManualUpdate('area')">同步</button>
      </div>
    </div>

    <button class="btn btn-primary big" :class="{stop: liveState.isLive}" @click="doToggle" :disabled="loading">
      {{ loading ? '处理中...' : (liveState.isLive ? '⏹ 停止直播' : '▶ 开始直播') }}
    </button>
    <div v-if="!liveState.isLive" class="tip-text">点击开始将自动同步标题与分区</div>
  </div>

  <div v-if="showVerify" class="modal-overlay" @click.self="showVerify=false">
    <div class="modal">
      <h3>需要人脸认证</h3>
      <div class="qr-box"><img v-if="verifyQr" :src="verifyQr"></div>
      <p style="color:#666;font-size:14px">请使用 Bilibili App 扫码认证</p>
      <button class="btn btn-primary" @click="showVerify=false">完成认证后关闭</button>
    </div>
  </div>
</template>

<style scoped>
.row { display: flex; gap: 10px; }
.big { width: 100%; padding: 16px; font-size: 16px; margin-top: 10px; }
.stop { background-color: #D93025; }
.tip-text { margin-top: 8px; text-align: center; color: #999; font-size: 12px; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.modal { background: white; padding: 30px; border-radius: 16px; text-align: center; width: 300px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.qr-box { margin: 20px auto; width: 200px; height: 200px; background: #f5f5f5; display: flex; align-items: center; justify-content: center; }
.qr-box img { width: 100%; height: 100%; border-radius: 8px; }
</style>