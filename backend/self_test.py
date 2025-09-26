import json, time, threading, requests

print('Attempting health check...')
for i in range(10):
    try:
        r = requests.get('http://127.0.0.1:5000/api/health', timeout=1)
        print('Health:', r.text)
        break
    except Exception as e:
        print('Retry', i+1, e)
        time.sleep(0.5)
else:
    print('Failed to reach server')
