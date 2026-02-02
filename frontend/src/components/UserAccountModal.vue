<script setup>
import { ref, onMounted } from 'vue';
import { useBridge } from '@/api/bridge';
import QrCodeLogin from '@/components/QrCodeLogin.vue';

const props = defineProps(['visible', 'currentUser']);
const emit = defineEmits(['close', 'switch', 'logout']);
const { getAccountList, switchAccount, logout } = useBridge();

const accountList = ref([]);
const currentUid = ref('');
const isAdding = ref(false); // 控制是否显示扫码界面

const loadAccounts = async () => {
  const data = await getAccountList();
  accountList.value = data.list;
  currentUid.value = data.current_uid;
};

onMounted(loadAccounts);

const handleSwitch = async (uid) => {
  if (uid === currentUid.value) return;
  const res = await switchAccount(uid);
  if (res.success) {
    emit('switch', res.data);
    emit('close');
  }
};

const handleLogout = async (uid) => {
  if(confirm('确定要移除该账户吗？')) {
    await logout(uid);
    await loadAccounts();
    if (uid === currentUid.value) {
      emit('logout');
      emit('close');
    }
  }
};

// 扫码成功回调
const onAddSuccess = (data) => {
  emit('switch', data); // 直接切换到新账号
  emit('close');
};
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal fade-in">
      <div class="header">
        <h3 v-if="!isAdding">账户管理</h3>
        <h3 v-else>
          <button class="back-btn" @click="isAdding = False">←</button>
          添加账户
        </h3>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div v-if="!isAdding" class="content-view">
        <div class="account-list">
          <div
            v-for="user in accountList"
            :key="user.uid"
            class="account-item"
            :class="{ active: user.uid === currentUid }"
            @click="handleSwitch(user.uid)"
          >
            <img :src="user.face || 'https://static.hdslb.com/images/member/noface.gif'" class="avatar" referrerpolicy="no-referrer">
            <div class="info">
              <div class="name">{{ user.uname }}</div>
              <div class="uid">UID: {{ user.uid }}</div>
            </div>
            <div class="actions">
              <span v-if="user.uid === currentUid" class="badge">当前</span>
              <button class="btn-text delete" @click.stop="handleLogout(user.uid)">退出</button>
            </div>
          </div>
        </div>
        <div class="footer">
          <button class="btn btn-secondary full" @click="isAdding = true">+ 添加新账户</button>
        </div>
      </div>

      <div v-else class="content-view qr-view">
        <QrCodeLogin @success="onAddSuccess" />
      </div>

    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1500; display: flex; align-items: center; justify-content: center; }
.modal { background: white; width: 360px; border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.header { padding: 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; }
.header h3 { margin: 0; font-size: 16px; display: flex; align-items: center; gap: 10px; }
.close-btn, .back-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #999; }
.back-btn:hover { color: #333; }

.content-view { min-height: 300px; display: flex; flex-direction: column; }
.qr-view { align-items: center; justify-content: center; padding: 20px; }

.account-list { flex: 1; overflow-y: auto; padding: 8px; max-height: 300px; }
.account-item { display: flex; align-items: center; gap: 12px; padding: 10px; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.account-item:hover { background: #f5f5f5; }
.account-item.active { background: #E8F0FE; border: 1px solid #D3E3FD; }

.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #eee; }
.info { flex: 1; overflow: hidden; }
.name { font-size: 14px; font-weight: 600; color: #333; }
.uid { font-size: 12px; color: #999; }

.actions { display: flex; align-items: center; gap: 8px; }
.badge { font-size: 10px; background: #0B57D0; color: white; padding: 2px 6px; border-radius: 4px; }
.delete { color: #D93025; font-size: 12px; }
.delete:hover { background: #FFEBEB; }

.footer { padding: 12px; border-top: 1px solid #eee; margin-top: auto; }
.full { width: 100%; }
</style>