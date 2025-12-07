# 2020-2025 ElenaBerry
import logging
import httpx

log = logging.getLogger(__name__)

class Client:
    def __init__(self, url, timeout=5, **kwargs):
        self.timeout = timeout
        self.kwargs = kwargs
        self.url = url

    def post(self, json):
        try:
            with httpx.Client() as client:
                client.post(url=self.url, json=dict(json), timeout=self.timeout, **self.kwargs)
        except httpx._exceptions.WriteError:
            log.error(f'{self.url} Write Error')
        except httpx._exceptions.ConnectTimeout:
            log.error(f'{self.url} Connect Timeout')
        except httpx._exceptions.ReadTimeout:
            log.error(f'{self.url} Read Timeout')
        except Exception as exc:
            log.exception(exc)

    def get(self):
        try:
            with httpx.Client() as client:
                r = client.get(url=self.url, timeout=self.timeout, **self.kwargs)
            return r
        except httpx._exceptions.ConnectTimeout:
            log.error(f'{self.url} Connect Timeout')
        except httpx._exceptions.ReadTimeout:
            log.error(f'{self.url} Read Timeout')
        except Exception as exc:
            log.exception(exc)
        return None

    async def async_post(self, json):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url=self.url, json=dict(json), timeout=self.timeout, **self.kwargs)
        except httpx._exceptions.WriteError:
            log.error(f'{self.url} Write Error')
        except httpx._exceptions.ConnectTimeout:
            log.error(f'{self.url} Connect Timeout')
        except httpx._exceptions.ReadTimeout:
            log.error(f'{self.url} Read Timeout')
        except Exception as exc:
            log.exception(exc)

    async def async_get(self):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url=self.url, timeout=self.timeout, **self.kwargs)
            return r
        except httpx._exceptions.ConnectTimeout:
            log.error(f'{self.url} Connect Timeout')
        except httpx._exceptions.ReadTimeout:
            log.error(f'{self.url} Read Timeout')
        except Exception as exc:
            log.exception(exc)
        return None


Request = Client