<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <h1>404</h1>
      <p>页面未找到</p>
      <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
  padding: var(--spacing-xl) var(--spacing-md);
}

.not-found-content {
  text-align: center;
}

.not-found-content h1 {
  font-size: 80px;
  font-weight: 800;
  color: var(--color-primary);
  line-height: 1;
  margin-bottom: var(--spacing-sm);
}

.not-found-content p {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-lg);
}
</style>
