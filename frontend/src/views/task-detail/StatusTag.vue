<template>
  <a-tag v-if="status === 'success'" color="green">成功</a-tag>
  <a-tag v-else-if="status === 'failed'" color="red">失败</a-tag>
  <a-tag v-else-if="status === 'timeout'" color="orange">超时</a-tag>
  <a-tag v-else>{{ status }}</a-tag>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    required: true
  }
})
</script>