<script setup lang="ts">
import { ref } from 'vue';
import ButtonsWidget from '@/components/ButtonsWidget.vue';
import TimeBar from '@/components/TimeBar.vue';
import { Answers } from '@/enums';
import { useRouter } from 'vue-router';

interface Question {
  content: string;
  answer: Answers;
}

const questions = ref<Question[]>([
  { content: 'What is your favorite color?', answer: Answers.Default },
  { content: 'Do you prefer cats or dogs?', answer: Answers.Default },
  {
    content: 'What is your dream vacation destination?',
    answer: Answers.Default,
  },
]);

const currentQuestionIndex = ref<number>(0);
const currentAnswer = ref<Answers>(Answers.Default);
const elapsed = ref<number>(0);
const router = useRouter();

const setElapsed = (newElapsed: number) => {
  elapsed.value = newElapsed;
};

const setCurrentAnswer = (value: string) => {
  if (value == currentAnswer.value) {
    currentAnswer.value = Answers.Default;
    return;
  }
  currentAnswer.value = value as Answers;
};

const answerQuestion = (answer: Answers) => {
  if (currentQuestionIndex.value === questions.value.length - 1) {
    router.push('results');
  }

  questions.value[currentQuestionIndex.value].answer = answer;
  currentQuestionIndex.value += 1;
  currentAnswer.value = Answers.Default;
  setElapsed(0);
};

const handleTimeUp = (isTimeUp: boolean) => {
  if (isTimeUp) {
    answerQuestion(Answers.Inaccurate);
  }
};
</script>

<template>
  <div class="container">
    <TimeBar
      :elapsed="elapsed"
      :setElapsed="setElapsed"
      @time-up="handleTimeUp"
    />
    <h1>{{ questions[currentQuestionIndex].content }}</h1>
    <ButtonsWidget
      :currentAnswer="currentAnswer"
      :setCurrentAnswer="setCurrentAnswer"
    />
    <button class="primary-button" @click="answerQuestion(currentAnswer)">
      {{ currentQuestionIndex === questions.length - 1 ? 'Finish' : 'Next' }}
    </button>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  gap: 60px;
}
</style>
