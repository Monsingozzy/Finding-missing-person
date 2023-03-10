import json
import sys
import base64
import io
from threading import Thread
import cv2
from PIL import Image
import numpy as np
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QListView
from PyQt5.QtWidgets import QMessageBox, QListWidget

from new_case import NewCase
from train_model import train_model
import match_faces
from db_operations import add_to_confirmed, fetch_confirmed_cases, delete_from_pending


class window(QMainWindow):
    """
    This is the main GUI window.
    """
    def __init__(self):
        """
        Title and some other initializations are done here.
        """
        super().__init__()
        self.title = "Missing Person Application"
        self.initialize()

    def initialize(self):
        """
        This method contains all the buttons that are preset on GUI.

        New Case: Whenever a new case has to be registered, this button is used.
        Refresh: This button trains the KNN model. It downloads all the pending cases
                    and trains a KNN model on it.
        Match: This button downloads all the images submitted by the user and
                tries to predict the probability of match. If any match is found then
                it will be printed.
        Confirmed Cases: All cases which have been confirmed will be displayed here.
        """
        self.setWindowTitle(self.title)
        self.setFixedSize(600, 400)

        button_upload = QPushButton("New Case", self)
        button_upload.move(470, 100)
        button_upload.clicked.connect(self.new_case)

        button_refresh_model = QPushButton("Refresh", self)
        button_refresh_model.move(470, 150)
        button_refresh_model.clicked.connect(self.refresh_model)

        button_match = QPushButton("Match", self)
        button_match.move(470, 200)
        button_match.clicked.connect(self.match_from_submitted)

        confirmedButton = QPushButton("Confirmed cases", self)
        confirmedButton.move(470, 250)
        confirmedButton.clicked.connect(self.view_confirmed_cases)

        self.show()

    def new_case(self):
        """
        New case window will open in new GUI.
        """
        self.dialog = NewCase(self)

    def refresh_model(self):
        """
        Model will be trained on this button press.
        All the pending cases will be downloaded from db and
        a KNN Classifier will be trained on it.
        """
        if train_model() is True:
            QMessageBox.about(self, "Success", "Model is trained")
        else:
            QMessageBox.about(self, "Error", "Something went wrong")

    def confirm(self, label, location, image):
        """
        This method will be automatically called whenever any match is found.
        That case will be deleted from pending.
        """
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(img)
        buff = io.BytesIO()
        im_pil.save(buff, format="JPEG")
        img_str = str(base64.b64encode(buff.getvalue()))
        add_to_confirmed(label[0][0], location, img_str)
        delete_from_pending(label[0][0])

    def decode_base64(self, img):
        """
        Image is converted ot numpy array.
        """
        img = img[1:]
        img = np.array(Image.open(io.BytesIO(base64.b64decode(img))))
        return img

    def view_confirmed_cases(self):
        """
        This method will be triggered when the view confirmed button will
        be pressed on GUI.
        """
        result = fetch_confirmed_cases()
        if result is None:
            pass
        else:
            list = QListView(self)
            list.setIconSize(QSize(72, 72))
            list.setMinimumSize(400, 380)
            model = QStandardItemModel(list)
            item = QStandardItem("Confirmed")
            model.appendRow(item)
            for key, value in result.items():
                label_ = str(key).split('@')
                name = label_[0]
                mobile = label_[1]
                father_name = label_[2]
                age = label_[3]
                location = value.get('location', ' ')
                date = value.get('date', ' ')
                image = value.get('image', ' ')
                image = self.decode_base64(image)
                if len(name.split('*')) == 2:
                    name = name.split('*')[0] + " " + name.split('*')[1]
                if len(father_name.split('*')) == 2:
                    father_name = father_name.split('*')[0] + " " + father_name.split('*')[1]  # nopep8

                item = QStandardItem("  Name                   : " + name +
                                     "\n  Father's Name    : " + father_name +
                                     "\n  Age                      : " + age +
                                     "\n  Mobile                 : " + mobile +
                                     "\n  Location             : " + location +
                                     "\n  Date                    : " + date)
                image = QtGui.QImage(image,
                                     image.shape[1],
                                     image.shape[0],
                                     image.shape[1] * 3,
                                     QtGui.QImage.Format_RGB888)
                icon = QPixmap(image)

                item.setIcon(QIcon(icon))
                model.appendRow(item)
            list.setModel(model)
            list.show()

    def match_from_submitted(self):
        """
        This method will be called when match faces button is pressed.
        It download all data from firebase which has been submitted by user
        and runs KNN classifier on it in prediction mode. Any match above 50%
        threshold is shown here.
        """
        result = match_faces.match()
        if result == []:
            QMessageBox.about(self, "No Match Till Now", "Please Pray")
        else:
            list = QListView(self)
            list.setIconSize(QSize(72, 72))
            list.setMinimumSize(400, 380)
            model = QStandardItemModel(list)
            item = QStandardItem("Found")
            model.appendRow(item)

            for person in result:
                label, image, location = person
                label_ = str(label[0][0]).split('@')
                name = label_[0]
                mobile = label_[1]
                father_name = label_[2]
                age = label_[3]

                self.confirm(label, location, image)

                if len(name.split('*')) == 2:
                    name = name.split('*')[0] + " " + name.split('*')[1]
                if len(father_name.split('*')) == 2:
                    father_name = father_name.split('*')[0] + " " + father_name.split('*')[1]  # nopep8

                item = QStandardItem("  Name                   : " + name +
                                     "\n  Father's Name    : " + father_name +
                                     "\n  Age                      : " + age +
                                     "\n  Mobile                 : " + mobile +
                                     "\n  Location             : " + location)
                image = QtGui.QImage(image,
                                     image.shape[1],
                                     image.shape[0],
                                     image.shape[1] * 3,
                                     QtGui.QImage.Format_RGB888)
                icon = QPixmap(image)

                item.setIcon(QIcon(icon))
                model.appendRow(item)
            list.setModel(model)
            list.show()

App = QApplication(sys.argv)
w = window()
sys.exit(App.exec())
