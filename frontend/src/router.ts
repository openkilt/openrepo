/**
 * Copyright 2022 by Open Kilt LLC. All rights reserved.
 * This file is part of the OpenRepo Repository Management Software (OpenRepo)
 * OpenRepo is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License
 * version 3 as published by the Free Software Foundation
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

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
