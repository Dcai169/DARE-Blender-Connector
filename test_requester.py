import requests
r = requests.head('http://localhost:41786', headers={'X-Content-Path': 'C:\\Users\\caid\\Documents\\DARE Output\\DestinyModel0'})
r.raise_for_status()

print(r.status_code)