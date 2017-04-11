import asyncio
import hashlib
import hmac
import logging
import sys

import aiohttp
from aiohttp import web

from settings import HOST, PORT, PATH, SLACK_TOKEN, GH_SECRET, MESSAGE_TEMPLATE
from settings import USERS_ASSOCIATION


async def slack_send_message(to, text):

    if not to.startswith('@') and not to.startswith('#'):
        to = '@' + to

    logger.info('sending message to {}: "{}"'.format(to, text))

    data = {
        'username': 'GH Review Request',
        'token': SLACK_TOKEN,
        'channel': to,
        'text': text,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://slack.com/api/chat.postMessage',
                                data=data) as response:

            return await response.text()


async def review_requested(data):
    pr_link = data['pull_request']['html_url']

    sender = data['sender']['login']
    sender_slack = USERS_ASSOCIATION.get(sender)

    reviewer = data['requested_reviewer']['login']
    reviewer_slack = USERS_ASSOCIATION.get(reviewer)

    if not reviewer_slack:
        logger.info('no slack username for @{}'.format(reviewer))
        return

    message = MESSAGE_TEMPLATE.format(
        sender=sender,
        sender_slack=sender_slack,
        reviewer=reviewer,
        reviewer_slack=reviewer_slack,
        pr_link=pr_link
    )

    asyncio.ensure_future(slack_send_message(
        to=reviewer_slack,
        text=message
    ))


async def gh_webhook(request):
    request_hmac = request.headers.get('X-Hub-Signature', '').split('=', 1)[-1]

    h = hmac.new(GH_SECRET, await request.read(), hashlib.sha1)

    if h.hexdigest() != request_hmac:
        logger.warning('{!r} - HMAC incorrect!'.format(
            request.headers.get('X-Hub-Signature')
        ))

        return web.Response(text='{}')

    data = await request.json()

    logger.info('new event: {}:{} ({})'.format(
        request.headers['X-Github-Event'],
        data['action'],
        request.headers['X-Github-Delivery'],
    ))

    if data.get('action') == 'review_requested':
        await review_requested(data)

    return web.Response(text='{}')

# App
app = web.Application()
app.router.add_post(PATH, gh_webhook)

# App Access Logging
access_logger = logging.getLogger('aiohttp.access')
access_logger.setLevel(logging.INFO)

access_log_handler = logging.StreamHandler(sys.stdout)
access_logger.addHandler(access_log_handler)

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

logger.addHandler(log_handler)


if __name__ == '__main__':
    web.run_app(app, host=HOST, port=PORT)
