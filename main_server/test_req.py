import urllib.request
import urllib.parse
import json

payload = {
    "on_line_proof_slip_no": "123",
    "slip_date": "2026-08-02",
    "type_of_proof": "test",
    "store": "store",
    "lot_no": "lot1",
    "quantity": 10,
    "proof_sample_size": 2,
    "proof_schedule_test_programme_ref": "ref",
    "material_used": "[]",
    "remarks": None,
    "date": "2026-08-02",
    "proof_result_no": "123"
}

def test():
    # Login
    data = urllib.parse.urlencode({"username": "admin", "password": "admin"}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:8080/api/auth/login", data=data)
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode())
    token = res["access_token"]
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req2 = urllib.request.Request("http://127.0.0.1:8080/api/proofs", data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req2) as response2:
            print(response2.status)
            print(response2.read().decode())
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read().decode())

test()
