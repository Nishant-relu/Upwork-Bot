class ClientInfoSelectors:

    LOCATION = ('li', {'data-qa': 'client-location'})
    JOB_POSTING_STATS = ('li', {'data-qa': 'client-job-posting-stats'})
    TOTAL_SPENT = ('strong', {'data-qa': 'client-spend'})
    CLIENT_HIRES = ('div', {'data-qa': 'client-hires'})
    COMPANY_PROFILE = ('li', {'data-qa': 'client-company-profile'})
    COMPANY_INDUSTRY = ('strong', {'data-qa': 'client-company-profile-industry'})
    COMPANY_SIZE = ('div', {'data-qa': 'client-company-profile-size'})
    HOURLY_RATE = ('strong', {'data-qa': 'client-hourly-rate'})
    CLIENT_HOURS = ('div', {'data-qa': 'client-hours'})
