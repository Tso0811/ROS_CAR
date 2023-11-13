import Jetson.GPIO as GPIO
import re
import time
from Rosmaster_Lib import Rosmaster
import cv2

# 初始化GPIO
GPIO.setmode(GPIO.BOARD) # 指定32為版面？？？
GPIO.setup(32, GPIO.IN) # 藍芽的TX接到GPIO的32腳位

# 定義變數和初始值
data = ""
utf8 = ""
output = ""
latfilename = "data.txt"
filename = "data.txt"  # 指定要保存数据的文件名
filenamenumber = 0
recording = False
stop_signal = "OFFF"
servo=90 # 控制前輪角度建議為45~135(90為直走) 官方為0~180--------
moter=0 #後輪馬達範圍為-100~100 （正值為往前，負值為往後）------

# 讀取前一個狀態和時間戳記input
prev_state = GPIO.input(32)
prev_timestamp = time.time() # 1970年1月1日0:00至今的秒數

cap = cv2.VideoCapture(0) ###################
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 视频编码器（使用XVID）
output_filename = 'output.avi'  # 输出视频文件名
out = cv2.VideoWriter(output_filename, fourcc, 20.0, (640, 480))  # 参数分别为文件名、编码器、帧率、分辨率


cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)

print("START")
bot = Rosmaster() #---------

def run_motor( motor):

 M1=0

 M3=0

 bot.set_motor(M1, motor, M3, motor)
 
def pwm_servo(S1):

 bot.set_pwm_servo(1, S1)




try:
    while True:
        current_state = GPIO.input(32) # 靜止不動為1 有動為0

        # 檢查當前狀態是否與前一個狀態不同
        if current_state != prev_state:
            data += str(current_state)
            current_timestamp = time.time()
            duration = current_timestamp - prev_timestamp
            prev_timestamp = current_timestamp
            dwduration = round(duration * 9600)
            dwcurrent_state = current_state ^ 1 # XOR (0變1 1變0)

            # 檢查時間間隔，並將狀態值附加到utf8變數中    utf8共39個bits
            if dwduration < 500:
                cnt = 0
                while cnt < dwduration:
                    utf8 = str(dwcurrent_state) + utf8
                    cnt += 1

            # 如果utf8的長度達到39，則進行數據處理和轉換
            if len(utf8) >= 39:
                utf8 = utf8[:-1] # 取0~37
                utf8_1 = utf8[:8] # 取0~7 (8,9必為01)
                utf8_2 = utf8[10:18] # 取10~17 (18,19必為01)
                utf8_3 = utf8[20:28] # 取20~27
                utf8_4 = utf8[30:38] # 取30~37

                decimal_value_1 = int(utf8_1, 2) # 從2進制變16進制
                decimal_value_2 = int(utf8_2, 2)
                decimal_value_3 = int(utf8_3, 2)
                decimal_value_4 = int(utf8_4, 2)

                character_1 = chr(decimal_value_1) # y的數字
                character_2 = chr(decimal_value_2) # y(-)/Y(+)
                character_3 = chr(decimal_value_3) # x的數字
                character_4 = chr(decimal_value_4) # x(-)/X(+)

                # 根據特定字符組合生成輸出字符串
                if character_4 == 'x' and character_2 == 'Y':
                    output = "X=-" + character_3 + "Y=" + character_1
                if character_2 == 'y' and character_4 == 'X':
                    output = "X=" + character_3 + "Y=-" + character_1
                if character_2 == 'y' and character_4 == 'x':
                    output = "X=-" + character_3 + "Y=-" + character_1
                if character_2 == 'Y' and character_4 == 'X':
                    output = "X=" + character_3 + "Y=" + character_1

                utf8 = ""
                print(output)
                
                matches = re.findall(r'-?\d+', output)
                if len(matches) >= 2:
                    servo = int(matches[0])#X的數值
                    moter = int(matches[1])#Y的數值
                    moter*=4
                    servo = 90+(servo*5)
                if(moter<100 and moter>-100):
                    run_motor(moter)
                if(servo>45 and servo<135):
                    pwm_servo(servo)


                # 檢查特定字符組合來控制錄製狀態和文件名
                if character_4 + character_3 + character_2 + character_1 == "ONON":
                    recording = True
                    filename = str(filenamenumber) + latfilename
                    print("開始紀錄。")
                if character_4 + character_3 + character_2 + character_1 == "OFFF":
                    recording = False
                    filenamenumber = int(filenamenumber) + 1
                    print("停止紀錄。")
                    break



                
                # 如果處於錄製狀態，將output寫入到文件中
                if recording:
                    with open(filename, "a") as file:
                        file.write(str(servo)+ "\n")
                        
                if recording:
                    ret, frame = cap.read()  # 读取一帧图像
                    cv2.imshow("摄像头", frame)
                    out.write(frame)
                     
                         

                        

        prev_state = current_state

finally:
    # 清理GPIO資源
    GPIO.cleanup()



