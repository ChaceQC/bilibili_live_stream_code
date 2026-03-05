<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, provide } from 'vue';
import QRCode from 'qrcode';
import { useBridge } from '@/api/bridge';
import Sidebar from '@/components/Sidebar.vue';
import AccountPanel from '@/components/AccountPanel.vue';
import StreamPanel from '@/components/StreamPanel.vue';
import ConsolePanel from '@/components/ConsolePanel.vue';
import DanmuPanel from '@/components/DanmuPanel.vue';
import RtmpPanel from '@/components/RtmpPanel.vue';
import MessageModal from '@/components/MessageModal.vue';
import UserAccountModal from '@/components/UserAccountModal.vue';
import WindowControls from '@/components/WindowControls.vue';

const { loadSavedConfig, getWindowPosition, windowDrag, refreshCurrentUser } = useBridge();
const activeTab = ref('account');
const isInitializing = ref(true);

// 响应式布局
const windowWidth = ref(window.innerWidth);
const isCompact = computed(() => windowWidth.value < 620);
const isSidebarOpen = ref(false);
const handleResize = () => { windowWidth.value = window.innerWidth; };

const userInfo = reactive({ isLoggedIn: false, uname: '', face: '', level: 0, uid: '', money: 0, bcoin: 0, following: 0, follower: 0, dynamic_count: 0, current_exp: 0, next_exp: 0 });
const globalForm = reactive({ roomId: '', cookie: '', csrf: '', title: '', area: '', subArea: '' });
const liveState = reactive({ isLive: false, rtmp1: {}, rtmp2: {}, srt: {} });

// 托盘人脸认证弹窗状态
const showTrayFaceVerify = ref(false);
const trayFaceVerifyQr = ref('');

const modalState = reactive({ visible: false, title: '', content: '', type: 'info' });
const showModal = (title, content, type = 'info') => { modalState.title = title; modalState.content = content; modalState.type = type; modalState.visible = true; };
provide('showModal', showModal);

const showAccountManager = ref(false);

// 刷新冷却逻辑
let lastRefreshTime = 0;
const REFRESH_COOLDOWN = 5 * 60 * 1000; // 5分钟

const tryRefreshUserInfo = async (force = false) => {
  const now = Date.now();
  if (!force && now - lastRefreshTime < REFRESH_COOLDOWN) return;

  try {
    const updatedUser = await refreshCurrentUser();
    if (updatedUser) {
      fillUserState(updatedUser);
      lastRefreshTime = now;
    }
  } catch (e) {
    console.error('Refresh failed:', e);
  }
};

// --- [终极优化] 指针捕获拖拽逻辑 ---
const initialDragState = ref({
  windowX: 0,
  windowY: 0,
  mouseX: 0,
  mouseY: 0,
});

const handlePointerDown = async (event) => {
  // 只在拖拽栏的空白处生效
  if (event.target.classList.contains('drag-bar')) {
    const initialWindowPos = await getWindowPosition();
    if (initialWindowPos) {
      initialDragState.value = {
        windowX: initialWindowPos.x,
        windowY: initialWindowPos.y,
        mouseX: event.screenX,
        mouseY: event.screenY,
      };
      // [关键] 捕获指针，让事件在鼠标移出窗口后也能继续触发
      event.target.setPointerCapture(event.pointerId);
    }
  }
};

const handlePointerMove = (event) => {
  // event.target.hasPointerCapture(event.pointerId) 检查当前元素是否正在捕获指针
  if (event.target.hasPointerCapture && event.target.hasPointerCapture(event.pointerId)) {
    const deltaX = event.screenX - initialDragState.value.mouseX;
    const deltaY = event.screenY - initialDragState.value.mouseY;
    const targetX = initialDragState.value.windowX + deltaX;
    const targetY = initialDragState.value.windowY + deltaY;
    windowDrag(targetX, targetY);
  }
};

const handlePointerUp = (event) => {
  // [关键] 释放指针捕获
  if (event.target.hasPointerCapture && event.target.hasPointerCapture(event.pointerId)) {
    event.target.releasePointerCapture(event.pointerId);
  }
};
// --- 结束 ---

onMounted(async () => {
  window.addEventListener('resize', handleResize);

  try {
    const user = await loadSavedConfig();
    if (user && user.uid) {
      fillUserState(user);
      // 启动应用时尝试更新
      await tryRefreshUserInfo();
    }
  } catch (e) { console.error(e); } finally { isInitializing.value = false; }

  // --- 注册托盘事件处理函数 ---
  window.onTrayLiveStarted = (data) => {
    liveState.isLive = true;
    if (data) {
      liveState.rtmp1 = data.rtmp1 || {};
      liveState.rtmp2 = data.rtmp2 || {};
      liveState.srt = data.srt || {};
    }
    activeTab.value = 'rtmp';
    showModal('成功', '托盘开播成功！推流码已生成', 'success');
  };

  window.onTrayNeedFaceVerify = async (qrUrl) => {
    try {
      trayFaceVerifyQr.value = await QRCode.toDataURL(qrUrl, { width: 200, margin: 2 });
    } catch (e) {
      trayFaceVerifyQr.value = '';
    }
    showTrayFaceVerify.value = true;
  };

  window.onTrayLiveStopped = () => {
    liveState.isLive = false;
    showModal('提示', '直播已通过托盘停止', 'success');
  };

  window.onTrayLiveError = (msg) => {
    showModal('托盘开播失败', msg || '未知错误', 'error');
  };
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  window.onTrayLiveStarted = null;
  window.onTrayNeedFaceVerify = null;
  window.onTrayLiveStopped = null;
  window.onTrayLiveError = null;
});

const fillUserState = (user) => {
  Object.assign(userInfo, { isLoggedIn: true, uname: user.uname, face: user.face, level: user.level, uid: user.uid, money: user.money, bcoin: user.bcoin, following: user.following, follower: user.follower, dynamic_count: user.dynamic_count, current_exp: user.current_exp, next_exp: user.next_exp });
  globalForm.roomId = user.roomId || ''; globalForm.cookie = user.cookie || ''; globalForm.csrf = user.csrf || ''; globalForm.title = user.last_title || '';
  if (user.last_area_name && Array.isArray(user.last_area_name)) { globalForm.area = user.last_area_name[0]; globalForm.subArea = user.last_area_name[1]; }
  activeTab.value = 'stream';
};

const onLoginSuccess = (data) => {
  fillUserState(data);
  lastRefreshTime = Date.now(); // 登录成功视为已刷新
};

const onSwitchAccount = (data) => {
  fillUserState(data);
  showModal('提示', `已切换: ${data.uname}`, 'success');
  lastRefreshTime = 0; // 切换账号后重置冷却，允许立即刷新一次
  tryRefreshUserInfo();
};

const onLogout = () => { Object.assign(userInfo, { isLoggedIn: false }); globalForm.roomId = ''; globalForm.cookie = ''; globalForm.csrf = ''; activeTab.value = 'account'; showModal('提示', '已退出登录', 'info'); };
const updateForm = (key, value) => { globalForm[key] = value; };

const handleTabChange = (tab) => {
  activeTab.value = tab;
  if (isCompact.value) isSidebarOpen.value = false;
};

const handleSidebarAccountClick = () => {
  showAccountManager.value = true;
  tryRefreshUserInfo();
  if (isCompact.value) isSidebarOpen.value = false;
};
</script>

<template>
  <div v-if="isInitializing" class="loading-screen"><div class="spinner"></div><p>加载中...</p></div>

  <div v-else class="app-root">
    <div
      class="drag-bar pywebview-drag-region"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
    >
      <div class="drag-bar-left">
        <button v-if="isCompact" class="menu-btn" @click.stop="isSidebarOpen = !isSidebarOpen">☰</button>
        <div class="app-title">B站直播工具</div>
      </div>
      <WindowControls />
    </div>

    <div class="app-layout">
      <!-- 侧边栏遮罩层（紧凑模式） -->
      <Transition name="fade-backdrop">
        <div v-if="isCompact && isSidebarOpen" class="sidebar-backdrop" @click="isSidebarOpen = false"></div>
      </Transition>

      <div class="sidebar-wrapper" :class="{ 'is-open': isSidebarOpen }">
        <Sidebar
          :active-tab="activeTab"
          :user="userInfo"
          @change="handleTabChange"
          @show-account-manager="handleSidebarAccountClick"
        />
      </div>
      <main class="content">
        <KeepAlive>
          <component
            :is="activeTab === 'account' ? AccountPanel : activeTab === 'stream' ? StreamPanel : activeTab === 'rtmp' ? RtmpPanel : activeTab === 'console' ? ConsolePanel : DanmuPanel"
            :current-user="userInfo"
            :form-data="globalForm"
            :live-state="liveState"
            @update-form="updateForm"
            @login-success="onLoginSuccess"
            @stream-start="(d) => {
              liveState.isLive=true;
              liveState.rtmp1=d.rtmp1;
              liveState.rtmp2=d.rtmp2;
              liveState.srt=d.srt;
              activeTab='rtmp';
            }"
            @stream-stop="() => { liveState.isLive=false; }"
          />
        </KeepAlive>
      </main>
    </div>

    <MessageModal :visible="modalState.visible" :title="modalState.title" :content="modalState.content" :type="modalState.type" @close="modalState.visible = false" />
    <UserAccountModal v-if="showAccountManager" :visible="showAccountManager" :current-user="userInfo" @close="showAccountManager = false" @switch="onSwitchAccount" @logout="onLogout" />

    <!-- 托盘触发的人脸认证弹窗 -->
    <Teleport to="body">
      <div v-if="showTrayFaceVerify" class="modal-overlay" @click.self="showTrayFaceVerify=false">
        <div class="modal tray-verify-modal">
          <div class="tray-verify-header">
            <h3>需要人脸认证</h3>
            <button class="tray-close-btn" @click="showTrayFaceVerify=false">×</button>
          </div>
          <div class="tray-qr-container">
            <div class="tray-qr-box">
              <img v-if="trayFaceVerifyQr" :src="trayFaceVerifyQr">
            </div>
            <div class="tray-qr-loading" v-if="!trayFaceVerifyQr">加载中...</div>
          </div>
          <p class="tray-verify-tip">请使用 <strong>Bilibili App</strong> 扫码完成认证</p>
          <button class="btn btn-primary tray-verify-done" @click="showTrayFaceVerify=false">我已完成认证</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
/* 根容器：Flex 纵向布局 */
.app-root { display: flex; flex-direction: column; height: 100vh; overflow: hidden; background: var(--bg-color); user-select: none; }

/* 顶部拖拽栏 */
.drag-bar {
  height: 32px; flex-shrink: 0;
  display: flex; justify-content: space-between; align-items: center;
  background: var(--surface-color);
  touch-action: none; /* 禁用触摸滚动等默认行为 */
}

.drag-bar-left {
  display: flex; align-items: center; gap: 4px;
  pointer-events: none; /* 子元素各自控制 */
}

.menu-btn {
  pointer-events: all;
  background: none; border: none; cursor: pointer;
  font-size: 16px; line-height: 1;
  padding: 4px 8px; margin-left: 4px;
  border-radius: 6px; color: var(--text-sub);
  transition: background 0.15s;
}
.menu-btn:hover { background: rgba(0,0,0,0.08); }

.app-title {
  font-size: 12px; margin-left: 8px; color: #666; font-weight: 500;
  pointer-events: none;
}

/* 主布局 */
.app-layout { display: flex; flex: 1; overflow: hidden; position: relative; }
.content { flex: 1; padding: 40px; overflow-y: auto; background: var(--bg-color); }

/* 侧边栏容器 */
.sidebar-wrapper { flex-shrink: 0; }

/* 紧凑模式遮罩 */
.sidebar-backdrop {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 199;
}

/* 遮罩淡入淡出动画 */
.fade-backdrop-enter-active, .fade-backdrop-leave-active { transition: opacity 0.2s; }
.fade-backdrop-enter-from, .fade-backdrop-leave-to { opacity: 0; }

/* 响应式：紧凑模式 */
@media (max-width: 620px) {
  .sidebar-wrapper {
    position: absolute;
    left: 0; top: 0; height: 100%;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 4px 0 20px rgba(0,0,0,0.12);
  }
  .sidebar-wrapper.is-open { transform: translateX(0); }
  .content:has(.danmu-panel) { padding: 0; }
}

/* 原有样式保持不变 */
.loading-screen { height: 100vh; width: 100vw; display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--bg-color); color: var(--text-sub); }
.spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid var(--primary-color); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* 托盘人脸认证弹窗 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.tray-verify-modal { width: 340px; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.15); }
.tray-verify-header { padding: 16px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.tray-verify-header h3 { margin: 0; font-size: 16px; color: var(--text-main); }
.tray-close-btn { background: none; border: none; font-size: 24px; color: #999; cursor: pointer; line-height: 1; }
.tray-close-btn:hover { color: #333; }
.tray-qr-container { padding: 30px; background: #f8f9fa; position: relative; display: flex; justify-content: center; }
.tray-qr-box { background: white; padding: 12px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.tray-qr-box img { display: block; }
.tray-qr-loading { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; color: #999; }
.tray-verify-tip { padding: 0 20px; margin: 20px 0; font-size: 14px; color: #444; text-align: center; }
.tray-verify-done { width: calc(100% - 40px); margin: 0 20px 20px 20px; height: 44px; }
</style>
