import time
from gochara_south_indian import calculate_gochara_chart

print("Starting benchmark...")
start = time.time()
res = calculate_gochara_chart(
    date="2026-03-21",
    time="11:21:10",
    place="Bhongir, India",
    latitude=17.51083,
    longitude=78.88889,
    timezone="Asia/Kolkata",
)
dur = time.time() - start
print(f"Calculated in {dur:.4f}s")
