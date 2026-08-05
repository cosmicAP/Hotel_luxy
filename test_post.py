import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

cj = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# GET request to get the cookie
r = opener.open('http://127.0.0.1:8000/signup/')
csrf = None
for cookie in cj:
    if cookie.name == 'csrftoken':
        csrf = cookie.value

data = urllib.parse.urlencode({'csrfmiddlewaretoken': csrf, 'username': 'a'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/signup/', data=data)
req.add_header('Referer', 'http://127.0.0.1:8000/signup/')

r2 = opener.open(req)
html = r2.read().decode()
print(f"Status: {r2.status}")
if "errorlist" in html:
    print("Errorlist found!")
    for line in html.split('\n'):
        if "errorlist" in line:
            print(line.strip())
else:
    print("No errorlist found!")
