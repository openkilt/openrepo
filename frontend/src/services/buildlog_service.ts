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