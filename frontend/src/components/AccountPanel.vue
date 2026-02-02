<script setup>
import { inject } from 'vue';
import QrCodeLogin from '@/components/QrCodeLogin.vue';

// 接收 App.vue 传来的完整用户信息
const props = defineProps(['currentUser']);
const emit = defineEmits(['login-success']);
const showModal = inject('showModal');

const handleLoginSuccess = (data) => {
  showModal('登录成功', `欢迎回来，${data.uname}`, 'success');
  emit('login-success', data);
};

// 工具：处理下一级经验显示
const getExpText = () => {
  const cur = props.currentUser.current_exp || 0;
  const next = props.currentUser.next_exp;
  if (next === '--' || !next) return `${cur} / --`;
  return `${cur} / ${next}`;
};

const getProgress = () => {
  const cur = props.currentUser.current_exp || 0;
  const next = props.currentUser.next_exp;
  if (typeof next !== 'number') return 100;
  return Math.min((cur / parseInt(next)) * 100, 100);
};
</script>

<template>
  <div class="panel fade-in">
    <h2>账号信息</h2>

    <div v-if="!currentUser.isLoggedIn" class="card empty-state">
      <p class="hint">请扫描二维码登录 Bilibili</p>
      <QrCodeLogin @success="handleLoginSuccess" />
    </div>

    <div v-else class="card user-dashboard">
      <div class="header-section">
        <img :src="currentUser.face" class="avatar-lg" referrerpolicy="no-referrer" />
        <div class="main-info">
          <div class="name-row">
            <span class="name">{{ currentUser.uname }}</span>
            <span class="level-tag">Lv.{{ currentUser.level }}</span>
          </div>
          <div class="uid">UID: {{ currentUser.uid }}</div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-item">
          <div class="val text-blue">{{ currentUser.money || 0 }}</div>
          <div class="label">硬币</div>
        </div>
        <div class="stat-item">
          <div class="val text-orange">{{ currentUser.bcoin || 0 }}</div>
          <div class="label">B币</div>
        </div>
        <div class="stat-item">
          <div class="val">{{ currentUser.follower || 0 }}</div>
          <div class="label">粉丝</div>
        </div>
        <div class="stat-item">
          <div class="val">{{ currentUser.following || 0 }}</div>
          <div class="label">关注</div>
        </div>
        <div class="stat-item">
          <div class="val">{{ currentUser.dynamic_count || 0 }}</div>
          <div class="label">动态</div>
        </div>
      </div>

      <div class="exp-section">
        <div class="exp-text">
          <span>当前成长</span>
          <span>{{ getExpText() }}</span>
        </div>
        <div class="progress-bar">
          <div class="fill" :style="{ width: getProgress() + '%' }"></div>
        </div>
        <div class="tips" v-if="typeof currentUser.next_exp === 'number'">
          距离升级还需 <span class="highlight">{{ currentUser.next_exp - currentUser.current_exp }}</span> 点
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 40px; }
.hint { color: #666; margin-bottom: 20px; }

.user-dashboard { padding: 30px; }
.header-section { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
.avatar-lg { width: 80px; height: 80px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.main-info { display: flex; flex-direction: column; gap: 4px; }
.name-row { display: flex; align-items: center; gap: 8px; }
.name { font-size: 20px; font-weight: bold; color: #333; }
.level-tag { background: #FB7299; color: white; font-size: 12px; padding: 1px 6px; border-radius: 4px; }
.uid { color: #999; font-size: 13px; }

.stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 30px; border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0; padding: 20px 0; }
.stat-item { text-align: center; }
.stat-item .val { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 4px; }
.stat-item .label { font-size: 12px; color: #999; }
.text-blue { color: #23ADE5 !important; }
.text-orange { color: #FFB027 !important; }

.exp-section { background: #F9F9F9; padding: 16px; border-radius: 12px; }
.exp-text { display: flex; justify-content: space-between; font-size: 12px; color: #666; margin-bottom: 8px; }
.progress-bar { height: 8px; background: #E0E0E0; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.fill { height: 100%; background: #FB7299; transition: width 0.5s ease; }
.tips { font-size: 12px; color: #999; text-align: right; }
.highlight { color: #FB7299; font-weight: bold; }
</style>