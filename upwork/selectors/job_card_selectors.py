class JobCardSelectors:

    CARD_CONTAINER = ('section', {'class': 'card-list-container'})
    JOB_CARD = ('article', {})
    TITLE = ('a', {})
    JOB_INFO = ('ul', {'class': 'job-tile-info-list'})
    DESCRIPTION = ('p', {})
    KEYWORDS = ('div', {'class': 'air3-token-container'})
    JOB_TYPE = ('li', {'data-test': 'job-type-label'})
    EXPERIENCE = ('li', {'data-test': 'experience-level'})
    BUDGET = ('li', {'data-test': 'is-fixed-price'})
    DURATION = ('li', {'data-test': 'duration-label'})
