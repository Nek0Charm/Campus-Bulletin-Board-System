<template>
  <div class="loading-skeleton" :class="`skeleton-${type}`">
    <template v-if="type === 'card'">
      <div v-for="i in count" :key="i" class="skeleton-card">
        <div
          class="shimmer"
          style="width: 40px; height: 40px; border-radius: 8px; margin: 0 auto 8px"
        />
        <div class="shimmer" style="width: 80px; height: 14px; margin: 0 auto 6px" />
        <div class="shimmer" style="width: 120px; height: 10px; margin: 0 auto" />
      </div>
    </template>
    <template v-else-if="type === 'list-item'">
      <div v-for="i in count" :key="i" class="skeleton-list-item">
        <div class="shimmer" style="width: 60%; height: 16px; margin-bottom: 6px" />
        <div class="shimmer" style="width: 40%; height: 10px" />
      </div>
    </template>
    <template v-else-if="type === 'detail'">
      <div class="shimmer" style="width: 70%; height: 22px; margin-bottom: 10px" />
      <div class="shimmer" style="width: 30%; height: 14px; margin-bottom: 16px" />
      <div
        class="shimmer"
        style="width: 100%; height: 12px; margin-bottom: 8px"
        v-for="i in 5"
        :key="i"
      />
      <div class="shimmer" style="width: 70%; height: 12px; margin-bottom: 8px" />
    </template>
    <template v-else-if="type === 'table-row'">
      <div v-for="i in count" :key="i" class="skeleton-table-row">
        <div class="shimmer" style="width: 24px; height: 24px; border-radius: 50%" />
        <div class="shimmer" style="width: 80px; height: 10px" />
        <div class="shimmer" style="width: 130px; height: 10px" />
        <div class="shimmer" style="width: 40px; height: 10px" />
        <div class="shimmer" style="width: 40px; height: 10px" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    type: 'card' | 'list-item' | 'detail' | 'table-row'
    count?: number
  }>(),
  {
    count: 1,
  },
)
</script>

<style scoped>
.loading-skeleton {
  padding: var(--spacing-md);
}

.skeleton-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  text-align: center;
}

.skeleton-list-item {
  padding: var(--spacing-md);
  background: var(--color-bg-card);
  border-radius: var(--radius-sm);
  margin-bottom: var(--spacing-sm);
  border: 1px solid var(--color-border-light);
}

.skeleton-table-row {
  display: flex;
  gap: var(--spacing-lg);
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
}

.shimmer {
  background: linear-gradient(
    90deg,
    var(--color-border-light) 25%,
    #f0f0f0 50%,
    var(--color-border-light) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
