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

class BuildLogDataService {
    getBuildList(repo_uid: string) {
      return http.get(`/builds/?repo=${repo_uid}`);
    }
  
    getBuild(repo_uid: string, build_number: number) {
      return http.get(`/builds/?repo=${repo_uid}&build_number=${build_number}`);
    }
    getBuildLogLines(repo_uid: string, build_number: number, min_line_number: number) {
      return http.get(`/buildlogs/?repo=${repo_uid}&build=${build_number}&min_line=${min_line_number}`);
    }
  
  }
  
  export default new BuildLogDataService();