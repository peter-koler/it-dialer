<template>
  <a-modal
    :visible="visible"
    :title="editingUser ? '编辑用户' : '新增用户'"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      :model="formState"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      ref="formRef"
    >
      <a-form-item
        label="用户名"
        name="username"
        :rules="[
          { required: true, message: '请输入用户名' },
          { min: 3, max: 20, message: '用户名长度为3-20位' },
          { pattern: /^[a-zA-Z0-9]+$/, message: '用户名只能包含字母和数字' }
        ]"
      >
        <a-input
          v-model:value="formState.username"
          :disabled="!!editingUser"
          placeholder="请输入用户名"
        />
      </a-form-item>
      
      <a-form-item
        label="邮箱"
        name="email"
        :rules="[
          { required: true, message: '请输入邮箱' },
          { type: 'email', message: '请输入正确的邮箱格式' }
        ]"
      >
        <a-input v-model:value="formState.email" placeholder="请输入邮箱" />
      </a-form-item>
      
      <a-form-item
        label="角色"
        name="role"
        :rules="[{ required: true, message: '请选择角色' }]"
      >
        <a-select v-model:value="formState.role" placeholder="请选择角色">
          <a-select-option value="admin">管理员</a-select-option>
          <a-select-option value="viewer">查看者</a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item
        v-if="!editingUser"
        label="密码"
        name="password"
        :rules="[
          { required: true, message: '请输入密码' },
          { min: 6, max: 20, message: '密码长度为6-20位' }
        ]"
      >
        <a-input-password v-model:value="formState.password" placeholder="请输入密码" />
      </a-form-item>
      
      <a-form-item label="状态" name="status">
        <a-switch
          v-model:checked="formState.status"
          checked-children="启用"
          un-checked-children="禁用"
        />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  editingUser: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['ok', 'cancel'])

const formRef = ref()
const formState = reactive({
  username: '',
  email: '',
  role: 'viewer',
  password: '',
  status: true
})

// 监听编辑用户变化
watch(
  () => props.editingUser,
  (newVal) => {
    if (newVal) {
      formState.username = newVal.username
      formState.email = newVal.email
      formState.role = newVal.role
      formState.status = newVal.status === 1
    } else {
      // 重置表单
      formState.username = ''
      formState.email = ''
      formState.role = 'viewer'
      formState.password = ''
      formState.status = true
    }
  },
  { immediate: true }
)

const handleOk = () => {
  formRef.value
    .validate()
    .then(() => {
      const values = {
        ...formState,
        status: formState.status ? 1 : 0
      }
      emit('ok', values)
    })
    .catch((error) => {
      console.log('表单验证失败:', error)
    })
}

const handleCancel = () => {
  emit('cancel')
}
</script>