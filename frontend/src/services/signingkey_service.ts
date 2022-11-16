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

class SigningKeyDataService {
    getAll() {
      return http.get("/signingkeys/");
    }
  
    get(fingerprint: string) {
      return http.get(`signingkeys/${fingerprint}/`);
    }
  
    create(name: string, email: string) {

      let data = new FormData();
      data.append("name", name);
      data.append("email", email);
      
      return http.post("/signingkeys/", data);
    }
  
    update(fingerprint: string, data: any) {
      return http.put(`/signingkeys/${fingerprint}/`, data);
    }
  
    delete(fingerprint: string) {
      return http.delete(`/signingkeys/${fingerprint}/`);
    }

  }
  
  export default new SigningKeyDataService();