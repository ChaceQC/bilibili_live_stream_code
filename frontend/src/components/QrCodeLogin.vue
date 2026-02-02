<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useBridge } from '@/api/bridge';
import QRCode from 'qrcode';

const emit = defineEmits(['success', 'close']);
const { getLoginQrcode, pollLoginStatus } = useBridge();

const qrImgUrl = ref('');
const qrStatusText = ref('正在获取二维码...');
const isExpired = ref(false);
let pollTimer = null;

const loadQrCode = async () => {
  if (pollTimer) clearInterval(pollTimer);
  isExpired.value = false;
  qrStatusText.value = '加载中...';

  const res = await getLoginQrcode();
  if (res && res.url) {
    qrImgUrl.value = await QRCode.toDataURL(res.url, { width: 180, margin: 2 });
    qrStatusText.value = '请使用 Bilibili App 扫码';

    pollTimer = setInterval(async () => {
      const status = await pollLoginStatus(res.qrcode_key);
      if (status.code === 0) {
        clearInterval(pollTimer);
        emit('success', status.data);
      } else if (status.code === 86090) {
        qrStatusText.value = '✅ 扫码成功，请在手机上确认';
      } else if (status.code === 86038) {
        qrStatusText.value = '⚠️ 二维码已过期';
        isExpired.value = true;
        clearInterval(pollTimer);
      }
    }, 1500);
  } else {
    qrStatusText.value = '获取失败，请检查网络';
  }
};

onMounted(loadQrCode);
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer); });
</script>

<template>
  <div class="qr-container">
    <div class="qr-box">
      <img v-if="qrImgUrl" :src="qrImgUrl" />
      <div v-if="isExpired" class="expired-mask" @click="loadQrCode">
        <span>点击刷新</span>
      </div>
    </div>
    <p class="status">{{ qrStatusText }}</p>
    <button v-if="isExpired" class="btn btn-secondary btn-sm" @click="loadQrCode">刷新二维码</button>
  </div>
</template>

<style scoped>
.qr-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }
.qr-box {
  position: relative; width: 180px; height: 180px;
  background: #f5f5f5; border-radius: 12px; overflow: hidden;
  margin-bottom: 16px;
}
.qr-box img { width: 100%; height: 100%; }
.expired-mask {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: white; font-weight: bold;
}
.status { color: #666; font-size: 14px; margin-bottom: 12px; }
.btn-sm { padding: 6px 12px; font-size: 12px; }
</style>