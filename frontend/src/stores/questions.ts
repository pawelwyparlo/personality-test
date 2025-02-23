import { ref, computed, watch } from 'vue';
import { defineStore } from 'pinia';
import { Answers } from '@/enums';

interface Question {
  content: string;
  answer: Answers;
}

export const useQuestionsStore = defineStore('questions', () => {
  const questions = ref<Question[]>([
    { content: 'What is your favorite color?', answer: Answers.Default },
    { content: 'Do you prefer cats or dogs?', answer: Answers.Default },
    {
      content: 'What is your dream vacation destination?',
      answer: Answers.Default,
    },
  ]);

  const currentQuestionIndex = ref<number>(0);

  const answerQuestion = (answer: Answers) => {
    console.log(answer, currentQuestionIndex.value);
    questions.value[currentQuestionIndex.value].answer = answer;
    currentQuestionIndex.value += 1;
  };

  return { questions, currentQuestionIndex, answerQuestion };
});
