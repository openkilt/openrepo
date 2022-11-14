import { createWebHistory, createRouter } from "vue-router";
import Home from '@/views/home.vue'
import Repo from '@/views/repo.vue'
import RepoSettings from '@/views/repo_settings.vue'
import RepoStatus from '@/views/repo_status.vue'
import SigningKeys from '@/views/signing_keys.vue'
import UserInfo from '@/views/user_info.vue'

const routes = [
  {
    path: "/",
    name: "home",
    component: Home,
  },
  {
    path: "/cfg/signing_keys",
    name: "signing_keys",
    component: SigningKeys,
  },
  {
    path: "/cfg/repo/:repo_uid",
    name: "repo",
    component: Repo,
  },
  {
    path: "/cfg/repo/:repo_uid/settings/",
    name: "repo_settings",
    component: RepoSettings,
  },
  {
    path: "/cfg/repo/:repo_uid/status/",
    name: "repo_status",
    component: RepoStatus,
  },
  {
    path: "/cfg/userinfo/",
    name: "user_info",
    component: UserInfo,
  },
//   {
//     path: "/add",
//     name: "add",
//     component: () => import("./components/AddTutorial.vue"),
//   },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

//export default router;
