from pathlib import Path


class PathConfig:
    """
    Configuration class for managing project directory paths.
    """

    def __init__(self):
        
        self.BASE_DIR = Path(__file__).parent.parent.resolve()

        # Directory Paths
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.USER_PROFILE_DIR = self.BASE_DIR / "user_profiles"
        self.DATA_DIR = self.BASE_DIR / "data"

        self.COOKIES_DIR = self.DATA_DIR / "cookies"
        self.APPLIED_JOBS_DIR = self.DATA_DIR / "applied_jobs"
        self.FAILED_JOB_DIR = self.DATA_DIR / "failed_jobs"
        self.STATS_DIR = self.DATA_DIR / "stats"
        self.SCREENSHOTS_DIR = self.DATA_DIR / "screenshots"
        self.SCRAPED_JOBS_DIR = self.DATA_DIR / "scraped_jobs"
        self.FILTERED_JOBS_DIR = self.DATA_DIR / "filtered_jobs"
        self.ATTACHMENTS_DIR = self.DATA_DIR / "attachments"

        # File path
        self.APPLIED_JOBS_FILE = self.APPLIED_JOBS_DIR / 'job_data.txt'
        self.FAILED_JOB_FILE = self.FAILED_JOB_DIR / "failed_jobs.txt"

        # Create all necessary directories and files       
        self._create_directories()
        self._create_files()

    
    def _create_directories(self) -> None:
        """
        Ensure all required directories exist.
        """
        dirs: list[Path] = [
            self.LOGS_DIR,
            self.DATA_DIR,
            self.APPLIED_JOBS_DIR,
            self.FAILED_JOB_DIR,
            self.SCREENSHOTS_DIR, 
            self.FILTERED_JOBS_DIR, 
            self.SCRAPED_JOBS_DIR,
            self.ATTACHMENTS_DIR,
            self.COOKIES_DIR,
            self.USER_PROFILE_DIR
        ]

        for dir in dirs:
            dir.mkdir(parents=True, exist_ok=True)
    
    def _create_files(self) -> None:
        """Ensure essential files exist."""
        file_paths = [
            self.APPLIED_JOBS_FILE, 
            self.FAILED_JOB_FILE
        ]

        for file_path in file_paths:
            file_path.touch(exist_ok=True)


paths:PathConfig = PathConfig()
