<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">实验室样品检测管理平台</h1>
      <nav class="nav-list">
        <RouterLink :to="DASHBOARD_ENTRY.path" class="nav-item">
          {{ DASHBOARD_ENTRY.label }}
        </RouterLink>
        <RouterLink v-for="item in MODULES" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向第三方检测实验室样品接收、任务分配、检测分析、结果复核、报告签发与标物管理的检测业务管理后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView v-slot="{ Component }">
        <KeepAlive :include="['Dashboard']">
          <component :is="Component" />
        </KeepAlive>
      </RouterView>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import { MODULES } from '@/modules'

const store = useSessionStore()

const DASHBOARD_ENTRY = { label: '运营概览', path: '/' }
</script>
