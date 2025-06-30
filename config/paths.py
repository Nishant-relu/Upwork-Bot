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

        self.APPLIED_JOBS_DIR = self.DATA_DIR / "applied_jobs"
        self.FAILED_JOB_DIR = self.DATA_DIR / "failed_jobs"
        self.STATS_DIR = self.DATA_DIR / "stats"
        self.SCREENSHOTS_DIR = self.DATA_DIR / "screenshots"
        self.SCRAPED_JOBS_DIR = self.DATA_DIR / "scraped_jobs"
        self.FILTERED_JOBS_DIR = self.DATA_DIR / "filtered_jobs"
        self.ATTACHMENTS_DIR = self.DATA_DIR / "attachments"

        # Create all necessary directories and files       
        self._create_directories()
    
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
            self.USER_PROFILE_DIR
        ]

        for dir in dirs:
            dir.mkdir(parents=True, exist_ok=True)


paths:PathConfig = PathConfig()
