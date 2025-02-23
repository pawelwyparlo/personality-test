<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const started = ref(false);
const takeTest = () => {
  started.value = true;
};

const startTest = () => {
  router.push('/test');
};
</script>

<template>
  <div class="container">
    <h1>{{ started ? 'Instructions' : 'Personality Test' }}</h1>
    <p v-if="started">
      Aliquam efficitur vitae urna vitae congue. Phasellus cursus turpis in
      vehicula eleifend. Nunc tincidunt finibus ipsum. Proin ultricies
      vestibulum eros vitae dictum. Praesent eget luctus ante. Quisque laoreet
      pretium lacus sit amet auctor. Donec vestibulum tellus odio, quis
      scelerisque diam ultrices ac. Nulla tincidunt porta ipsum a ornare.
      Vestibulum a auctor dolor, sed faucibus nunc. Ut fringilla risus quis nisi
      maximus, viverra mollis justo lacinia. Proin eget condimentum nisl. In
      feugiat massa ac faucibus fringilla. Quisque varius cursus turpis.
    </p>
    <button class="primary-button" v-if="!started" @click="takeTest">
      Take Test
    </button>
    <button class="primary-button" v-else @click="startTest">Start Test</button>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

h1 {
  font-size: 62px;
  color: white;
}

p {
  font-size: 16px;
  text-align: center;
  max-width: 50%;
}
</style>
