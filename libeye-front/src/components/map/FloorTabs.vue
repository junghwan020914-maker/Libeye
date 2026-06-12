<script setup lang="ts">
defineProps<{ floors: string[]; current: string }>();
const emit = defineEmits<{ (e: 'change', floor: string): void }>();
</script>

<template>
  <div class="flex overflow-x-auto hide-scrollbar px-4 pb-2 gap-2">
    <button v-for="floor in floors" :key="floor"
            @click="emit('change', floor)"
            class="px-5 py-2 rounded-full text-sm font-bold transition-colors whitespace-nowrap"
            :class="current === floor ? 'bg-stone-800 text-white shadow-md' : 'bg-stone-100 text-stone-500 hover:bg-stone-200'">
      {{ floor }}
    </button>
  </div>
</template>

<style scoped>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
