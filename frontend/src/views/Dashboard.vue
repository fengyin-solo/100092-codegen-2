<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，点击卡片可下钻查看具体模块的积压情况。</p>
      </div>
      <div class="range-switch" role="group" aria-label="统计区间">
        <button
          v-for="item in RANGES"
          :key="item.key"
          type="button"
          class="range-btn"
          :class="{ active: range === item.key }"
          :aria-pressed="range === item.key"
          @click="changeRange(item.key)"
        >
          {{ item.label }}
        </button>
      </div>
    </header>

    <div class="stat-row">
      <button
        v-for="card in cards"
        :key="card.key"
        type="button"
        class="stat-card card-btn"
        :class="{ active: activeCard === card.key }"
        @click="toggleCard(card.key)"
      >
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ cardValue(card.key) }}</strong>
        <span class="card-hint">{{ activeCard === card.key ? '收起明细' : '查看模块明细' }}</span>
      </button>
    </div>

    <section v-if="activeCard" class="drill-panel">
      <header class="drill-head">
        <h3>{{ activeCardMeta?.label }} · 模块明细</h3>
        <span class="drill-sub">
          {{ activeCardMeta?.sub }}｜{{ activeRangeLabel }}｜按待处理量从高到低排列
        </span>
      </header>
      <table class="data-table">
        <thead>
          <tr>
            <th>业务模块（最近记录时间）</th>
            <th>区间新增</th>
            <th>待处理</th>
            <th>异常量</th>
            <th>模块入口</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in boardRows" :key="row.key">
            <td>
              <span class="module-name">{{ row.name }}</span>
              <span class="module-time">{{ latestText(row) }}</span>
            </td>
            <td :class="{ 'cell-empty': !row.created }">{{ row.created || '暂无' }}</td>
            <td :class="{ 'cell-empty': !row.pending }">{{ row.pending || '暂无' }}</td>
            <td :class="{ 'cell-empty': !row.abnormal, 'cell-abnormal': row.abnormal > 0 }">
              {{ row.abnormal || '暂无' }}
            </td>
            <td>
              <RouterLink class="link" :to="modulePath(row.key)">进入模块</RouterLink>
            </td>
          </tr>
          <tr v-if="!boardRows.length">
            <td colspan="5" class="empty-state">{{ boardEmptyText }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <footer class="page-foot">
      <span>卡片数字与模块明细来自同一份区间汇总，进入模块处理后返回会自动刷新</span>
      <span v-if="loading" class="drill-loading">正在刷新…</span>
      <span v-else-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'

import { fetchJson } from '@/api/client'
import { MODULES } from '@/modules'

defineOptions({ name: 'Dashboard' })

type CardKey = 'modules' | 'created' | 'pending' | 'abnormal'
type RangeKey = 'today' | '7d' | '30d' | 'all'

interface CardMeta {
  key: CardKey
  label: string
  sub: string
}

interface ModuleStat {
  key: string
  name: string
  created: number
  pending: number
  abnormal: number
  latest: string | null
  has_data: boolean
}

interface Overview {
  range: RangeKey
  cards: { key: CardKey; label: string; value: number }[]
  modules: ModuleStat[]
}

const RANGES: { key: RangeKey; label: string }[] = [
  { key: 'today', label: '今日' },
  { key: '7d', label: '近7日' },
  { key: '30d', label: '近30日' },
  { key: 'all', label: '全部' },
]

const CARD_META: CardMeta[] = [
  { key: 'modules', label: '业务模块', sub: '列出全部业务模块的积压情况' },
  { key: 'created', label: '区间新增', sub: '仅列出当前区间内有新增记录的模块' },
  { key: 'pending', label: '待处理', sub: '仅列出当前区间内存在待处理记录的模块' },
  { key: 'abnormal', label: '异常量', sub: '仅列出当前区间内存在异常记录的模块' },
]

const range = ref<RangeKey>('all')
// 默认展开“待处理”：这是看板最常看的积压视角；切换与展开状态随 KeepAlive 保留。
const activeCard = ref<CardKey | null>('pending')
const overview = ref<Overview | null>(null)
const loading = ref(false)
const errorMessage = ref('')

const cards = computed(() => {
  const remote = overview.value?.cards ?? []
  return CARD_META.map((meta) => ({
    ...meta,
    label: remote.find((item) => item.key === meta.key)?.label ?? meta.label,
  }))
})

const activeCardMeta = computed(() => CARD_META.find((item) => item.key === activeCard.value) ?? null)
const activeRangeLabel = computed(() => RANGES.find((item) => item.key === range.value)?.label ?? '')

function modulePath(key: string): string {
  return MODULES.find((item) => item.key === key)?.path ?? `/${key}`
}

function cardValue(key: CardKey): number | string {
  return overview.value?.cards.find((item) => item.key === key)?.value ?? '—'
}

function latestText(row: ModuleStat): string {
  if (row.latest) {
    return `最近记录：${row.latest}`
  }
  // 区分“整张表没有数据”和“当前区间暂时没有记录”，避免一律显示 0。
  return row.has_data ? `当前${activeRangeLabel.value}区间暂无记录` : '暂无任何记录'
}

const boardRows = computed<ModuleStat[]>(() => {
  const card = activeCard.value
  if (!card) {
    return []
  }
  const byKey = new Map((overview.value?.modules ?? []).map((item) => [item.key, item]))
  // 以共享模块目录为基准，保证看板与左侧导航的模块清单一致。
  const rows = MODULES.map((entry) => {
    const stat = byKey.get(entry.key)
    return stat ?? {
      key: entry.key,
      name: entry.label,
      created: 0,
      pending: 0,
      abnormal: 0,
      latest: null,
      has_data: false,
    }
  })
  const filtered = rows.filter((row) => {
    if (card === 'modules') {
      return true
    }
    if (card === 'created') {
      return row.created > 0
    }
    return row[card] > 0
  })
  // 排序随区间数据变化：待处理降序，其次异常量、新增量，最后按导航顺序兜底。
  const order = new Map(MODULES.map((item, index) => [item.key, index]))
  return filtered.sort((a, b) => {
    if (b.pending !== a.pending) return b.pending - a.pending
    if (b.abnormal !== a.abnormal) return b.abnormal - a.abnormal
    if (b.created !== a.created) return b.created - a.created
    return (order.get(a.key) ?? 0) - (order.get(b.key) ?? 0)
  })
})

const boardEmptyText = computed(() => {
  const label = activeCardMeta.value?.label ?? ''
  return `${activeRangeLabel.value}内没有${label}相关的模块记录`
})

function toggleCard(key: CardKey) {
  activeCard.value = activeCard.value === key ? null : key
}

async function changeRange(next: RangeKey) {
  if (next === range.value) return
  range.value = next
  await load()
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    overview.value = await fetchJson<Overview>(`/api/overview?range=${range.value}`)
  } catch (error) {
    // 保留上一次已拿到的数据；首次加载失败时卡片显示“—”而不是伪造的 0。
    errorMessage.value = error instanceof Error ? error.message : '运营概览读取失败'
  } finally {
    loading.value = false
  }
}

// KeepAlive 缓存本页：区间与展开卡片在进入模块再返回时保持不变；
// 每次激活都重新拉取，保证卡片数字与模块页处理后的数据一致。
onActivated(load)
</script>

<style scoped>
.range-switch {
  display: inline-flex;
  gap: 4px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 2px;
  background: #fff;
}
.range-btn {
  border: none;
  background: transparent;
  border-radius: 6px;
  padding: 5px 14px;
  font-size: 13px;
  cursor: pointer;
  color: var(--muted);
}
.range-btn.active {
  background: var(--brand);
  color: #fff;
}
.card-btn {
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 2px;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.card-btn:hover {
  border-color: var(--brand);
}
.card-btn.active {
  border-color: var(--brand);
  box-shadow: 0 0 0 1px var(--brand) inset;
}
.card-hint {
  font-size: 12px;
  color: var(--muted);
}
.card-btn.active .card-hint {
  color: var(--brand);
}
.drill-panel {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.drill-head h3 {
  margin: 0;
  font-size: 14px;
}
.drill-sub {
  display: block;
  color: var(--muted);
  font-size: 12px;
  margin: 2px 0 10px;
}
.module-name {
  font-weight: 600;
}
.module-time {
  display: block;
  color: var(--muted);
  font-size: 12px;
  margin-top: 2px;
}
.cell-empty {
  color: var(--muted);
}
.cell-abnormal {
  color: #b42318;
  font-weight: 600;
}
.drill-loading {
  color: var(--brand);
}
</style>
