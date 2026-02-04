<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useBridge } from '@/api/bridge';

const { startDanmuMonitor, stopDanmuMonitor, sendDanmu } = useBridge();
const messages = ref([]);
const messageListRef = ref(null);
const isAutoScroll = ref(true);
const inputMsg = ref('');
const sending = ref(false);

const addMessage = (data) => {
  messages.value.push(data);
  // 限制消息数量，防止内存溢出
  if (messages.value.length > 200) {
    messages.value.shift();
  }

  if (isAutoScroll.value) {
    nextTick(() => {
      if (messageListRef.value) {
        scrollToBottom();
      }
    });
  }
};

const scrollToBottom = () => {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight;
  }
};

const handleScroll = () => {
  if (!messageListRef.value) return;
  const { scrollTop, scrollHeight, clientHeight } = messageListRef.value;
  // 如果距离底部小于 50px，则认为是自动滚动状态
  isAutoScroll.value = scrollHeight - scrollTop - clientHeight < 50;
};

const handleSend = async () => {
  const msg = inputMsg.value.trim();
  if (!msg) return;

  sending.value = true;
  try {
    const res = await sendDanmu(msg);
    if (res.code === 0) {
      inputMsg.value = '';
      // 发送成功，等待弹幕服务器推送回显，或者可以在这里手动添加一条本地回显
    } else {
      // 简单的错误提示，实际项目中可以使用 Toast 组件
      console.error(res.msg);
      // 也可以添加到系统消息中显示
      addMessage({
        type: 'interact',
        uname: '系统提示',
        msg: `发送失败: ${res.msg}`
      });
    }
  } catch (e) {
    console.error(e);
    addMessage({
        type: 'interact',
        uname: '系统提示',
        msg: `发送出错: ${e}`
      });
  } finally {
    sending.value = false;
  }
};

onMounted(() => {
  // 暴露给全局，供 Python 调用
  window.onDanmuMessage = (data) => {
    addMessage(data);
  };
  startDanmuMonitor();
});

onUnmounted(() => {
  stopDanmuMonitor();
  window.onDanmuMessage = null;
});
</script>

<template>
  <div class="danmu-panel fade-in">
    <div class="danmu-header">
      <h3>弹幕监控</h3>
      <div class="controls">
        <label>
          <input type="checkbox" v-model="isAutoScroll"> 自动滚动
        </label>
      </div>
    </div>

    <div class="message-list" ref="messageListRef" @scroll="handleScroll">
      <TransitionGroup name="msg-anim">
        <div v-for="(msg, index) in messages" :key="index" class="message-row">

          <template v-if="msg.type === 'danmu'">
            <div class="avatar-col">
              <img :src="msg.face || 'https://i0.hdslb.com/bfs/face/member/noface.jpg'" alt="face" loading="lazy" referrerpolicy="no-referrer">
            </div>
            <div class="content-col">
              <div class="uname">{{ msg.uname }}</div>
              <div class="bubble-wrapper">
                <div class="bubble">
                  {{ msg.msg }}
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="msg.type === 'interact'">
             <div class="system-msg interact">
               <span class="uname">{{ msg.uname }}</span> {{ msg.msg }}
             </div>
          </template>

          <template v-else-if="msg.type === 'gift'">
            <div class="system-msg gift">
              <span class="uname">{{ msg.uname }}</span> {{ msg.action }} {{ msg.gift_name }} x {{ msg.num }}
            </div>
          </template>

          <template v-else-if="msg.type === 'system'">
            <div class="system-msg system">
              {{ msg.msg }}
            </div>
          </template>

        </div>
      </TransitionGroup>
    </div>

    <!-- 发送区域 -->
    <div class="send-area">
      <input
        type="text"
        v-model="inputMsg"
        @keyup.enter="handleSend"
        placeholder="发送弹幕..."
        :disabled="sending"
      />
      <button @click="handleSend" :disabled="sending || !inputMsg.trim()">
        {{ sending ? '...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
/* === 面板整体容器 === */
.danmu-panel {
  display: flex;
  flex-direction: column;
  height: 100%;

  /* [核心修改] 宽度 80% 并居中 */
  width: 80%;
  margin: 0 auto;

  background: #f2f2f2; /* QQ 经典的浅灰底色 */
  border-radius: 16px; /* 圆润边框 */
  overflow: hidden;
  font-family: "Microsoft YaHei", sans-serif;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.danmu-header {
  padding: 12px 18px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f9f9f9;
}

.danmu-header h3 {
  margin: 0;
  font-size: 15px;
  color: #333;
  font-weight: 600;
}

.controls {
  font-size: 12px;
  color: #666;
  user-select: none;
}
.controls input {
  vertical-align: middle;
  margin-top: -2px;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f2f2f2;
}

/* 隐藏滚动条但保留功能 */
.message-list::-webkit-scrollbar {
  width: 6px;
}
.message-list::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 3px;
}

.message-row {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  width: 100%;
}

/* === QQ 风格核心样式 === */

/* 1. 弹幕布局：Flex Row */
.message-row:has(.avatar-col) {
  flex-direction: row;
  align-items: flex-start;
}

/* 2. 头像列 */
.avatar-col {
  margin-right: 10px;
  flex-shrink: 0;
}

.avatar-col img {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: block;
  border: 1px solid rgba(0,0,0,0.05);
}

/* 3. 内容列 */
.content-col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 80%; /* 气泡最大宽度 */
}

.uname {
  font-size: 12px;
  color: #888;
  margin-bottom: 4px;
  margin-left: 2px;
  line-height: 1;
}

/* 4. 气泡 */
.bubble {
  position: relative;
  background-color: #ffffff;
  color: #111;
  padding: 9px 13px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-all;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

/* 5. 气泡的小三角 */
.bubble::before {
  content: '';
  position: absolute;
  top: 12px;
  left: -5px;
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 6px solid #ffffff;
}

/* === 系统消息样式 === */
.system-msg {
  align-self: center;
  font-size: 12px;
  padding: 3px 12px;
  border-radius: 12px;
  margin: 4px 0;
  max-width: 90%;
  text-align: center;
}

.system-msg.interact {
  color: #888;
  background: rgba(0, 0, 0, 0.03);
}

.system-msg.gift {
  color: #ff6699;
  background: rgba(255, 102, 153, 0.08);
}

.system-msg.system {
  color: #ffffff;
  background: rgba(0, 0, 0, 0.4);
}

.system-msg .uname {
  font-weight: bold;
  color: inherit;
  margin: 0 4px;
}

/* === 发送区域样式 === */
.send-area {
  padding: 12px 16px;
  background: #f9f9f9;
  border-top: 1px solid rgba(0,0,0,0.06);
  display: flex;
  gap: 10px;
  align-items: center;
}

.send-area input {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  outline: none;
  font-size: 14px;
  background: #fff;
  transition: all 0.2s;
}

.send-area input:focus {
  border-color: #00aeec;
  box-shadow: 0 0 0 2px rgba(0, 174, 236, 0.1);
}

.send-area button {
  padding: 8px 20px;
  background: #00aeec;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
  white-space: nowrap;
}

.send-area button:hover:not(:disabled) {
  background: #00a1d6;
}

.send-area button:disabled {
  background: #e0e0e0;
  color: #aaa;
  cursor: not-allowed;
}

/* === 动画效果 === */

/* 面板淡入 */
.fade-in {
  animation: panelFadeIn 0.4s ease-out;
}
@keyframes panelFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 弹幕列表动画 */
.msg-anim-enter-active {
  transition: all 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
}
.msg-anim-leave-active {
  position: absolute;
  transition: all 0.3s ease;
  opacity: 0;
}
.msg-anim-enter-from {
  opacity: 0;
  transform: translateY(15px) scale(0.95);
}
</style>