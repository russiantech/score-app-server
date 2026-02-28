netstat -ano | findstr :8001 | ForEach-Object {                                                                        
>>     taskkill /PID ($_ -split '\s+')[-1] /F
>> }