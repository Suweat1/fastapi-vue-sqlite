<template>
  <div class="price-charts">
    <div v-if="loading" class="empty-state">正在加载价格数据...</div>
    <template v-else>
      <div class="chart-row">
        <div class="chart-card surface">
          <h4>各分类均价对比</h4>
          <v-chart :option="categoryAvgOption" autoresize class="chart-instance" />
        </div>
        <div class="chart-card surface">
          <h4>价格区间分布</h4>
          <v-chart :option="distributionOption" autoresize class="chart-instance" />
        </div>
      </div>
      <div class="chart-card surface chart-card--full">
        <h4>近 7 天发布趋势</h4>
        <v-chart :option="trendOption" autoresize class="chart-instance chart-instance--tall" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { priceStatsApi } from '../api/admin'

use([BarChart, LineChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const loading = ref(false)
const data = ref({
  category_avg: [],
  price_distribution: [],
  daily_trend: [],
})
const isDark = ref(false)

const getThemeColors = () => {
  const style = getComputedStyle(document.documentElement)
  return {
    text: style.getPropertyValue('--muted').trim() || '#86868b',
    axisLine: style.getPropertyValue('--line').trim() || 'rgba(0,0,0,0.08)',
    tooltipBg: isDark.value ? 'rgba(29,29,31,0.92)' : 'rgba(255,255,255,0.95)',
    tooltipBorder: isDark.value ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
    tooltipText: isDark.value ? '#f5f5f7' : '#1d1d1f',
  }
}

const onThemeChange = () => {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark'
}

const observer = new MutationObserver(onThemeChange)

const categoryAvgOption = computed(() => {
  const rows = data.value.category_avg
  if (!rows.length) return {}
  const c = getThemeColors()
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      formatter(params) {
        const p = params[0]
        const row = rows[p.dataIndex]
        return `${p.name}<br/>均价: ¥${row.avg_price}<br/>最低: ¥${row.min_price}<br/>最高: ¥${row.max_price}<br/>数量: ${row.count}`
      },
    },
    grid: { left: 60, right: 20, top: 16, bottom: 40 },
    xAxis: {
      type: 'category',
      data: rows.map((r) => r.name),
      axisLabel: { color: c.text, fontSize: 11 },
      axisLine: { lineStyle: { color: c.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: c.text, fontSize: 11, formatter: '¥{value}' },
      splitLine: { lineStyle: { color: c.axisLine } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.avg_price),
        barWidth: '50%',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#f97316' },
              { offset: 1, color: 'rgba(249,115,22,0.25)' },
            ],
          },
        },
      },
    ],
  }
})

const distributionOption = computed(() => {
  const rows = data.value.price_distribution
  if (!rows.length) return {}
  const c = getThemeColors()
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
      formatter(params) {
        const p = params[0]
        const row = rows[p.dataIndex]
        return `${p.name}<br/>数量: ${row.count} 件<br/>占比: ${row.percent}%`
      },
    },
    grid: { left: 60, right: 20, top: 16, bottom: 40 },
    xAxis: {
      type: 'category',
      data: rows.map((r) => r.range),
      axisLabel: { color: c.text, fontSize: 11 },
      axisLine: { lineStyle: { color: c.axisLine } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: c.text, fontSize: 11 },
      splitLine: { lineStyle: { color: c.axisLine } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: rows.map((r) => r.count),
        barWidth: '50%',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#38bdf8' },
              { offset: 1, color: 'rgba(56,189,248,0.2)' },
            ],
          },
        },
      },
    ],
  }
})

const trendOption = computed(() => {
  const rows = data.value.daily_trend
  if (!rows.length) return {}
  const c = getThemeColors()
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: c.tooltipBg,
      borderColor: c.tooltipBorder,
      textStyle: { color: c.tooltipText },
    },
    grid: { left: 50, right: 20, top: 16, bottom: 40 },
    xAxis: {
      type: 'category',
      data: rows.map((r) => r.date.slice(5)),
      axisLabel: { color: c.text, fontSize: 11 },
      axisLine: { lineStyle: { color: c.axisLine } },
      axisTick: { show: false },
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: c.text, fontSize: 11 },
      splitLine: { lineStyle: { color: c.axisLine } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'line',
        data: rows.map((r) => r.count),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#22c55e', width: 3 },
        itemStyle: { color: '#22c55e', borderWidth: 2, borderColor: isDark.value ? '#1d1d1f' : '#ffffff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34,197,94,0.35)' },
              { offset: 1, color: 'rgba(34,197,94,0.02)' },
            ],
          },
        },
      },
    ],
  }
})

const loadData = async () => {
  loading.value = true
  try {
    data.value = await priceStatsApi()
  } catch {
    data.value = { category_avg: [], price_distribution: [], daily_trend: [] }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  isDark.value = document.documentElement.getAttribute('data-theme') === 'dark'
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  loadData()
})

onBeforeUnmount(() => {
  observer.disconnect()
})

defineExpose({ loadData })
</script>

<style scoped>
.price-charts {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card {
  padding: 22px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
}

.chart-card h4 {
  margin: 0 0 14px;
  font-size: 15px;
  color: var(--text);
  font-weight: 600;
}

.chart-card--full {
  width: 100%;
}

.chart-instance {
  width: 100%;
  height: 280px;
}

.chart-instance--tall {
  height: 260px;
}

@media (max-width: 768px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}
</style>
