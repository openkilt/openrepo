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