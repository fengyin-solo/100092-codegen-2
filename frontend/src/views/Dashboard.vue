<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，点击卡片可下钻查看各模块积压情况。</p>
      </div>
      <div class="range-tabs" role="group" aria-label="统计区间">
        <button
          v-for="option in RANGE_OPTIONS"
          :key="option.key"
          type="button"
          class="range-tab"
          :class="{ active: store.range === option.key }"
          @click="store.setRange(option.key)"
        >
          {{ option.label }}
        </button>
      </div>
    </header>

    <div class="stat-row">
      <article
        v-for="card in store.cards"
        :key="card.key"
        class="stat-card stat-card--clickable"
        :class="{ active: store.activeCard === card.key }"
        role="button"
        tabindex="0"
        :aria-expanded="store.activeCard === card.key"
        @click="store.toggleCard(card.key)"
        @keydown.enter="store.toggleCard(card.key)"
        @keydown.space.prevent="store.toggleCard(card.key)"
      >
        <span class="stat-label">
          {{ card.label }}
          <span class="stat-hint">{{ store.activeCard === card.key ? '点击收起' : '点击下钻' }}</span>
        </span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>

    <p v-if="store.loading" class="board-note">正在更新看板数据…</p>
    <p v-if="store.errorMessage" class="error-text">{{ store.errorMessage }}</p>

    <section v-if="activePanel" class="drill-panel">
      <header class="drill-head">
        <h3>{{ activePanel.title }}</h3>
        <p class="drill-tip">{{ activePanel.tip }}</p>
      </header>
      <table class="data-table">
        <thead>
          <tr>
            <th>业务模块</th>
            <th>最近记录时间</th>
            <th>待处理量</th>
            <th>异常量</th>
            <th>进入模块</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in activePanel.rows" :key="row.key">
            <td>
              <RouterLink class="module-link" :to="row.path">{{ row.name }}</RouterLink>
              <span v-if="row.total === 0" class="tag tag-empty">暂无数据</span>
            </td>
            <td>{{ formatLatest(row) }}</td>
            <td>
              <span v-if="row.pending === null" class="muted">暂无</span>
              <span v-else>{{ row.pending }}</span>
            </td>
            <td>
              <span v-if="row.abnormal === null" class="muted">暂无</span>
              <span v-else :class="{ 'abnormal-num': row.abnormal > 0 }">{{ row.abnormal }}</span>
            </td>
            <td>
              <RouterLink class="link" :to="row.path">前往{{ row.name }} →</RouterLink>
            </td>
          </tr>
          <tr v-if="!activePanel.rows.length">
            <td colspan="5" class="empty-state">{{ activePanel.emptyText }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'

import {
  RANGE_OPTIONS,
  useOverviewStore,
  type CardKey,
  type OverviewModule,
} from '@/stores/overview'

const store = useOverviewStore()

/** 各卡片下钻的口径：决定列出哪些模块与说明文案。 */
const PANEL_RULES: Record<
  CardKey,
  { title: string; tip: string; emptyText: string; pick: (rows: OverviewModule[]) => OverviewModule[] }
> = {
  modules: {
    title: '业务模块下钻',
    tip: '全部业务模块，按待处理量从高到低排列；没有任何记录的模块标记为暂无数据。',
    emptyText: '当前没有可展示的业务模块',
    pick: (rows) => rows,
  },
  created: {
    title: '区间新增下钻',
    tip: '仅列出所选统计区间内有新增记录的模块，按待处理量从高到低排列。',
    emptyText: '所选统计区间内暂无模块产生新增记录',
    pick: (rows) => rows.filter((row) => (row.created ?? 0) > 0),
  },
  pending: {
    title: '待处理量下钻',
    tip: '仅列出存在待处理事项的模块，按待处理量从高到低排列，优先处理积压最多的模块。',
    emptyText: '所选统计区间内暂无待处理事项',
    pick: (rows) => rows.filter((row) => (row.pending ?? 0) > 0),
  },
  abnormal: {
    title: '异常量下钻',
    tip: '仅列出存在异常记录的模块，按待处理量从高到低排列，并标注异常量。',
    emptyText: '所选统计区间内暂无异常记录',
    pick: (rows) => rows.filter((row) => (row.abnormal ?? 0) > 0),
  },
}

const activePanel = computed(() => {
  const key = store.activeCard
  if (!key) {
    return null
  }
  const rule = PANEL_RULES[key]
  return {
    ...rule,
    rows: rule.pick(store.modules),
  }
})

function formatLatest(row: OverviewModule): string {
  if (row.total === 0) {
    return '暂无数据'
  }
  if (!row.hasDateField) {
    return '暂无记录时间'
  }
  return row.latestTime ?? '区间内暂无记录'
}

onMounted(() => {
  // 每次进入看板都按当前已选区间重新拉取，保证从模块页返回时数字与模块内一致；
  // 区间与展开的卡片由 store/localStorage 记忆，不会跳回默认那一组。
  void store.refresh()
})
</script>
