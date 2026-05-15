import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import HomeView from '../views/HomeView.vue'
import ItemDetailView from '../views/ItemDetailView.vue'
import PublishView from '../views/PublishView.vue'
import MyItemsView from '../views/MyItemsView.vue'
import FavoritesView from '../views/FavoritesView.vue'
import OrdersView from '../views/OrdersView.vue'
import MessagesView from '../views/MessagesView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import AdminView from '../views/AdminView.vue'
import NotFoundView from '../views/NotFoundView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/items/new', name: 'item-create', component: PublishView, meta: { requiresAuth: true } },
    { path: '/items/:id/edit', name: 'item-edit', component: PublishView, meta: { requiresAuth: true } },
    { path: '/items/:id', name: 'item-detail', component: ItemDetailView },
    { path: '/me/items', name: 'my-items', component: MyItemsView, meta: { requiresAuth: true } },
    { path: '/me/favorites', name: 'favorites', component: FavoritesView, meta: { requiresAuth: true } },
    { path: '/me/orders', name: 'orders', component: OrdersView, meta: { requiresAuth: true } },
    { path: '/me/messages', name: 'messages', component: MessagesView, meta: { requiresAuth: true } },
    { path: '/me/notifications', name: 'notifications', component: NotificationsView, meta: { requiresAuth: true } },
    { path: '/admin', name: 'admin', component: AdminView, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) {
    await auth.bootstrap()
  }
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'home' }
  }
  return true
})

export default router
