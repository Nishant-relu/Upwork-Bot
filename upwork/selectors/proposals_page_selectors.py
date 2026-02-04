
class ProposalSelectors:
    
    ACTIVE_PROPOSALS_CARD = "div.active-proposals-card-view"
    SUBMITTED_PROPOSALS_CARD = "div.submitted-proposals-card-view"

    TABLE = ('table', {})
    PROPOSAL_ROW_TAG = ('tr', {'class': 'details-row'})
    JOB_INFO_CELL_TAG = ('td', {'data-cy': 'job-info'})
    JOB_LINK_TAG = ('a', {'class': 'up-n-link'})

    VIEWED_MARK_TAG = ('div', {'data-cy': 'proposal-views-mark'})
