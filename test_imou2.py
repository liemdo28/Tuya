import asyncio, aiohttp, json
from imouapi.api import ImouAPIClient

async def test():
    session = aiohttp.ClientSession()
    api = ImouAPIClient('lca938b20270374441', '0d7e5b3c216d4d2383e088bc65f2a4', session)
    await api.async_connect()
    
    methods = [
        ('deviceBaseList', {'bindId':'','limit':50,'type':'bind'}),
        ('listDeviceDetailsByPage', {'pageSize':'50','currentPage':'1'}),
    ]
    
    for name, params in methods:
        try:
            result = await api._async_call_api(name, params)
            print(f'{name}: {json.dumps(result, indent=2, ensure_ascii=False)}')
        except Exception as e:
            print(f'{name}: ERROR - {e}')
        print()
    
    await session.close()

asyncio.run(test())
