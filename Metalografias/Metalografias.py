# Para ventana
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as Imag
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics.texture import Texture
from kivy.config import Config
Config.set('graphics', 'resizable', 0)  # Desactiva el cambio de tamaño
# Para procesamiento
import imutils
# JIS G5502-2022 ISO法、JIS法による球状化率の判定
# -*- coding: utf-8 -*-
from PIL import Image
import numpy as np
import cv2
import os
import sys
import datetime
import math
import platform as platf

# Inicio de funcion de proceso
# https://www.rectus.co.jp/archives/18
# pythonのprintでエラーになるときの対応
import io
#sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 環境設定 - Entorno ambiental
iDir="" 
ossys = os.name
if ossys == "Windows":
    iDir=os.path.expanduser(r'~\Desktop')
else:
    iDir=os.path.dirname(os.path.abspath(__file__))
# 画像ファイルが格納されているフォルダ - Carpeta donde se almacenan los archivos de imagen.

pic_width=1920 
# 入力画像のサイズによらず、画像処理や出力画像はこの幅に設定
# Independientemente del tamaño de la imagen de entrada, el procesamiento de imágenes y las imágenes de salida se configuran en este ancho.

# pic_height（高さ）は入力画像の幅と高さの比から計算
# pic_height (alto) se calcula a partir de la relación entre el ancho y el alto de la imagen de entrada

min_grainsize= 0.0071 #0.0071 
# 画像の幅に対する黒鉛の最小長さ（撮影した画像に応じて設定が必要）
# "Longitud mínima de grafito en relación con el ancho de la imagen (se requiere ajuste según la imagen capturada)".
# min_grainsize=0.007はサンプル画像に対する値である。
# "min_grainsize=0.007 es un valor para la imagen de muestra."
# サンプル画像は幅142mmに表示させると、倍率100倍の組織画像になる. 
# "Cuando la imagen de muestra se muestra con un ancho de 142 mm, se convierte en una imagen de estructura a 100x de aumento."
# この場合、黒鉛の最小長さ（10μm）は1mmとなる。1mm÷142mm=0.007→min_grainsize. 
# "En este caso, la longitud mínima de grafito (10 μm) se convierte en 1 mm. 1 mm ÷ 142 mm = 0.007 → min_grainsize."

marumi_ratio = 0.6 #iso法で形状ⅤとⅥと判定する丸み係数のしきい値

# ダイアログ形式によるファイル選択

# contoursからmin_grainsize未満の小さい輪郭と、画像の端に接している輪郭を除いてcoutours1に格納
#  "Almacena en contours1 los contornos que son más grandes que min_grainsize y que no están en contacto con los bordes de la imagen."
def select_contours(contours, pic_width, pic_height, min_grainsize):
    contours1 = []
    for e, cnt in enumerate(contours):
        x_rect, y_rect, w_rect, h_rect = cv2.boundingRect(cnt)
        (x_circle, y_circle), radius_circle = cv2.minEnclosingCircle(cnt)
        if int(pic_width * min_grainsize) <= 2 * radius_circle \
            and 0 < int(x_rect) and 0 < int(y_rect) and \
            int(x_rect + w_rect) < pic_width and int(y_rect + h_rect) < pic_height:
            contours1.append(cnt)  
    return contours1

# 輪郭の長軸の中心座標と、最遠点対の半分の長さを求める（キャリパ法）
# "Calcular las coordenadas del centro del eje mayor del contorno y la mitad de la longitud del par de puntos más distantes (método de calibración)."
def get_graphite_length(hull):
    max_distance = 0
    for i, hull_x in enumerate(hull):
        for j, hull_y in enumerate(hull):
            if j + 1 < len(hull) and i != j + 1:
                dis_x = hull[j+1][0][0] - hull[i][0][0]
                dis_y = hull[j+1][0][1] - hull[i][0][1]
                dis = math.sqrt(dis_x**2 + dis_y**2)
                if dis > max_distance:
                    max_distance = dis # 最遠点対の距離を更新
                    x = dis_x * 0.5 + hull[i][0][0] # 最遠点対の中点を更新
                    y = dis_y * 0.5 + hull[i][0][1] # 最遠点対の中点を更新
    return(x, y, max_distance * 0.5) # 最遠点対の半分の長さ（円の半径）

class FileChooserPopup(Popup):
    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Selecciona una imagen'
        self.size_hint = (0.5, 0.5)
        self.filechooser = FileChooserListView(path=iDir, filters=['*.jpg', '*.png', '*.jpeg'])
        self.on_select = on_select
        
        # Botones de abrir y cerrar
        self.open_button = Button(text='Abrir', size_hint_y=None, height=50)
        self.close_button = Button(text='Cerrar', size_hint_y=None, height=50)

        # Enlazar los botones a funciones
        self.open_button.bind(on_release=self.open_file)
        self.close_button.bind(on_release=self.dismiss)

        # Layout principal
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.filechooser)
        
        # Layout para los botones
        button_layout = BoxLayout(size_hint_y=None, height=50)
        button_layout.add_widget(self.open_button)
        button_layout.add_widget(self.close_button)

        layout.add_widget(button_layout)
        self.add_widget(layout)

    def open_file(self, instance):
        selection = self.filechooser.selection
        if selection:
            self.on_select(selection[0])  # Llama a la función pasada con el archivo seleccionado
            self.dismiss()  # Cierra el Popup

class MyApp(App):
    def build(self):
        App.title = "Sistema de conteo de Nódulos JIS - ISO"
        # Establece la ventana en modo maximizado
        Window.size = (Window.width, Window.height)
        Window.maximize()  # Maximiza la ventana
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        title_label = Label(text="[b]SISTEMA BASICO DE CONTEO \n DE NODULOS[/b]", font_size='50sp', size_hint=(1, 0.5), markup=True, halign="center")
        main_layout.add_widget(title_label)

        # Imágenes en un BoxLayout
        images_layout = BoxLayout(orientation='horizontal', spacing=5, size_hint=(1,1), padding=5)

        self.img1 = Imag(size_hint=(1, 1))
        self.img1.source= 'iso.png'
        self.img2 = Imag(size_hint=(1, 1))
        self.img2.source ='jis.png'

        images_layout.add_widget(self.img1)
        images_layout.add_widget(self.img2)

        main_layout.add_widget(images_layout)
        
        # Etiquetas en un GridLayout
        labels_layout = GridLayout(cols=2, spacing=5, size_hint=(1, 0.3))
        self.labels = [Label(text=f'Resultados {i + 1}', font_size='18sp', size_hint=(1, 0.3), markup=True) for i in range(4)]
        
        for self.label in self.labels:
            labels_layout.add_widget(self.label)
        
        main_layout.add_widget(labels_layout)


        # Botones en un BoxLayout
        buttons_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.3))

        button1 = Button(text='[b]Cargar imágen a procesar[/b]', size_hint=(0.5, None), height=50, markup=True)
        button1.bind(on_release=self.show_filechooser)
        button2 = Button(text='[b]Salir[/b]', size_hint=(0.5, None), height=50, markup=True)
        button2.bind(on_release=self.salir)

        buttons_layout.add_widget(button1)
        buttons_layout.add_widget(button2)

        main_layout.add_widget(buttons_layout)

        return main_layout
    
    def show_filechooser(self, instance):
        popup = FileChooserPopup(on_select=self.analizar)
        popup.open()
        
    def salir(self, instance):
        App.get_running_app().stop()
        
        
    def analizar(self, image_path):
        # 画像ファイル名の取り込み
        image = image_path
        if image == "":
            sys.exit()

        # 画像ファイルごとの球状化率はこの変数に格納
        nodularity_ISO = 0
        nodularity_JIS = 0


        # 画像ファイルの読み込み、サイズ取得（パス名に全角があるとエラーになる）
        img_color_ISO= cv2.imread(image) # カラーで出力表示させるためカラーで読み込み
        img_height, img_width, channel = img_color_ISO.shape # 画像のサイズ取得
        
        # 画像処理や出力画像のサイズ計算（pic_width, pic_height）
        pic_height=int(pic_width * img_height / img_width)
        img_color_ISO = cv2.resize(img_color_ISO, (pic_width, pic_height)) # 読み込んだ画像ファイルのサイズ変換
        img_color_JIS = img_color_ISO.copy() #img_colorのコピーの作成
        
        # カラー→グレー変換、白黒反転の二値化、輪郭の検出、球状化率の評価に用いる輪郭の選別
        img_gray = cv2.cvtColor(img_color_ISO, cv2.COLOR_BGR2GRAY)
        ret, img_inv_binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        contours, hierarchy = cv2.findContours(img_inv_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contours1 = select_contours(contours, pic_width, pic_height, min_grainsize) # 球状化率の評価に用いる輪郭をcoutours1に格納

        # 黒鉛の面積と黒鉛の長軸の中心座標、長軸の半分の長さの計算、丸み係数の算出
        sum_graphite_areas = 0
        sum_graphite_areas_5and6 = 0
        num_graphite1 = num_graphite2 = num_graphite3 = num_graphite4 = num_graphite5 = 0

        for i, cnt in enumerate(contours1): 
            graphite_area = cv2.contourArea(cnt)
            sum_graphite_areas += graphite_area
            hull = cv2.convexHull(cnt) # 凸包
            x, y, graphite_radius = get_graphite_length(hull) # 輪郭の長軸の中心座標（x, y）と長軸の半分の長さ(graphite_radius)
            marumi = graphite_area / ((graphite_radius ** 2) * math.pi) #丸み係数

            # ISO法による形状ⅤとⅥの黒鉛の判定し、それらの黒鉛の輪郭を赤色で描画
            if marumi >= marumi_ratio:
                sum_graphite_areas_5and6 += graphite_area
                cv2.drawContours(img_color_ISO, contours1, i, (0, 0, 255), 2)

            # JIS法による形状分類
            if marumi <= 0.2:
                num_graphite1 += 1
                cv2.drawContours(img_color_JIS, contours1, i, (255, 255, 0), 2) #水色
            if 0.2 < marumi <= 0.4:
                num_graphite2 += 1
                cv2.drawContours(img_color_JIS, contours1, i, (0, 255, 0), 2) #緑
            if 0.4 < marumi <= 0.7:
                num_graphite3 += 1
                cv2.drawContours(img_color_JIS, contours1, i, (128, 0, 128), 2) #紫
            if 0.7 < marumi <= 0.8:
                num_graphite4 += 1
                cv2.drawContours(img_color_JIS, contours1, i, (255, 0, 0), 2) #青
            if 0.8 < marumi:
                num_graphite5 += 1
                cv2.drawContours(img_color_JIS, contours1, i, (0, 0,255), 2) #赤
                    
        # 球状化率（ISO法）
        nodularity_ISO = sum_graphite_areas_5and6 / sum_graphite_areas * 100
            # 球状化率（JIS法）
        nodularity_JIS= (0.3 * num_graphite2 + 0.7 * num_graphite3 + 0.9 * num_graphite4 + 1.0 * num_graphite5)/ len(contours1) * 100
        
        # 画像ファイルの保存
        # src = filename
        # idx = src.rfind(r'.')
        #result_ISO_filename = src[:idx] + "_nodularity(ISO)." + src[idx+1:]
        #result_JIS_filename = src[:idx] + "_nodularity(JIS)." + src[idx+1:]
        #cv2.imwrite(result_ISO_filename, img_color_ISO)
        #cv2.imwrite(result_JIS_filename, img_color_JIS)
        imageiso = img_color_ISO
        imageiso = cv2.resize(imageiso, (500, 400))
        imagejis = img_color_JIS
        imagejis = cv2.resize(imagejis, (500, 400))
        #cv2.imshow("ISO", imageiso)
        #cv2.imshow("JIS", imagejis)  
        # --- Nuevas funciones
        #isoimg = cv2.imread(imageiso)
        isoimg = imutils.resize(imageiso, height=600, width=600)
        imageToIso = cv2.cvtColor(isoimg, cv2.COLOR_BGR2RGB)
        #imiso = Image.fromarray(imageToIso )
        #imageiso = Image(source=imiso)
        
        #jisimg = cv2.imread(imagejis)
        jisimg = imutils.resize(imagejis, height=600, width=600)
        imageToJis = cv2.cvtColor(jisimg, cv2.COLOR_BGR2RGB)
        
        imjis = Image.fromarray(imageToJis )
        #imagejis = Image(source=imjis)
        
        # img1.config(image=imageiso)
        #texture = self.image_to_texture(imiso)
        texture = Texture.create(size=(imageToIso.shape[1], imageToIso.shape[0]), colorfmt='rgb')
        texture.blit_buffer(imageToIso.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        self.img1.texture = texture
        #self.img1.texture= texture
        # img2.config(image=imagejis)
        #texture = self.image_to_texture(imjis)
        texture = Texture.create(size=(imageToJis.shape[1], imageToJis.shape[0]), colorfmt='rgb')
        texture.blit_buffer(imageToJis.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        self.img2.texture = texture
        # ---          
            
        # 球状化率などのデータの保存
        # now = datetime.datetime.now()

        #output_file = str(os.path.dirname(image[0])) + '/nodularity_{0:%Y%m%d%H%M}'.format(now) + ".csv"
        self.valormingra=f"[b]Método ISO):[/b] "
        self.labels[0].text=str(self.valormingra)
        
        self.valorminretio =f"[b]Método JIS:[/b] "
        self.labels[1].text=str(self.valorminretio)
        
        self.valornodiso=f"{round(nodularity_ISO, 2)}"
        self.labels[2].text=str(self.valornodiso)
        
        self.valornodjis= f"{round(nodularity_JIS, 2)}"
        self.labels[3].text=str(self.valornodjis)
        
        # 任意のキーまたは「閉じる」ボタンをクリックするとウィンドウを閉じてプログラムを終了する
        #while True:
        #    key = cv2.waitKey(100) & 0xff
        #    if key != 255 or cv2.getWindowProperty('ISO', cv2.WND_PROP_VISIBLE) !=  1 or cv2.getWindowProperty('JIS', cv2.WND_PROP_VISIBLE) !=  1:
        #        break
        #cv2.destroyAllWindows()
        
    #def exit(self):
    #    sys.exit()            


if __name__ == '__main__':
    MyApp().run()