import ctypes
import os
import threading
import time

import cv2
import keyboard
import numpy as np
import pyautogui
import winsound

# 加载user32.dll库
user32 = ctypes.windll.user32

exit_sign = False
running = False
beep = False

press_thread = None
click_thread = None

delay = 1
count = 0
leftC_delay = 2
repeat_num = 0


def print_msg():
    print("\033[1;33m" + "*=" * 20 + "\033[0m\n\n",
          "\033[1;31m     按下 \033[1;36mF8\033[1;31m 启动或暂停脚本 \033[1;36mF12\033[1;31m 关闭脚本。\033[0m\n\n",
          "\033[1;33m" + "*=" * 20 + "\033[0m")


def XY_getter(this_path, threshold=0.006):
    # 获取当前截图并转为 numpy 数组
    screenshot = pyautogui.screenshot()
    screenshot_np = np.array(screenshot)  # 将 PIL 图像转为 numpy 数组
    img = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)  # 转为 BGR 格式以兼容 OpenCV

    # 读取截图和目标图像
    img_target = cv2.imread(this_path)

    print(f"[INFO]\033[1;93m正在处理路径：\033[0m{this_path}")

    # 确保图像正确加载
    if img is None or img_target is None:
        raise FileNotFoundError("[ERROR]\033[1;31m无法加载截图或目标图像，请检查路径\033[0m")

    # 获取目标图像尺寸
    this_high, this_wid, _ = img_target.shape

    # 执行模板匹配
    this_result = cv2.matchTemplate(img, img_target, cv2.TM_SQDIFF_NORMED)

    # 获取匹配结果最小值
    min_val, _, min_loc, _ = cv2.minMaxLoc(this_result)

    # 检查是否超过阈值
    if min_val > threshold:
        print(f"[ERROR]\033[1;31m匹配失败，最小匹配值: \033[0m{min_val}")
        # 返回 None 表示匹配失败
        return None

    # 计算中心位置坐标
    upper_left = min_loc
    lower_right = (upper_left[0] + this_wid, upper_left[1] + this_high)
    center_x = int((upper_left[0] + lower_right[0]) / 2)
    center_y = int((upper_left[1] + lower_right[1]) / 2)
    return center_x, center_y


def to_click(this_xy, bt):
    x = this_xy[0]
    y = this_xy[1]
    pyautogui.click(x, y, button=bt)


# def to_click(button: str, x, y):
#     # 按下和释放鼠标按键
#     if button == "left":
#         user32.mouse_event(0x0002, x, y, 0, 0)  # 鼠标左键按下
#         user32.mouse_event(0x0004, x, y, 0, 0)  # 鼠标左键松开
#     elif button == "right":
#         user32.mouse_event(0x0008, x, y, 0, 0)  # 鼠标右键按下
#         user32.mouse_event(0x0010, x, y, 0, 0)  # 鼠标右键松开


def do():
    global delay, beep

    while running:

        # 加载点击目标文件
        with open("target_path.txt", "r", encoding="utf-8") as file1:
            content = file1.readlines()
        for this_path in content:
            if not running:
                break
            time.sleep(delay)
            # 注解功能
            if this_path.startswith("#"):
                continue
            elif this_path.lower().startswith("r-"):
                btn = "right"
                this_path = this_path[2:]
            elif this_path.lower().startswith("l-"):
                btn = "left"
                this_path = this_path[2:]
            elif this_path.lower().startswith("space-"):
                this_path = this_path[6:]
                btn = "space"
            else:
                cache = this_path.split("-")
                btn = cache[0]
                this_path = cache[1]

            try:
                this_xy = XY_getter(this_path.strip())
                # 为空时跳过
                if this_xy is None:
                    continue

                if btn in ["left", "right"]:
                    to_click(this_xy, btn)
                elif btn == "space":
                    pyautogui.press('space')
                else:
                    pyautogui.press(btn)
                # to_click(button=btn)

                if beep:
                    # 响一声表示成功执行
                    winsound.Beep(800, 500)

                msg = os.path.basename(this_path)
                # 使用字典简化多条件判断
                clicker = {
                    "left": "左键",
                    "space": "空格",
                    "right": "右键"
                }.get(btn, f"摁下{btn}")

                print(f"[INFO]\033[1;92m成功{clicker}点击\033[0m：{msg}")
            except Exception as e:
                print(e)
                continue


def click_Thread():
    global leftC_delay, beep
    c = 0
    while running:
        c += 0.1
        if c <= leftC_delay:
            time.sleep(0.1)
            continue

        c = 0
        user32.mouse_event(0x0002, 0, 0, 0, 0)  # 鼠标左键按下
        user32.mouse_event(0x0004, 0, 0, 0, 0)  # 鼠标左键松开
        print("[CLICKER]\033[1;92m已点击一次\033[0m")

        if beep:
            winsound.Beep(555, 666)


def begin_script():
    global running, press_thread, click_thread
    init()
    if running:
        running = False
        if press_thread is not None:
            press_thread.join()  # 等待线程结束
            if delay > 0:
                click_thread.join()
        print("脚本\033[1;31m已停止\033[0m")
    else:
        running = True
        press_thread = threading.Thread(target=do)
        click_thread = threading.Thread(target=click_Thread)
        press_thread.start()
        if delay > 0:
            click_thread.start()
        print("脚本\033[1;36m已启动\033[0m")


def init():
    global delay, beep, count, leftC_delay
    # 加载配置文件
    with open("config.txt", "r", encoding="utf-8") as file:
        content = file.readlines()
    try:
        for line in content:
            # 注解功能
            if line.startswith("#"):
                continue
            elif line.lower().startswith("beep:"):
                beep = True if line.lower().strip().endswith("true") else False
            elif line.startswith("delay:"):
                delay = float(line.lower().strip().replace("delay:", ""))
            elif line.lower().startswith("leftclick_delay:"):
                leftC_delay = float(line.lower().strip().replace("leftclick_delay:", ""))
    except Exception as e:
        print(e)


# 定义按下按键时的回调函数
def on_key_event(event):
    global repeat_num, exit_sign
    repeat_num += 1
    # 避免重复
    if repeat_num < 2:
        return
    # 检查是否是按键按下事件
    if event.name == 'f8':
        repeat_num = 0
        begin_script()
    # 退出脚本
    elif event.name == 'f12':
        print("[INFO]\033[1;36m正在关闭程序！\033[0m")
        begin_script()
        # 关闭脚本
        exit_sign = True


if __name__ == '__main__':
    """
    绑定 F8 热键  在这里监听 F8 键启动或停止长按操作
    keyboard.add_hotkey('F8', begin_script) 不是很好用，因为在玩的时候似乎会失效。

    2024/11/13更新：
    1.改进的键盘的监听。
    2.改进了匹配的精度，避免了乱点。
    3.目前支持了更多的可 press 键。
    4.支持达到特定条件直接退出，避免了 keyboard.wait() 无效的问题。
    5.优化了截屏的读取，避免了多余的I/O开支。
    """
    # 打印提示
    print_msg()
    # 添加全局监听器
    keyboard.hook(on_key_event)
    # 使用循环检查退出标志，避免阻塞
    while not exit_sign:
        time.sleep(0.1)  # 延迟以降低CPU占用
