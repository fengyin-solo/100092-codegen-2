/**
 * 业务模块目录：左侧导航与运营概览下钻共用同一份清单，
 * key 对应后端 /api/overview 返回的模块键，也是路由路径（/{key}）。
 * 顺序即导航与看板的默认排列顺序。
 */
export interface ModuleEntry {
  key: string
  label: string
  path: string
}

export const MODULES: ModuleEntry[] = [
  { key: 'sample', label: '样品登记', path: '/sample' },
  { key: 'contract', label: '委托合同', path: '/contract' },
  { key: 'task', label: '检测任务', path: '/task' },
  { key: 'method', label: '检测方法', path: '/method' },
  { key: 'instrument', label: '仪器设备', path: '/instrument' },
  { key: 'standard', label: '标准物质', path: '/standard' },
  { key: 'result', label: '检测结果', path: '/result' },
  { key: 'report', label: '检测报告', path: '/report' },
  { key: 'boundary', label: '分包检测', path: '/boundary' },
  { key: 'abnormal', label: '不符合项', path: '/abnormal' },
  { key: 'envmonitor', label: '环境监控', path: '/envmonitor' },
  { key: 'blind', label: '盲样考核', path: '/blind' },
  { key: 'ability', label: '能力验证', path: '/ability' },
  { key: 'intermediate', label: '中间液配制', path: '/intermediate' },
  { key: 'audit', label: '内审检查', path: '/audit' },
  { key: 'certification', label: '认证认可', path: '/certification' },
  { key: 'quality', label: '质控样', path: '/quality' },
  { key: 'reagent2', label: '试剂管理', path: '/reagent2' },
  { key: 'waste', label: '实验废液', path: '/waste' },
  { key: 'opinion', label: '客户反馈', path: '/opinion' },
]
