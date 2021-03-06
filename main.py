import os
import sys

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5 import uic


class Map(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)

        self.params = {
            'll': '37.530887,55.703118',
            'spn': '0.002,0.002',
            'l': 'map',
            'size': '650,450'
        }

        self.map_btn.toggled.connect(self.layerChange)
        self.map_btn.setChecked(True)
        self.sat_btn.toggled.connect(self.layerChange)
        self.hyb_btn.toggled.connect(self.layerChange)

        self.post_switch.toggled.connect(self.alter_post)

        self.geocoder_params = {
            'apikey': '40d1649f-0493-4b70-98ba-98533de7710b',
            'geocode': None,
            'format': 'json'
        }

        self.find_button.clicked.connect(self.find_address)
        self.discard_btn.clicked.connect(self.discard_query)

        self.getImage()
        self.show_map()

    def find_address(self):
        self.geocoder_params['geocode'] = self.address_input.text()
        geocoder_response = requests.get('http://geocode-maps.yandex.ru/1.x/', params=self.geocoder_params)

        if not geocoder_response:
            print("Ошибка выполнения запроса:")
            print("Http статус: ", geocoder_response.status_code, " (", geocoder_response.reason, ")", sep='')
            sys.exit(1)

        json_response = geocoder_response.json()
        try:
            toponym = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']

            self.cur_toponym = toponym
            self.params['ll'] = toponym["Point"]["pos"].replace(' ', ',')
            self.params['pt'] = self.params['ll'] + ',pm2rdm'
            toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"].split(', ')
            if self.post_switch.isChecked():
                try:
                    toponym_address.append(f'Почтовый индекс: {toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]}')
                except KeyError:
                    toponym_address.append('Почтовый индекс не найден')
            self.address_output.setText('\n'.join(toponym_address))
            self.getImage()
            self.show_map()
        except IndexError:
            self.address_output.setText("Ничего не найдено.")

    def alter_post(self):
        if self.post_switch.isChecked():
            try:
                new_text = self.address_output.text() + f'\nПочтовый индекс: {self.cur_toponym["metaDataProperty"]["GeocoderMetaData"]["Address"]["postal_code"]}'
            except KeyError:
                new_text = self.address_output.text() + '\nПочтовый индекс не найден'
        else:
            new_text = '\n'.join(self.address_output.text().split('\n')[:-1])
        self.address_output.setText(new_text)

    def getImage(self):
        response = requests.get('http://static-maps.yandex.ru/1.x/', params=self.params)

        if not response:
            print("Ошибка выполнения запроса:")
            print("Http статус: ", response.status_code, " (", response.reason, ")", sep='')
            sys.exit(1)

        self.map_file = "map.png"
        with open(self.map_file, "wb") as f:
            f.write(response.content)

    def show_map(self):
        self.pixmap = QPixmap(self.map_file)
        self.image.setPixmap(self.pixmap)
        self.coords.setText(f'Координаты: {self.params["ll"]}')

    def change_scale_plus(self):
        self.params['spn'] = ','.join(list(map(lambda x: str(float(x) + 0.001)
        if float(x) < 50 else x, self.params['spn'].split(','))))
        self.getImage()
        self.show_map()

    def change_scale_minus(self):
        self.params['spn'] = ','.join(list(map(lambda x: str(float(x) - 0.001)
        if float(x) > 0 else x, self.params['spn'].split(','))))
        self.getImage()
        self.show_map()

    def layerChange(self):
        if self.sender() == self.map_btn:
            self.params['l'] = 'map'
        elif self.sender() == self.sat_btn:
            self.params['l'] = 'sat'
        elif self.sender() == self.hyb_btn:
            self.params['l'] = 'sat,skl'
        self.getImage()
        self.show_map()

    def closeEvent(self, event):
        os.remove(self.map_file)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.move_map(0, 1)
        elif event.key() == Qt.Key_Down:
            self.move_map(0, -1)
        elif event.key() == Qt.Key_Left:
            self.move_map(-1, 0)
        elif event.key() == Qt.Key_Right:
            self.move_map(1, 0)
        elif event.key() == Qt.Key_PageUp:
            self.change_scale_minus()
        elif event.key() == Qt.Key_PageDown:
            self.change_scale_plus()

    def discard_query(self):
        self.params['pt'] = ''
        self.cur_toponym = None
        self.address_output.setText('Полный адрес')
        self.getImage()
        self.show_map()

    def move_map(self, x, y):
        x_shift = float(self.params['spn'].split(',')[0]) * x
        y_shift = float(self.params['spn'].split(',')[1]) * y
        new_ll = self.params['ll'].split(',')
        new_ll[0] = float(new_ll[0]) + x_shift
        new_ll[1] = float(new_ll[1]) + y_shift
        self.params['ll'] = ','.join(map(str, new_ll))
        self.getImage()
        self.show_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pr = Map()
    pr.show()
    sys.exit(app.exec())
