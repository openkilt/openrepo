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

class PackageDataService {
    getAll(repo_uid: string) {
      return http.get(`/${repo_uid}/packages/`);
    }
  
    get(repo_uid: string, package_uid: string) {
      return http.get(`/${repo_uid}/pkg/${package_uid}/`);
    }
  
    update(repo_uid: string, package_uid: string, data: any) {
      return http.put(`/${repo_uid}/pkg/${package_uid}/`, data);
    }
  
    delete(repo_uid: string, package_uid: string) {
      return http.delete(`/${repo_uid}/pkg/${package_uid}/`);
    }
  
    copy(src_repo_uid: string, package_uid: string, dest_repo_uid: string) {

      let data = new FormData();
      data.append("dest_repo_uid", dest_repo_uid);

      return http.post(`/${src_repo_uid}/pkg/${package_uid}/copy/`, data)
    }

  }
  
  export default new PackageDataService();