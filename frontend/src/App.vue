<script setup>
import { ref, reactive, onMounted, provide } from 'vue';
import { useBridge } from '@/api/bridge';
import Sidebar from '@/components/Sidebar.vue';
import AccountPanel from '@/components/AccountPanel.vue';
import StreamPanel from '@/components/StreamPanel.vue';
import ConsolePanel from '@/components/ConsolePanel.vue';
import MessageModal from '@/components/MessageModal.vue';
import UserAccountModal from '@/components/UserAccountModal.vue';
import WindowControls from '@/components/WindowControls.vue';

const { loadSavedConfig, getWindowPosition, windowDrag } = useBridge();
const activeTab = ref('account');
const isInitializing = ref(true);

const userInfo = reactive({ isLoggedIn: false, uname: '', face: '', level: 0, uid: '', money: 0, bcoin: 0, following: 0, follower: 0, dynamic_count: 0, current_exp: 0, next_exp: 0 });
const globalForm = reactive({ roomId: '', cookie: '', csrf: '', title: '', area: '', subArea: '' });
const liveState = reactive({ isLive: false, addr: '', code: '' });

const modalState = reactive({ visible: false, title: '', content: '', type: 'info' });
const showModal = (title, content, type = 'info') => { modalState.title = title; modalState.content = content; modalState.type = type; modalState.visible = true; };
provide('showModal', showModal);

const showAccountManager = ref(false);

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
  try {
    const user = await loadSavedConfig();
    if (user && user.uid) fillUserState(user);
  } catch (e) { console.error(e); } finally { isInitializing.value = false; }
});

const fillUserState = (user) => {
  Object.assign(userInfo, { isLoggedIn: true, uname: user.uname, face: user.face, level: user.level, uid: user.uid, money: user.money, bcoin: user.bcoin, following: user.following, follower: user.follower, dynamic_count: user.dynamic_count, current_exp: user.current_exp, next_exp: user.next_exp });
  globalForm.roomId = user.roomId || ''; globalForm.cookie = user.cookie || ''; globalForm.csrf = user.csrf || ''; globalForm.title = user.last_title || '';
  if (user.last_area_name && Array.isArray(user.last_area_name)) { globalForm.area = user.last_area_name[0]; globalForm.subArea = user.last_area_name[1]; }
  activeTab.value = 'stream';
};

const onLoginSuccess = (data) => fillUserState(data);
const onSwitchAccount = (data) => { fillUserState(data); showModal('提示', `已切换: ${data.uname}`, 'success'); };
const onLogout = () => { Object.assign(userInfo, { isLoggedIn: false }); globalForm.roomId = ''; globalForm.cookie = ''; globalForm.csrf = ''; activeTab.value = 'account'; showModal('提示', '已退出登录', 'info'); };
const updateForm = (key, value) => { globalForm[key] = value; };
</script>

<template>
  <div v-if="isInitializing" class="loading-screen"><div class="spinner"></div><p>加载中...</p></div>

  <div v-else class="app-root">
    <div
      class="drag-bar"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
    >
      <div class="app-title">B站直播工具</div>
      <WindowControls />
    </div>

    <div class="app-layout">
      <Sidebar
        :active-tab="activeTab"
        :user="userInfo"
        @change="t => activeTab = t"
        @show-account-manager="showAccountManager = true"
      />
      <main class="content">
        <KeepAlive>
          <component
            :is="activeTab === 'account' ? AccountPanel : activeTab === 'stream' ? StreamPanel : ConsolePanel"
            :current-user="userInfo"
            :form-data="globalForm"
            :live-state="liveState"
            @update-form="updateForm"
            @login-success="onLoginSuccess"
            @stream-start="(d) => { liveState.isLive=true; liveState.addr=d.addr; liveState.code=d.code; activeTab='console'; }"
            @stream-stop="() => { liveState.isLive=false; }"
          />
        </KeepAlive>
      </main>
    </div>

    <MessageModal :visible="modalState.visible" :title="modalState.title" :content="modalState.content" :type="modalState.type" @close="modalState.visible = false" />
    <UserAccountModal v-if="showAccountManager" :visible="showAccountManager" :current-user="userInfo" @close="showAccountManager = false" @switch="onSwitchAccount" @logout="onLogout" />
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

.app-title {
  font-size: 12px; margin-left: 12px; color: #666; font-weight: 500;
  pointer-events: none;
}

/* 主布局 */
.app-layout { display: flex; flex: 1; overflow: hidden; }
.content { flex: 1; padding: 40px; overflow-y: auto; background: var(--bg-color); }

/* 原有样式保持不变 */
.loading-screen { height: 100vh; width: 100vw; display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--bg-color); color: var(--text-sub); }
.spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid var(--primary-color); border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 16px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
