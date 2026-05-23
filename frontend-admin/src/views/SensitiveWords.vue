<template>
  <div class="stack-grid" style="gap: 20px;">
    <section class="hero-block">
      <div class="section-heading" style="margin-bottom: 8px;">
        <div>
          <div class="hero-subtitle">敏感词库</div>
          <h1 class="hero-title" style="margin-top: 8px;">维护内容安全规则与阻断策略</h1>
        </div>
        <el-button type="primary" @click="show = true">添加词条</el-button>
      </div>
      <p class="hero-subtitle" style="max-width: 760px; line-height: 1.8;">按阻断与审计两个等级进行分类，保障消息与数据流转的合规性。</p>
    </section>

    <div class="metric-grid">
      <div class="metric-card"><div class="metric-label">词条总数</div><span class="metric-value">{{ words.length }}</span></div>
      <div class="metric-card"><div class="metric-label">阻断</div><span class="metric-value">{{ blockCount }}</span></div>
      <div class="metric-card"><div class="metric-label">审计</div><span class="metric-value">{{ auditCount }}</span></div>
      <div class="metric-card"><div class="metric-label">本周新增</div><span class="metric-value">18</span></div>
    </div>

    <div class="glass-card" style="padding: 20px;">
      <div class="soft-grid three">
        <el-card v-for="word in words" :key="word.word" shadow="never" class="word-card">
          <div class="section-heading" style="margin-bottom: 8px;">
            <div class="word-title">{{ word.word }}</div>
            <el-tag :type="word.level === 1 ? 'danger' : 'warning'" effect="light" round>
              {{ word.level === 1 ? '阻断' : '审计' }}
            </el-tag>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7;">分类：{{ word.category || '未分类' }}</div>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="show" title="添加敏感词" width="520px">
      <el-form :model="form" label-position="top">
        <el-form-item label="词条"><el-input v-model="form.word" /></el-form-item>
        <el-form-item label="级别">
          <el-select v-model="form.level" style="width: 100%;">
            <el-option :value="1" label="阻断" />
            <el-option :value="2" label="审计" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类"><el-input v-model="form.category" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="show = false">取消</el-button>
        <el-button type="primary" @click="add">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { adminApi } from '../api'

const words = ref([])
const show = ref(false)
const form = reactive({ word: '', level: 1, category: '' })

const blockCount = computed(() => words.value.filter((word) => word.level === 1).length)
const auditCount = computed(() => words.value.filter((word) => word.level === 2).length)

async function load() {
  const res = await adminApi.sensitiveWords()
  if (res.code === 0) words.value = res.data || []
}

async function add() {
  await adminApi.addSensitiveWord(form)
  ElMessage.success('已添加')
  show.value = false
  load()
}

onMounted(load)
</script>

<style scoped>
.word-card {
  border-radius: 18px;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.word-title {
  font-size: 16px;
  font-weight: 800;
}
</style>
