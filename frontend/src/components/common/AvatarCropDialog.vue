<template>
  <el-dialog
    v-model="visible"
    title="裁切头像"
    width="480px"
    :close-on-click-modal="false"
    @closed="onClosed"
  >
    <div class="crop-container">
      <img ref="imgRef" :src="imageSrc" alt="待裁切图片" class="crop-img" />
    </div>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="exporting" @click="handleConfirm">确认裁切</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'

const props = defineProps<{
  modelValue: boolean
  imageSrc: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [blob: Blob]
}>()

const visible = ref(props.modelValue)
const imgRef = ref<HTMLImageElement | null>(null)
const exporting = ref(false)
let cropper: Cropper | null = null

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val) {
      nextTick(initCropper)
    }
  },
)

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) destroyCropper()
})

function initCropper() {
  destroyCropper()
  if (!imgRef.value) return
  cropper = new Cropper(imgRef.value, {
    aspectRatio: 1,
    viewMode: 1,
    dragMode: 'move',
    autoCropArea: 0.8,
    responsive: true,
    cropBoxResizable: true,
  })
}

function destroyCropper() {
  if (cropper) {
    cropper.destroy()
    cropper = null
  }
}

async function handleConfirm() {
  if (!cropper) return
  exporting.value = true
  try {
    const canvas = cropper.getCroppedCanvas({ width: 256, height: 256 })
    canvas.toBlob(
      (blob) => {
        if (blob) {
          emit('confirm', blob)
          visible.value = false
        }
        exporting.value = false
      },
      'image/jpeg',
      0.9,
    )
  } catch {
    exporting.value = false
  }
}

function onClosed() {
  destroyCropper()
}

onBeforeUnmount(destroyCropper)
</script>

<style scoped>
.crop-container {
  width: 100%;
  max-height: 360px;
  overflow: hidden;
}

.crop-img {
  display: block;
  max-width: 100%;
}
</style>
