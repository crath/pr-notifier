HOST = '127.0.0.1'
PORT = 5051
PATH = '/secretpath'

SLACK_TOKEN = 'xoxp-123-456-789-abcdef'
GH_SECRET = b'supersecret'  # webhook secret

MESSAGE_TEMPLATE = (
    '{sender_slack} requested PR review from {reviewer_slack}: {pr_link} '
    ':partyparrot:'
)

USERS_ASSOCIATION = {
    # GH username: SLACK username
    'python273': 'kirill'
}
