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