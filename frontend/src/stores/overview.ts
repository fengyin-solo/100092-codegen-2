import { defineStore } from 'pinia'

import { fetchJson } from '@/api/client'

/** 概览卡片的口径标识，同时作为下钻面板的 key。 */
export type CardKey = 'modules' | 'created' | 'pending' | 'abnormal'

/** 看板支持的统计区间；与后端 RANGE_DAYS 的 key 保持一致。 */
export type RangeKey = 'today' | '7d' | '30d' | 'all'

export const RANGE_OPTIONS: { key: RangeKey; label: string }[] = [
  { key: 'today', label: '今日' },
  { key: '7d', label: '近 7 天' },
  { key: '30d', label: '近 30 天' },
  { key: 'all', label: '全部' },
]

export type OverviewCard = {
  key: CardKey
  label: string
  value: number
}

export type OverviewModule = {
  key: string
  name: string
  path: string
  total: number
  hasDateField: boolean
  /** 区间新增量；空模块或区间内无记录时为 null，页面展示「暂无」而不是 0。 */
  created: number | null
  /** 待处理量；同上，null 表示暂无数据。 */
  pending: number | null
  /** 异常量；同上，null 表示暂无数据。 */
  abnormal: number | null
  /** 最近一条记录的时间；取不到时为 null。 */
  latestTime: string | null
}

type OverviewPayload = {
  range: RangeKey
  cards: OverviewCard[]
  modules: OverviewModule[]
}

const STORAGE_KEY = 'overview-board-state'

type PersistedState = {
  range: RangeKey
  activeCard: CardKey | null
}

function restoreState(): PersistedState {
  const fallback: PersistedState = { range: '30d', activeCard: 'pending' }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return fallback
    }
    const saved = JSON.parse(raw) as Partial<PersistedState>
    const range = RANGE_OPTIONS.some((item) => item.key === saved.range)
      ? (saved.range as RangeKey)
      : fallback.range
    const activeCard =
      saved.activeCard === 'modules' ||
      saved.activeCard === 'created' ||
      saved.activeCard === 'pending' ||
      saved.activeCard === 'abnormal' ||
      saved.activeCard === null
        ? saved.activeCard
        : fallback.activeCard
    return { range, activeCard }
  } catch {
    return fallback
  }
}

export const useOverviewStore = defineStore('overview', {
  state: () => {
    const initial = restoreState()
    return {
      range: initial.range,
      activeCard: initial.activeCard as CardKey | null,
      /** 按区间缓存概览数据：切换区间即时呈现，返回看板也不会闪回默认区间。 */
      dataByRange: {} as Partial<Record<RangeKey, OverviewPayload>>,
      loading: false,
      errorMessage: '',
    }
  },
  getters: {
    payload(state): OverviewPayload | undefined {
      return state.dataByRange[state.range]
    },
    cards(state): OverviewCard[] {
      return state.dataByRange[state.range]?.cards ?? []
    },
    modules(state): OverviewModule[] {
      return state.dataByRange[state.range]?.modules ?? []
    },
  },
  actions: {
    persist() {
      const state: PersistedState = { range: this.range, activeCard: this.activeCard }
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
      } catch {
        // 浏览器禁用本地存储时退化为仅当前会话内记忆，不影响看板使用。
      }
    },
    setRange(range: RangeKey) {
      if (range === this.range) {
        return
      }
      this.range = range
      this.persist()
      void this.ensureRange()
    },
    toggleCard(key: CardKey) {
      this.activeCard = this.activeCard === key ? null : key
      this.persist()
    },
    async ensureRange(force = false) {
      if (!force && this.dataByRange[this.range]) {
        return
      }
      this.loading = true
      this.errorMessage = ''
      try {
        const payload = await fetchJson<OverviewPayload>(`/api/overview?range=${this.range}`)
        this.dataByRange[payload.range] = payload
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : '运营概览读取失败'
      } finally {
        this.loading = false
      }
    },
    /** 从模块页返回时调用：沿用已选区间刷新数字，保证卡片与模块实际数据一致。 */
    refresh() {
      return this.ensureRange(true)
    },
  },
})
