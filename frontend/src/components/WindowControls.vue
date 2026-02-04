<script setup>
import { ref } from 'vue';
import { useBridge } from '@/api/bridge';

const { windowControl } = useBridge();
const isMaximized = ref(false);

const handleMin = () => windowControl('min');
const handleClose = () => windowControl('close');
const handleMax = async () => {
  const state = await windowControl('max');
  isMaximized.value = state;
};
</script>

<template>
  <div class="window-controls">
    <button class="win-btn min" @click="handleMin">
      <svg width="12" height="12" viewBox="0 0 12 12"><rect x="1" y="6" width="10" height="1"></rect></svg>
    </button>
    <button class="win-btn max" @click="handleMax">
      <svg v-if="!isMaximized" width="12" height="12" viewBox="0 0 12 12"><rect x="2" y="2" width="8" height="8" stroke="currentColor" fill="none"></rect></svg>
      <svg v-else width="12" height="12" viewBox="0 0 12 12">
        <rect x="4" y="2" width="6" height="6" stroke="currentColor" fill="none"></rect>
        <path d="M2 4v6h6v-2" stroke="currentColor" fill="none"></path>
      </svg>
    </button>
    <button class="win-btn close" @click="handleClose">
      <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" stroke-width="1.2"></path></svg>
    </button>
  </div>
</template>

<style scoped>
.window-controls {
  display: flex;
  z-index: 9999;
}
.win-btn {
  width: 46px; height: 32px;
  background: transparent; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #555;
  transition: background 0.2s;
  /* [修复] 明确按钮本身不可拖拽，这是最关键的修复 */
  -webkit-app-region: no-drag;
}
.win-btn:hover { background: rgba(0,0,0,0.1); }
.win-btn.close:hover { background: #e81123; color: white; }
svg { fill: currentColor; }
</style>