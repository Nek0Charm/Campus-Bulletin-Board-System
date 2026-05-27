<script setup lang="ts">
import AppHeader from '@/components/common/AppHeader.vue'
import AppFooter from '@/components/common/AppFooter.vue'
</script>

<template>
  <AppHeader />
  <router-view />
  <AppFooter />
</template>

<style>
@import '@/styles/variables.css';
</style>
