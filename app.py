import asyncio
import hashlib
import hmac

import aiohttp
from aiohttp import web

from settings import HOST, PORT, PATH, SLACK_TOKEN, GH_SECRET, MESSAGE_TEMPLATE
from settings import USERS_ASSOCIATION


async def slack_send_message(to, text):

    if not to.startswith('@') or not to.startswith('#'):
        to = '@' + to

    data = {
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
    reviewer = data['requested_reviewer']['login']

    message = MESSAGE_TEMPLATE.format(
        sender=sender,
        reviewer=reviewer,
        pr_link=pr_link
    )

    asyncio.ensure_future(slack_send_message(
        to=USERS_ASSOCIATION.get(reviewer),
        text=message
    ))


async def gh_webhook(request):
    request_hmac = request.headers.get('X-Hub-Signature', '').split('=', 1)[-1]

    h = hmac.new(GH_SECRET, await request.read(), hashlib.sha1)

    if h.hexdigest() != request_hmac:
        return web.Response(text='{}')

    data = await request.json()

    if data.get('action') == 'review_requested':
        await review_requested(data)

    return web.Response(text='{}')


app = web.Application()
app.router.add_post(PATH, gh_webhook)

if __name__ == '__main__':
    web.run_app(app, host=HOST, port=PORT)
