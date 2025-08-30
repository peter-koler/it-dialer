<template>
  <a-modal
    :open="visible"
    title="重置密码"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <a-form
      :model="formState"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      ref="formRef"
    >
      <a-form-item label="用户名">
        <a-input v-model:value="user.username" disabled />
      </a-form-item>
      
      <a-form-item
        label="新密码"
        name="password"
        :rules="[
          { required: true, message: '请输入新密码' },
          { min: 6, max: 20, message: '密码长度为6-20位' }
        ]"
      >
        <a-input-password v-model:value="formState.password" placeholder="请输入新密码" />
      </a-form-item>
      
      <a-form-item
        label="确认密码"
        name="confirmPassword"
        :rules="[
          { required: true, message: '请确认密码' },
          { validator: validateConfirmPassword }
        ]"
      >
        <a-input-password v-model:value="formState.confirmPassword" placeholder="请确认密码" />
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
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['ok', 'cancel'])

const formRef = ref()
const formState = reactive({
  password: '',
  confirmPassword: ''
})

// 监听用户变化
watch(
  () => props.user,
  () => {
    // 重置表单
    formState.password = ''
    formState.confirmPassword = ''
  },
  { immediate: true }
)

const validateConfirmPassword = (_, value) => {
  if (!value) {
    return Promise.reject('请确认密码')
  }
  if (value !== formState.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  return Promise.resolve()
}

const handleOk = () => {
  formRef.value
    .validate()
    .then(() => {
      emit('ok', formState)
    })
    .catch((error) => {
      console.log('表单验证失败:', error)
    })
}

const handleCancel = () => {
  emit('cancel')
}
</script>