<template>
  <div class="page-header-wrapper">
    <el-breadcrumb v-if="breadcrumbs && breadcrumbs.length" separator=">">
      <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index" :to="item.to">
        {{ item.label }}
      </el-breadcrumb-item>
    </el-breadcrumb>

    <div v-if="title || $slots.actions" class="title-row">
      <h1 v-if="title">{{ title }}</h1>
      <div v-if="$slots.actions" class="actions">
        <slot name="actions" />
      </div>
    </div>

    <div v-if="$slots.default" class="page-extra">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router'

defineProps<{
  title?: string
  breadcrumbs?: { label: string; to?: RouteLocationRaw }[]
}>()
</script>

<style scoped>
.page-header-wrapper {
  margin-bottom: var(--spacing-lg);
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: var(--spacing-md);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.title-row h1 {
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.page-extra {
  margin-top: var(--spacing-md);
}
</style>
