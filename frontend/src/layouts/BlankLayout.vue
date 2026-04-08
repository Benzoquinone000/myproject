<script setup>
import { ref, provide } from 'vue'
import SettingsModal from '@/components/SettingsModal.vue'

// Add state for settings modal
const showSettingsModal = ref(false)

// Provide settings modal methods to child components
const openSettingsModal = () => {
  showSettingsModal.value = true
}

provide('settingsModal', {
  openSettingsModal
})
</script>

<template>
  <div>
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
    <SettingsModal
      v-model:visible="showSettingsModal"
      @close="() => showSettingsModal = false"
    />
  </div>
</template>
