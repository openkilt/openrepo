import threading
import time
from repo.models import Repository
import logging
from django.conf import settings
from adapters.repo import get_repo_adapter

logger = logging.getLogger("openrepo_web")

class BackgroundWorker(threading.Thread):

    def __init__(self, chore_list):
        self.stay_alive = True
        self._chore_list = chore_list
        threading.Thread.__init__(self)

    def stop(self):
        self.stay_alive = False

    def run(self):
        logger.info(f"Starting bg worker thread {threading.current_thread().ident}")
        next_task_repo_uid = ''

        while self.stay_alive:

            try:

                next_task_repo_uid = self._chore_list.get_next_task()

                if next_task_repo_uid is not None:

                    try:
                        logger.info(f"Worker triggering update of repo {next_task_repo_uid}")

                        repo = Repository.objects.get(repo_uid=next_task_repo_uid)
                        repo.is_stale = False
                        repo.save()

                        # Perform the repo update here
                        adapter = get_repo_adapter(repo)
                        adapter.setup_repo()
                    finally:
                        self._chore_list.cleaning_done(next_task_repo_uid)

            except:
                logger.exception(f"Unhandled exception while processing repo {next_task_repo_uid}")
            time.sleep(1.0)


class ChoreList:
    '''
    Keeps track of all repos that need to be refreshed.  We need to use this rather than a simple queue because
    while a repo is being recreated, we don't want to queue up multiple refreshes.  Only one is necessary at the end.
    For example, if 20 deb files are added in succession to a repo, we would refresh after the first one is added, and while the
    repo is being refreshed, the other 19 are added, we would then do another refresh again (i.e., 2 total refreshes instead of 20)

    The threads will ask the class for the next item on the list by oldest timestamp that is not being cleaned.

    The manager will add new items to the list, but if something is already on the list, it won't modify

    When the job first starts, it will signal the repo as no longer dirty and start refreshing.
    If a new file comes in, it will flag the repo as dirty so that refresh can happen again.
     After the job is complete, the thread will notify the list to remove the entry so subsequent refreshes can be added for that repo
    '''
    def __init__(self):
        # Map will be:
        # {repo_uid: {is_being_cleaned, insert_timestamp}
        self._repo_state = {}
        self._lock = threading.Lock()

    def set_needs_clean(self, repo_uid):

        try:
            self._lock.acquire()

            if repo_uid not in self._repo_state:
                self._repo_state[repo_uid] = {'is_being_cleaned': False,
                                              'clean_time_start': -1,
                                              'insert_time': time.time()}
            else:
                # Check if this task has been set to "is_being_cleaned" for a very long time.
                # If so, remove it and allow it to be reset.)
                if self._repo_state[repo_uid]['is_being_cleaned']:
                    delta_sec = time.time() - self._repo_state[repo_uid]['clean_time_start']
                    if delta_sec > settings.REPO_CREATE_TIMEOUT_SEC:
                        logger.info(f"Timeout on repo refresh of {repo_uid} after {delta_sec} seconds.  Allowing retry")
                        del self._repo_state[repo_uid]
        finally:
            self._lock.release()


    def get_next_task(self):
        try:
            self._lock.acquire()
            sorted_list = sorted(self._repo_state.items(), key=lambda item: item[1]['insert_time'])
            for repo_uid, state in sorted_list:
                if not state['is_being_cleaned']:
                    self._repo_state[repo_uid]['is_being_cleaned'] = True
                    self._repo_state[repo_uid]['clean_time_start'] = time.time()
                    return repo_uid

            return None

        finally:
            self._lock.release()

    def cleaning_done(self, repo_uid):
        try:
            self._lock.acquire()
            del self._repo_state[repo_uid]
        finally:
            self._lock.release()
