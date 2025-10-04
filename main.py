import cv2
import mediapipe as mp
import pyautogui
import numpy as np

class VirtualMouse:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.screen_width, self.screen_height = pyautogui.size()
        
        self.prev_x, self.prev_y = 0, 0
        self.frame_width, self.frame_height = 640, 480
        
        # Tıklama durumu
        self.last_action_time = 0
        
    def get_finger_state(self, landmarks):
        """Parmak durumunu kontrol et"""
        fingers = [0, 0, 0, 0, 0]  # [baş, işaret, orta, yüzük, serçe]
        
        # Parmak kontrolleri
        if landmarks[8].y < landmarks[6].y:  # İşaret parmağı
            fingers[1] = 1
        if landmarks[12].y < landmarks[10].y:  # Orta parmak
            fingers[2] = 1
        if landmarks[16].y < landmarks[14].y:  # Yüzük parmağı
            fingers[3] = 1
        if landmarks[20].y < landmarks[18].y:  # Serçe parmak
            fingers[4] = 1
            
        return fingers
    
    def process_hand_gestures(self, landmarks, img):
        h, w, c = img.shape
        
        # İşaret parmağı pozisyonu
        index_tip = landmarks[8]
        x = int(index_tip.x * w)
        y = int(index_tip.y * h)
        
        # Ekran koordinatları
        screen_x = np.interp(x, [0, self.frame_width], [0, self.screen_width])
        screen_y = np.interp(y, [0, self.frame_height], [0, self.screen_height])
        
        # Parmak durumu
        fingers = self.get_finger_state(landmarks)
        
        # FARE HAREKETİ - Sadece işaret parmağı açıkken
        if fingers[1] == 1:
            if self.prev_x != 0 and self.prev_y != 0:
                screen_x = self.prev_x + (screen_x - self.prev_x) / 3
                screen_y = self.prev_y + (screen_y - self.prev_y) / 3
            
            pyautogui.moveTo(screen_x, screen_y)
            self.prev_x, self.prev_y = screen_x, screen_y
            
            cv2.putText(img, "FARE HAREKETI", (10, 400), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # TIKLAMA KONTROLÜ - Sadece BAŞPARMAK ile
        current_time = cv2.getTickCount() / cv2.getTickFrequency()
        
        # SOL TIK: İşaret + Başparmak yakın
        index_tip = landmarks[8]
        thumb_tip = landmarks[4]
        distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2)
        
        if distance < 0.05:  # Parmaklar yakınsa
            if current_time - self.last_action_time > 0.8:  # 0.8 saniye bekle
                pyautogui.click()
                cv2.putText(img, "SAG TIK!", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                self.last_action_time = current_time
        
        # SAĞ TIK: Orta + Yüzük parmak açık
        elif fingers[2] == 1 and fingers[3] == 1:
            if current_time - self.last_action_time > 0.8:
                pyautogui.rightClick()
                cv2.putText(img, "SOL TIK!", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                self.last_action_time = current_time
        
        # SCROLL: Serçe parmak açık
        elif fingers[4] == 1:
            if current_time - self.last_action_time > 0.5:
                pyautogui.scroll(10)
                cv2.putText(img, "SCROLL!", (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 3)
                self.last_action_time = current_time
        
        # Görsel feedback
        cv2.circle(img, (x, y), 10, (255, 0, 255), cv2.FILLED)
        
        # Mesafe bilgisi
        cv2.putText(img, f"Mesafe: {distance:.3f}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Tik: <0.05", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def start(self):
        cap = cv2.VideoCapture(0)
        cap.set(3, self.frame_width)
        cap.set(4, self.frame_height)
        
        print("🎯 YENI SANAL FARE BASLATILDI!")
        print("KULLANIM:")
        print("- İşaret parmağı → Fare hareketi")
        print("- İşaret + Başparmak BİRLEŞTİR → SAĞ TIK")
        print("- Orta + Yüzük parmak AÇIK → SOL TIK") 
        print("- Serçe parmak AÇIK → SCROLL")
        print("- Q → Çıkış")
        print("\n💡 İPUCU: Fare hareketi için sadece işaret parmağını kullan!")
        
        while True:
            success, img = cap.read()
            if not success:
                break
                
            img = cv2.flip(img, 1)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            results = self.hands.process(rgb_img)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    self.process_hand_gestures(hand_landmarks.landmark, img)
            else:
                cv2.putText(img, "EL ALGILANMADI", (150, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                self.prev_x, self.prev_y = 0, 0
            
            cv2.imshow("Eag Vitural Mouse", img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

def main():
    try:
        virtual_mouse = VirtualMouse()
        virtual_mouse.start()
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()