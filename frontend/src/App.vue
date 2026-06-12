<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'

const route = useRoute()
const isAdminRoute = computed(() => route.path.startsWith('/admin'))
</script>

<template>
  <AppHeader />
  <main :class="['app-main', { 'app-main--full': isAdminRoute }]">
    <transition name="page-fade" mode="out-in">
      <router-view />
    </transition>
  </main>
  <AppFooter />
</template>

<style>
@import '@/styles/variables.css';

body {
  background: #f2f3f5;
}

.app-main {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 0 var(--spacing-md);
  box-sizing: border-box;
  background: #f2f3f5;
}

.app-main--full {
  max-width: none;
  margin: 0;
  padding: 0;
}

@media (max-width: 767px) {
  .app-main {
    padding: 0 var(--spacing-sm);
  }

  .app-main--full {
    padding: 0;
  }
}
</style>
