<template>
  <div class="user-search-bar">
    <a-row :gutter="16">
      <a-col :span="8">
        <a-input-search
          v-model:value="keyword"
          placeholder="请输入用户名或邮箱"
          enter-button
          @search="onSearch"
        />
      </a-col>
      <a-col :span="8">
        <a-select
          v-model:value="role"
          style="width: 100%"
          placeholder="请选择角色"
          @change="onRoleChange"
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="admin">admin</a-select-option>
          <a-select-option value="viewer">viewer</a-select-option>
        </a-select>
      </a-col>
      <a-col :span="8" style="text-align: right">
        <a-button type="primary" @click="onAddUser">
          <template #icon>
            <PlusOutlined />
          </template>
          新增用户
        </a-button>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const keyword = ref('')
const role = ref('')

const emit = defineEmits(['search', 'role-change', 'add-user'])

const onSearch = (value) => {
  emit('search', value)
}

const onRoleChange = (value) => {
  emit('role-change', value)
}

const onAddUser = () => {
  emit('add-user')
}
</script>

<style scoped>
.user-search-bar {
  margin-bottom: 16px;
}
</style>