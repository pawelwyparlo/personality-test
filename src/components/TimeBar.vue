<script setup lang="ts">
import {
  computed,
  ref,
  onUnmounted,
  defineEmits,
  defineProps,
  watch,
} from 'vue';
const props = defineProps<{
  elapsed: number;
  setElapsed: (newElapsed: number) => void;
}>();
const emit = defineEmits<{ (event: 'time-up', isTimeUp: boolean): void }>();
const duration = ref<number>(30 * 1000);

let lastTime: number;
let handle: number;

const update = () => {
  props.setElapsed(performance.now() - lastTime);

  if (props.elapsed >= duration.value) {
    cancelAnimationFrame(handle);
    emit('time-up', true);
  } else {
    handle = requestAnimationFrame(update);
  }
};

const reset = () => {
  props.setElapsed(0);
  lastTime = performance.now();
  update();
};

const progressRate = computed(() =>
  Math.min(props.elapsed / duration.value, 1)
);

watch(props, () => {
  if (props.elapsed === 0) {
    reset();
  }
});

reset();
onUnmounted(() => {
  cancelAnimationFrame(handle);
});
</script>

<template>
  <progress class="loader-container" :value="progressRate" max="1"></progress>
</template>

<style scoped>
.loader-container {
  width: 80%;
  height: 8px;
  overflow: hidden;
  appearance: none;
}

.loader-container::-webkit-progress-bar {
  background-color: #e0e0e0;
  border-radius: 5px;
}

.loader-container::-webkit-progress-value {
  background-color: #388e3c;
  border-radius: 5px;
}

.loader-container::-moz-progress-bar {
  background-color: #388e3c;
  border-radius: 5px;
}
</style>
