from io import StringIO
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QFileDialog,
    QGraphicsPixmapItem, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QCheckBox, QListWidget, QAbstractItemView
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt,QThread
import sys
from PIL import Image,ImageDraw,ImageOps
import queue
import shutil

def iMage_expend(iMage_pass,paint_point):
    width ,height = iMage_pass.size
    paint_point_x, paint_point_y = paint_point
    left = top = right = bottom = 0
    width_index = width - 1
    height_index = height - 1
    if paint_point_x < 0:
        left = abs(paint_point_x)
    elif width_index < paint_point_x:
        right = paint_point_x - width_index

    if paint_point_y < 0:
        top = abs(paint_point_y)
    elif height_index < paint_point_y:
        bottom = paint_point_y - height_index
    expand = (left,top,right,bottom)
    iMage_pass = ImageOps.expand(image= iMage_pass,border=expand,fill=(0,0,0,0))
    expand = (left,top,right,bottom)
    return iMage_pass, expand

drawing_queue = queue.Queue()
class ImageDrawingThread(QThread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.provinces = {}
        self.numbers = ["0","1","2","3","4","5","6","7","8","9"]
    def run(self):
        while self.running:
            try:
                point1, point2,province_id_temporary,tool = drawing_queue.get(timeout=0.1)
                if (point1, point2, province_id, tool) != (None, None, None, None):
                    if tool == "add":
                        self.add(point1, point2,province_id_temporary)
                    if tool == "save":
                        self.save_provinces()
            except queue.Empty:
                continue
    def save_provinces (self):
        saved_province = []
        os.makedirs("save",exist_ok=True)
        print("better show this motherfucker")
        for i,j in self.provinces.items():
            key_str = i
            file = j
            lst_prov_key = key_str.split("_")
            prov_key = lst_prov_key[1]
            if prov_key not in saved_province:
                saved_province.append(prov_key)
                os.makedirs(f"save/province_{prov_key}",exist_ok=True)
            if isinstance(file,Image.Image):
                file.save(f"province_image_{prov_key}.png",format="png")
                shutil.move(f"province_image_{prov_key}.png",f"save/province_{prov_key}/province_image_{prov_key}.png")
            else:
                text_file = file.getvalue()
                with open(f"province_metadata_{prov_key}.txt","w") as output_file:
                    output_file.write(text_file)
                shutil.move(f"province_metadata_{prov_key}.txt",f"save/province_{prov_key}/province_metadata_{prov_key}.txt")
    def add(self,point1, point2,province_id_temporary):
        if f"province_{province_id_temporary}" in self.provinces and f"metadata_{province_id_temporary}" in self.provinces:
            red, green, bleu = extract_rgb_divmod(province_id_temporary)
            meta_data = self.provinces[f"metadata_{province_id_temporary}"]
            province_file = self.provinces[f"province_{province_id_temporary}"]
            meta_data.seek(0)
            province_image_center_txt = meta_data.readline()
            province_map_center_txt = meta_data.readline()
            list_str_province_image_center_txt = province_image_center_txt.split(",")
            img_cent_x = list_str_province_image_center_txt[0]
            img_cent_y = list_str_province_image_center_txt[1]
            province_image_center = (int(img_cent_x),int(img_cent_y))
            list_str_province_map_center_txt = province_map_center_txt.split(",")
            map_cent_x = list_str_province_map_center_txt[0]
            map_cent_y = list_str_province_map_center_txt[1]
            province_map_center = (int(map_cent_x), int(map_cent_y))
            dist_point_to_map_center = (point1[0] - province_map_center[0],point1[1] - province_map_center[1])
            province_file, index_change = iMage_expend(province_file,dist_point_to_map_center)

            dist_point_to_map_center = (dist_point_to_map_center[0] + index_change[0],dist_point_to_map_center[1] + index_change[1])
            province_map_center = (province_map_center[0] + index_change[0], province_map_center[1] + index_change[1])
            province_file.putpixel(dist_point_to_map_center,(red,bleu,green,255))
            meta_data.seek(0)
            meta_data.truncate(0)
            meta_data.seek(0)
            meta_data.write(f"0,0\n{province_map_center[0]},{province_map_center[1]}\n")
            meta_data.seek(0)
            if point2 is not None:
                line_origin = dist_point_to_map_center
                dist_point_to_map_center = (point2[0] - province_map_center[0], point2[1] - province_map_center[1])
                province_file,index_change1 = iMage_expend(province_file,dist_point_to_map_center)

                dist_point_to_map_center = (dist_point_to_map_center[0] + index_change1[0], dist_point_to_map_center[1] + index_change1[1])
                province_map_center = (province_map_center[0] + index_change1[0],province_map_center[1] + index_change1[1])
                draw = ImageDraw.Draw(province_file)
                draw.line((line_origin[0],line_origin[1],dist_point_to_map_center[0],dist_point_to_map_center[1]),fill=(red,bleu,green,255),width=1)
                meta_data.seek(0)
                meta_data.truncate(0)
                meta_data.seek(0)
                meta_data.write(f"0,0\n{province_map_center[0]},{province_map_center[1]}\n")
                meta_data.seek(0)
            print("metadata_",type(meta_data), repr(meta_data))
            print("province_", type(province_file), repr(province_file))
            self.provinces[f"metadata_{province_id_temporary}"] = meta_data
            self.provinces[f"province_{province_id_temporary}"] = province_file
        else:
            meta_data = StringIO()
            first_write = (0, 0)
            province_file = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            red, green, bleu = extract_rgb_divmod(province_id_temporary)
            province_file.putpixel(xy=first_write,value=(red,green,bleu,255))
            first_line = f"{first_write[0]},{first_write[1]}\n{point1[0]},{point1[1]}\n"
            meta_data.write(first_line)
            meta_data.seek(0)
            self.provinces[f"metadata_{province_id_temporary}"] = meta_data
            self.provinces[f"province_{province_id_temporary}"] = province_file
            print("run")
def province_select(new_id, add_new):
    global province_id, province_id_max
    if add_new:
        province_id_max += 1
        province_id = province_id_max
        print(f"[province_select] Added new province: {province_id}")
    else:
        province_id = new_id
        print(f"[province_select] Selected existing province: {province_id}")
    print(f"[province_select] province_id_max = {province_id_max}")
    return province_id, province_id_max

def extract_rgb_divmod(color_24bit):
    blue = color_24bit % 256
    color_24bit //= 256
    green = color_24bit % 256
    color_24bit //= 256
    red = color_24bit % 256
    return red, green, blue

province_id = 1
province_id_max = 1

class MyDrawWindow(QGraphicsView):
    def __init__(self, map_path):
        super().__init__()
        self.province_id_last = None
        self.mouse_pressed = False
        self.last_paint_pos = None

        print("[MyDrawWindow] Initializing drawing canvas")

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        pixmap = QPixmap(map_path)
        self.original_pixmap = QPixmap(map_path)
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        self.drawing_pixmap = QPixmap(self.original_pixmap.size())
        self.drawing_pixmap.fill(Qt.transparent)
        self.drawing_item = QGraphicsPixmapItem(self.drawing_pixmap)
        self.scene.addItem(self.drawing_item)

        self.fitInView(self.drawing_item, Qt.KeepAspectRatio)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setFocusPolicy(Qt.StrongFocus)

        self.worker = ImageDrawingThread()
        self.worker.start()


    def draw_at_position(self, scene_pos):
        global province_id
        print(f"[draw_at_position] Drawing at scene pos: {scene_pos}")
        if province_id != self.province_id_last:
            self.last_paint_pos = None
            print("[draw_at_position] Province changed, resetting last_paint_pos")
        item_pos = self.pixmap_item.mapFromScene(scene_pos)
        x = int(item_pos.x())
        y = int(item_pos.y())
        painter = QPainter(self.drawing_pixmap)
        red, green, bleu = extract_rgb_divmod(province_id)
        painter.setPen(QPen(QColor(red, green, bleu), 1))
        if self.last_paint_pos and self.last_paint_pos != item_pos:
            painter.drawLine(x, y, int(self.last_paint_pos.x()), int(self.last_paint_pos.y()))
            point2 = (int(self.last_paint_pos.x()), int(self.last_paint_pos.y()))
            print(f"[draw_at_position] Drawing line from {point2} to {(x, y)}")
            self.start_worker((x,y),point2, province_id,"add")
        else:
            painter.drawPoint(x, y)
            print(f"[draw_at_position] Drawing point at {(x, y)}")
            self.start_worker((x,y),None,province_id,"add")
        painter.end()
        self.drawing_item.setPixmap(self.drawing_pixmap)
        self.last_paint_pos = item_pos
        self.province_id_last = province_id

    def start_worker(self, point1, point2,pid,tool):
        drawing_queue.put((point1, point2,pid,tool))

    def on_worker_finished(self, updated_provinces,save):
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = True
            print(f"[mousePressEvent] Mouse pressed at {event.pos()}")
            self.draw_at_position(self.mapToScene(event.pos()))

    def mouseMoveEvent(self, event):
        if self.mouse_pressed:
            print(f"[mouseMoveEvent] Mouse moved to {event.pos()}")
            self.draw_at_position(self.mapToScene(event.pos()))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pressed = False
            print("[mouseReleaseEvent] Mouse released")

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        delta = event.angleDelta().y()
        zoom_factor = zoom_in_factor if delta > 0 else zoom_out_factor
        print(f"[wheelEvent] Zoom {'in' if delta > 0 else 'out'}")
        self.scale(zoom_factor, zoom_factor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            print("[keyPressEvent] Up arrow")
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - 100)
        elif event.key() == Qt.Key_Down:
            print("[keyPressEvent] Down arrow")
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + 100)
        elif event.key() == Qt.Key_Left:
            print("[keyPressEvent] Left arrow")
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - 100)
        elif event.key() == Qt.Key_Right:
            print("[keyPressEvent] Right arrow")
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + 100)
        elif event.key() == Qt.Key_Escape:
            print("[keyPressEvent] Escape key pressed. Closing window.")
            self.parent().close()
        elif event.key() == Qt.Key_R:
            print("[keyPressEvent] Reset view")
            self.resetTransform()
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def get_size(self):
        return self.width()

class province_widget(QWidget):
    def __init__(self):
        super().__init__()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

        self.item = ["province :1"]
        self.list_widget.addItems(self.item)
        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def add_item(self):
        global province_id
        print(f"[province_widget] Adding new province {province_id} to list")
        self.item.append(f"province:{province_id}")
        self.list_widget.clear()
        self.list_widget.addItems(self.item)

    def on_selection_changed(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            item = selected_items[0].text()
            print(f"[province_widget] Selected item: {item}")
            item_split = item.split(":")
            province_select(int(item_split[1]), False)

class setting_widget(QWidget):
    def __init__(self, size):
        super().__init__()
        self.setFixedWidth(size)

        layout = QVBoxLayout()
        self.list_province = province_widget()

        make_new_province_button = QPushButton("new province")
        make_new_province_button.clicked.connect(self.new_province_clicked)
        layout.addWidget(make_new_province_button)

        sea_or_land = QCheckBox("sea province")
        layout.addWidget(sea_or_land)

        layout.addWidget(self.list_province)

        save_button = QPushButton("save")
        save_button.clicked.connect(self.save_file)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def new_province_clicked(self):
        print("[setting_widget] New province button clicked")
        province_select(974, True)
        self.list_province.add_item()
    def save_file(self):
        drawing_queue.put((None,None,None,"save"))
        print("just in case")

class MainWindow(QMainWindow):
    def __init__(self, map_path):
        super().__init__()
        print(f"[MainWindow] Initializing with map: {map_path}")
        self.setWindowTitle("Simple PyQt Window with QGraphicsView Zooming")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        self.draw_widget = MyDrawWindow(map_path)
        size = self.draw_widget.get_size()
        self.leftside = setting_widget(size)

        layout.addWidget(self.leftside)
        layout.addWidget(self.draw_widget)
        self.resize(1920, 1440)

app = QApplication(sys.argv)
map_path = QFileDialog.getOpenFileName(None, "Select Map Image", "", "Images (*.png *.jpg *.bmp)")[0]

if map_path:
    print(f"[main] File selected: {map_path}")
    window = MainWindow(map_path)
    window.show()
    sys.exit(app.exec_())
else:
    print("[main] No file selected. Exiting.")