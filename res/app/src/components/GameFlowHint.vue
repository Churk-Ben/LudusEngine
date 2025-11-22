<template>
  <n-card>
    <div class="flex">
      <strong>流程</strong>
      <div class="space" />
      <span class="muted">{{ step }}/{{ total }}</span>
    </div>
    <div style="margin-top:8px">{{ hint }}</div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NCard } from 'naive-ui'
const props = defineProps<{ steps: string[]; index: number }>()
const total = computed(() => props.steps.length)
const step = computed(() => props.index + 1)
const hint = computed(() => props.steps[props.index] || '')
</script>