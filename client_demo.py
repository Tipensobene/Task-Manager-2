import requests


try:
    response = requests.get(
        'http://127.0.0.1:8000/tasks/stats',
        timeout=5
    )

    print(response.status_code)

    if response.status_code == 200:
        data=response.json()
        print(
            f"总任务数：{data['total']}\n"
            f"已完成任务数：{data['completed_num']}\n"
            f"未完成任务数：{data['uncompleted_num']}"
        )

    else:
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"请求失败：{e}")

