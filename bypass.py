import tarfile
import urllib3
import uuid
import json
import asyncio
import sys
import os
from tempfile import gettempdir

sys.path.append(os.path.os.path.join(os.getcwd(), 'dependencies'))

from pyppeteer import launch


class ByPass:
    def __init__(self, boto_session):
        self.s3 = boto_session.resource('s3')
        self.s3_client = boto_session.client('s3')

    async def _interception(self, req):
        try:
            if req.resourceType in ['image', 'font', 'other']:
                await req.abort()
            else:
                await req.continue_()
        except:
            pass

    async def setUp(self):
        args = ['--no-sandbox', '--disable-gpu', '--single-process', '--proxy-server=' + os.environ['PROXY_URL']]
        options = {'ignoreHTTPSerrors': True, 'userDataDir': gettempdir(), 'args': args, 'headless': False}

        if os.environ['DEBUG'] == 'n':
            chrome_path_targz = os.path.join(gettempdir(), 'headless_shell.tar.gz')
            chrome_path = os.path.join(gettempdir(), 'headless_shell')
            options.update({'executablePath': chrome_path, 'headless': True})

            if not isfile(chrome_path):
                self.s3.Bucket('recaptcha-spider-browser').download_file('headless_shell.tar.gz', chrome_path_targz)
                chrome = tarfile.open(chrome_path_targz)
                chrome.extractall(path=gettempdir())

        self.browser = await launch(options)
        self.page = await self.browser.newPage()

        await self.page.authenticate({'username': os.environ['PROXY_LOGIN'], 'password': os.environ['PROXY_PASSWORD']})
        await self.page.setRequestInterception(True)

        self.page.on('request', lambda req: asyncio.ensure_future(self._interception(req)))
        script = "() => {Object.defineProperty(window, 'navigator', {value: {}});}"

        await self.page.setViewport({'width': 1920, 'height': 1080})
        await self.page.evaluateOnNewDocument(script)

        return self.page

    async def run(self):
        page = self.page
        http = urllib3.PoolManager()

        for frame in page.frames:
            if 'https://www.google.com/recaptcha/api2/anchor' in frame.url:
                await frame.waitFor(2000)
                await frame.click('.recaptcha-checkbox-checkmark')
                await frame.waitFor(2000)
            if 'https://www.google.com/recaptcha/api2/bframe' in frame.url:
                await frame.waitFor(2000)
                await frame.click('.rc-button-audio')
                await frame.waitFor(3000)

                href = await frame.Jeval('.rc-audiochallenge-tdownload-link', '(e) => {return e.href;}')
                r = http.request('GET', href)
                audio_name = os.path.join(gettempdir(), 'audio.mp3')

                with open(audio_name, 'wb+') as f:
                    f.write(r.data)

                with open(audio_name, 'rb') as f:
                    headers = {'Authorization': 'Bearer ' + os.environ['WIT_API_TOKEN'], 'Content-Type': 'audio/mpeg3'}
                    r = http.request('POST', 'https://api.wit.ai/speech', body=f.read(), headers=headers)
                    response = json.loads(r.data.decode('utf-8'))

                await frame.Jeval('.rc-response-input-field', '(e) => {e.value = "' + response['_text'] + '";}')
                await frame.click('#recaptcha-verify-button')
                await frame.waitFor(2000)
                await self.page.click('#recaptcha-demo-submit')

                return audio_name

    async def print_and_screenshot(self):
        pdf_name = '{}/{}.pdf'.format(gettempdir(), uuid.uuid4().hex)
        await self.page.pdf({'path': pdf_name, 'printBackground': True})

        with open(pdf_name, 'rb') as f:
            self.s3_client.put_object(Body=f, Bucket='recaptcha-spider-test', Key=pdf_name.split('/')[-1])

        screenshot_name = '{}/{}.png'.format(gettempdir(), uuid.uuid4().hex)
        await self.page.screenshot({'path': screenshot_name, 'fullPage': True})

        with open(screenshot_name, 'rb') as f:
            self.s3_client.put_object(Body=f, Bucket='recaptcha-spider-test', Key=screenshot_name.split('/')[-1])
