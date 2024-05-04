from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivymd.app import MDApp
from kivy.uix.image import Image
import time
import mediapipe as mp
from threading import Thread
from kivymd.uix.button import MDIconButton
from mediapipe.tasks.python import vision
import cv2

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = vision.GestureRecognizer
GestureRecognizerOptions = vision.GestureRecognizerOptions
VisionRunningMode = vision.RunningMode

options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path='gesture_recognizer.task', delegate="CPU"),
        running_mode=VisionRunningMode.VIDEO)

gesture_text = ' ', 0, 0
recognizer = GestureRecognizer.create_from_options(options)
COUNTER = 0

class CameraApp(MDApp):
    def build(self):
        self.layout = FloatLayout()
        self.camera = cv2.VideoCapture(0)  # Инициализация камеры (0 - первая доступная камера)
        self.is_front_camera = False

        self.camera_view = Image()
        self.layout.add_widget(self.camera_view)


        self.switch_camera_button = MDIconButton(
            icon="switch.png",
            icon_size="50sp",
            md_bg_color='ffffff1d',
            pos_hint={'center_x': 0.2, 'center_y': 0.1},
            on_release = self.switch_camera


        )
        self.layout.add_widget(self.switch_camera_button)

        self.exit_button = MDIconButton(
            icon="exit.png",
            icon_size="50sp",
            md_bg_color='ffffff1d',
            pos_hint={'center_x': 0.8, 'center_y': 0.1},
            on_release = self.stop

        )
        self.layout.add_widget(self.exit_button)
        Clock.schedule_interval(self.update_camera_view, 1.0 / 30.0)

        return self.layout

    def detect_gestures(self, frame):
        global gesture_text
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        gesture_recognition_result = recognizer.recognize_for_video(mp_image, timestamp_ms=int(time.time() * 1000))
        result = gesture_recognition_result.gestures
        h, w, _ = frame.shape
        if result:
            name = result[0][0].category_name
            if name != 'None':
                y = int(min(hl.y for hl in gesture_recognition_result.hand_landmarks[0]) * h) - 30
                x = int(min(hl.x for hl in gesture_recognition_result.hand_landmarks[0]) * w)
                if x < 10:
                    x = 10
                if y < 30:
                    y = 30
                gesture_text = name, x, y
            else:
                gesture_text = ' ', 0, 0
        else:
            gesture_text = ' ', 0, 0

    def update_camera_view(self, dt):


        ret, frame = self.camera.read()
        if ret:
            # Обработка кадра и распознавание жестов
            global COUNTER
            COUNTER += 1
            t = Thread(target=self.detect_gestures, args=(frame,))
            if COUNTER == 5:
                t.start()
                COUNTER = 0

            # Вывод результатов на кадр

            buf = cv2.putText(frame, gesture_text[0], (gesture_text[1], gesture_text[2]), cv2.FONT_HERSHEY_COMPLEX, 1,
                    (0, 255, 0), 2)
            buf = cv2.flip(buf, 0).tobytes()
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')

            self.camera_view.texture = texture


    def switch_camera(self, instance):
        self.camera.release()
        self.is_front_camera = not self.is_front_camera
        camera_index = 1 if self.is_front_camera else 0
        self.camera = cv2.VideoCapture(camera_index)

    def stop(self, instance):
        self.camera.release()
        App.get_running_app().stop()

if __name__ == '__main__':
    CameraApp().run()