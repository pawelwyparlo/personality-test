import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/test',
      name: 'test',
      component: () => import('../views/QuestionView.vue'),
    },
    {
      path: '/results',
      name: 'results',
      component: () => import('../views/ResultsView.vue'),
    },
  ],
});

export default router;
