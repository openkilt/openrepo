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

import http from "../http_common";

class RepoDataService {
    getAll() {
      return http.get("/repos/");
    }
  
    get(repo_uid: string) {
      return http.get(`/${repo_uid}/`);
    }
  
    create(data: any) {
      return http.post("/repos/", data);
    }
  
    update(repo_uid: string, data: any) {
      return http.put(`/${repo_uid}/`, data);
    }
  
    delete(repo_uid: string) {
      return http.delete(`/${repo_uid}/`);
    }

    upload(repo_uid: string, package_file: File, overwrite: false) {

      let data = new FormData();
      data.append("package_file", package_file);
      if (overwrite)
        data.append("overwrite", 'true');

      return http.post(`/${repo_uid}/upload/`, data)
    }
  
  }
  
  export default new RepoDataService();