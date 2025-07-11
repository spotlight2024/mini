from locust import HttpUser, task, between, events
import json
import csv
from threading import Lock

results = []
results_lock = Lock()

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    host = "http://127.0.0.1:8002"

    @task
    def mock_click(self):
        with self.client.post(
            "/mock_click",
            json={
                "serial_id": "test_serial",
                "method": "css selector",
                "selector": ".test-selector"
            },
            catch_response=True
        ) as response:
            try:
                data = response.json().get("data", {})
                process_time = data.get("process_time")
                mock_delay = data.get("mock_delay")
                with results_lock:
                    results.append({
                        "type": "mock_click",
                        "response_time": response.elapsed.total_seconds(),
                        "process_time": process_time,
                        "mock_delay": mock_delay
                    })
                response.success()
            except Exception as e:
                response.failure(f"解析响应失败: {e}")

    @task
    def mock_find_element(self):
        with self.client.post(
            "/mock_find_element",
            json={
                "serial_id": "test_serial",
                "method": "css selector",
                "selector": ".test-selector"
            },
            catch_response=True
        ) as response:
            try:
                data = response.json().get("data", {})
                process_time = data.get("process_time")
                mock_delay = data.get("mock_delay")
                with results_lock:
                    results.append({
                        "type": "mock_find_element",
                        "response_time": response.elapsed.total_seconds(),
                        "process_time": process_time,
                        "mock_delay": mock_delay
                    })
                response.success()
            except Exception as e:
                response.failure(f"解析响应失败: {e}")

@events.quitting.add_listener
def export_results(environment, **kwargs):
    with open("locust_results.csv", "w", newline="") as csvfile:
        fieldnames = ["type", "response_time", "process_time", "mock_delay", "extra_delay"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        with results_lock:
            for row in results:
                extra_delay = None
                if row["process_time"] is not None and row["response_time"] is not None:
                    extra_delay = row["response_time"] - row["process_time"]
                writer.writerow({
                    "type": row["type"],
                    "response_time": row["response_time"],
                    "process_time": row["process_time"],
                    "mock_delay": row["mock_delay"],
                    "extra_delay": extra_delay
                })
    print("已导出详细对比数据到 locust_results.csv") 