import os
import logging
import subprocess

class Git:
    """
    Git class to handle git operations
    """
    def __init__(self, repo_path: str,branch: str) -> None:
        """
        Initialize the Git class with the repository path
        """
        self.repo_path = repo_path
        self.logger = logging.getLogger(self.__class__.__name__)

    def push(self) -> None:
        """
        Push changes to the remote repository
        """
        try:
            self.logger.info("Pushing changes to remote repository")
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
            subprocess.run(['git', 'commit', '-m', 'Update'], cwd=self.repo_path, check=True)
            subprocess.run(['git', 'push'], cwd=self.repo_path, check=True)
            self.logger.info("Changes pushed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error pushing changes: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")

    def pull(self) -> None:
        """
        Pull changes from the remote repository
        """
        try:
            self.logger.info("Pulling changes from remote repository")
            subprocess.run(['git', 'pull'], cwd=self.repo_path, check=True)
            self.logger.info("Changes pulled successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error pulling changes: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")