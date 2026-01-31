import asyncio
import aiosmtplib

async def test():
     try:
         async with aiosmtplib.SMTP(hostname="smtp.gmail.com", port=465, use_tls=True) as client:
             await client.login("simlovely7@gmail.com", "biot hlpb gsad gxog")
             await client.sendmail("simlovely7@gmail.com", ["chrisjsmez@gmail.com"], "Testing")
     except Exception as e:
         print(e)

asyncio.run(test())