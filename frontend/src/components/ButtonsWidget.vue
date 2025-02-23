<script setup lang="ts">
import { ref, defineProps } from 'vue';
import { Answers } from '@/enums';

const props = defineProps<{
  currentAnswer: Answers;
  setCurrentAnswer: (answer: Answers) => void;
}>();

interface ButtonProps {
  text: string;
  value: string;
  color: string;
}

const buttonProps = ref<ButtonProps[]>([
  {
    text: Answers.VeryInaccurate,
    value: Answers.VeryInaccurate,
    color: '#45a049',
  },
  {
    text: Answers.Inaccurate,
    value: Answers.Inaccurate,
    color: '#66bb6a',
  },
  {
    text: Answers.Neutral,
    value: Answers.Neutral,
    color: '#81c784',
  },
  {
    text: Answers.Accurate,
    value: Answers.Accurate,
    color: '#66bb6a',
  },
  {
    text: Answers.VeryAccurate,
    value: Answers.VeryAccurate,
    color: '#45a049',
  },
]);
</script>

<template>
  <div class="buttons-container">
    <button
      v-for="item in buttonProps"
      :key="item.text"
      :style="{
        backgroundColor: item.value === currentAnswer ? 'green' : item.color,
      }"
      :value="item.value"
      class="styled-button"
      @click="props.setCurrentAnswer(item.value as Answers)"
    >
      {{ item.text }}
    </button>
  </div>
</template>

<style scoped>
.buttons-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.styled-button {
  width: 200px;
  height: 50px;
  border: none;
  cursor: pointer;
  color: white;
  font-weight: 600;
}

.styled-button:last-child {
  border-top-right-radius: 5px;
  border-bottom-right-radius: 5px;
}

.styled-button:first-child {
  border-top-left-radius: 5px;
  border-bottom-left-radius: 5px;
}

.styled-button:active {
  background-color: #2e7d32 !important;
}

.styled-button:hover {
  background-color: #388e3c !important;
}
</style>
