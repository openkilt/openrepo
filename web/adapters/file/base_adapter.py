import logging

logger = logging.getLogger("openrepo_web")


class RepoFileAdapter:
    def __init__(self, filepath, original_filename):
        pass

    def get_name(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_architecture(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_version(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_description(self):
        logger.warning("This function should never be called directly, only subclasses")

    def get_builddate(self):
        logger.warning("This function should never be called directly, only subclasses")

