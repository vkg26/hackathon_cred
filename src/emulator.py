import uiautomator2 as u2
import time

# Connect to the phone
d = u2.connect()  # or u2.connect_usb() if you face issues

# print(d.dump_hierarchy())
# d(className="android.view.ViewGroup", clickable=True, bounds="[0,640][1008,780]").click()
for obj in d(className="android.view.ViewGroup", clickable=True):
    if obj.info["bounds"] == {"left": 23, "top": 1757, "right": 667, "bottom": 2190}:
        obj.click()
        break
    
for obj in d(className="android.view.ViewGroup", clickable=True):
    print(obj.info["bounds"])

# # Step 2: Open recent apps to show it's working
# d.press("recent")
# time.sleep(2)
# d.press("home")

# # Step 3: Open an app (change package if needed)
# d.app_start("com.android.settings")  # Opens settings
# time.sleep(2)
# d.press("home")

print("✅ All actions completed!")
