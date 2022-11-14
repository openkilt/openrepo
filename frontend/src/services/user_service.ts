import http from "../http_common";

class UserDataService {
    whoAmI() {
        return http.get('/whoami');
    }
  

  }
  
  export default new UserDataService();