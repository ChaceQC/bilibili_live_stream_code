<script setup>
import { computed, ref, onMounted } from 'vue';
import { useBridge } from '@/api/bridge';

const props = defineProps(['activeTab', 'user']);
const emit = defineEmits(['change', 'show-account-manager']);

const { getVersion } = useBridge();
const defaultFace = 'https://static.hdslb.com/images/member/noface.gif';
const appVersion = ref('');

const menuItems = computed(() => {
  if (props.user.isLoggedIn) {
    return ['account', 'stream', 'rtmp', 'console', 'danmu'];
  } else {
    return ['account', 'console'];
  }
});

onMounted(async () => {
  appVersion.value = await getVersion();
});
</script>

<template>
  <aside class="sidebar">
    <div class="logo">📺 B站直播工具</div>

    <nav class="nav-menu">
      <div v-for="t in menuItems" :key="t"
           class="item" :class="{active: activeTab===t}" @click="$emit('change', t)">
        {{ t==='account'?'账号': t==='stream'?'直播': t==='rtmp'?'推流码': t==='console'?'控制台':'弹幕' }}
      </div>
    </nav>

    <div v-if="user.isLoggedIn" class="user-card" @click="$emit('show-account-manager')">
      <img :src="user.face || defaultFace" class="avatar" referrerpolicy="no-referrer" />
      <div class="info">
        <div class="name" :title="user.uname">{{ user.uname }}</div>
        <div class="lv">Lv.{{ user.level || 0 }}</div>
      </div>
      <div class="indicator">⋮</div>
    </div>

    <div v-else class="user-card disabled">
      <div class="avatar-placeholder">?</div>
      <div class="info">未登录</div>
    </div>

    <div v-if="appVersion" class="version-tag">{{ appVersion }}</div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 200px;
  background: var(--surface-color);
  padding: 20px;
  display: flex;
  flex-direction: column;
  /* [修复] 改为 100% 以适应父容器高度 (减去顶部拖拽栏后的高度) */
  height: 100%;
  box-sizing: border-box;
}

.logo {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 40px;
  color: var(--primary-color);
  flex-shrink: 0; /* 防止 Logo 被压缩 */
}

/* [新增] 导航菜单样式 */
.nav-menu {
  flex: 1; /* 占据剩余空间 */
  overflow-y: auto; /* 内容过多时滚动 */
  margin-bottom: 10px;
  /* 隐藏滚动条但保留功能 */
  scrollbar-width: none;
}
.nav-menu::-webkit-scrollbar { display: none; }

.item {
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-sub);
  transition: 0.2s;
  flex-shrink: 0;
}
.item:hover { background: rgba(0,0,0,0.05); }
.item.active { background: #D3E3FD; color: #041E49; font-weight: 600; }

.user-card {
  /* margin-top: auto;  <-- nav 既然已经 flex:1 了，这里就不强制 auto 了，保留一点底部边距即可 */
  padding: 10px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  flex-shrink: 0; /* 防止用户信息被压缩 */
}
.user-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.user-card.disabled { cursor: default; opacity: 0.7; }
.user-card.disabled:hover { transform: none; box-shadow: none; }

.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #eee; }
.avatar-placeholder { width: 40px; height: 40px; border-radius: 50%; background: #eee; display: flex; align-items: center; justify-content: center; color: #999; font-weight: bold; }

.info { flex: 1; overflow: hidden; }
.name { font-weight: 600; font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lv { font-size: 12px; color: #888; }
.indicator { color: #aaa; font-size: 16px; }

.version-tag {
  text-align: center;
  font-size: 11px;
  color: #bbb;
  margin-top: 8px;
  flex-shrink: 0;
}
</style>