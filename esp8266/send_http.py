from requests import post
from json import dumps


def post_temp(t, s, dp):
    url = "https://mvawcxui6v5.feishu.cn/space/api/bitable/share/content"

    data = {# "fldEi2LGAn":{"type":5,"value":get_time() * 1000},
     "fldF9Zuv8h":{"type":2,"value":t}, 
     "fldcJbXiZR":{"type":2,"value":s},
     "flduGPSBiZ":{"type":2,"value":dp},
     }

    payload = {
        "data": dumps(data),
        "shareToken":"shrcnCbGkHxjKxuNhOZdBQ9KK4d",
        "preUploadEnable":False 
        }

    headers = {
        "cookies": "session=U7CK1RF-405ld771-08cf-4d80-b3b4-0387ced795e8-NN5W4; _csrf_token=47424c6743a5873d3a11d77c3a0697fcfb1be058-1741437016;",
        "referer": "https://mvawcxui6v5.feishu.cn/share/base/form/shrcnCbGkHxjKxuNhOZdBQ9KK4d",
        "x-csrftoken": "47424c6743a5873d3a11d77c3a0697fcfb1be058-1741437016",
        "x-auth-token": "U7CK1RF-405ld771-08cf-4d80-b3b4-0387ced795e8-NN5W4",
        "user-agrent": "Uploader TMP/v1"
        }
    resp = post(url, json=payload, headers=headers)
    
    return resp.status_code


def post_error(message):
    """上传错误日志"""

    return post(
        "https://open.feishu.cn/open-apis/bot/v2/hook/e2a01f5d-eeee-4b13-b792-64b70375caf7",
        json={"msg_type":"post","content":{"post":{"zh_cn":{"title":"ESP8266错误信息:","content":[[{"tag":"text","text": message}]]}}}},
        headers={"Content-Type": "application/json"}
            )

if __name__ == "__main__":
#     resp = post_temp(0,0,0)
#     print(resp)
    # print(resp.request.url, "\n\n", resp.request.headers, "\n", resp.request.body, "\n\n\n")
#     import requests
# #     resp = requests.get("https://f.m.suning.com/api/ct.do")
    resp = post_error("Test\ntest2")
    print(resp.text, resp.status_code)

