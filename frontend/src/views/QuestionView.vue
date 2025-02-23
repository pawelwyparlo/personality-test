<script setup lang="ts">
import { ref, reactive, watchEffect } from 'vue';
import ButtonsWidget from '@/components/ButtonsWidget.vue';
import TimeBar from '@/components/TimeBar.vue';
import { Answers } from '@/enums';
import { useRouter } from 'vue-router';
import axios from 'axios';

interface Question {
  content: string;
  answer: Answers;
}

const ANSWERS_MAP = {
  Inaccurate: 1,
  VeryInaccurate: 2,
  Neutral: 3,
  None: 3,
  Accurate: 4,
  VeryAccurate: 5,
};

const submitAnswers = () => {
  const answersPayload = questions.map((question: Question, index: number) => ({
    id: index + 1,
    value: ANSWERS_MAP[question.answer as keyof typeof ANSWERS_MAP],
  }));
  axios
    .post(
      'http://127.0.0.1:5000/ipip/results',
      {
        sex: 'Male',
        age: 20,
        answers: answersPayload,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )
    .then((results) => console.log(results))
    .catch((error) => console.error({ error }));
};

const questions = reactive<Question[]>([]);

watchEffect(() => {
  fetch('http://127.0.0.1:5000/ipip/questions')
    .then((res) => res.json())
    .then((data) => {
      data.forEach((question: string) => {
        questions.push({ content: question, answer: Answers.Default });
      });
    });
});

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
  if (currentQuestionIndex.value === questions.length - 1) {
    submitAnswers();
    router.push('results');
  }

  questions[currentQuestionIndex.value].answer = answer;
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
