<script setup>
defineProps(['visible', 'title', 'content', 'type']); // type: 'info' | 'success' | 'error'
defineEmits(['close']);
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal fade-in">
      <div class="icon" :class="type">
        {{ type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️' }}
      </div>
      <h3>{{ title }}</h3>
      <p>{{ content }}</p>
      <button class="btn btn-primary" @click="$emit('close')">确定</button>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.4); z-index: 2000;
  display: flex; align-items: center; justify-content: center;
}
.modal {
  background: white; padding: 24px; border-radius: 16px;
  text-align: center; width: 300px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}
.icon { font-size: 40px; margin-bottom: 10px; }
.modal h3 { margin: 0 0 10px 0; font-size: 18px; color: #333; }
.modal p { color: #666; margin-bottom: 20px; font-size: 14px; line-height: 1.5; }
.btn-primary { width: 100%; justify-content: center; }
</style>