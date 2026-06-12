<template>
  <div class="stats-card">
    <span class="stats-num">{{ value }}</span>
    <span class="stats-label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  value: number | string
  label: string
}>()
</script>

<style scoped>
.stats-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-xl) var(--spacing-lg);
  text-align: center;
}

.stats-num {
  display: block;
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.stats-label {
  display: block;
  margin-top: var(--spacing-xs);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}
</style>
