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