from PyQt5.QtGui import QImage, QPixmap
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot, QTimer, QDate, Qt
from PyQt5.QtWidgets import QDialog, QMessageBox
import cv2
import face_recognition
import numpy as np
import datetime
import os
import sys
import os.path
from cryptography.fernet import Fernet


class UiDialog(QDialog):
    def __init__(self):
        super(UiDialog, self).__init__()
        loadUi("./main.ui", self)

        #Update Time and Date
        now = QDate.currentDate()
        currentDate = now.toString('dd MMM yyyy')
        currentTime = datetime.datetime.now().strftime("%I:%M %p")

        self.lblDate2.setText(currentDate)
        self.lblTime2.setText(currentTime)
        self.image = None

        #Button for opening folder of attendance.csv
        self.btnOpenFile.clicked.connect(self.fileOpen)

        #Button to generate encryption key
        self.btnKeyGen.clicked.connect(self.genKey)

        #Button to start the encryption of attendance file
        self.btnEncrypt.clicked.connect(self.encryptF)

        #Button to decrypt attendance file
        self.btnDecrypt.clicked.connect(self.decryptF)

        #Exit button
        self.btnExit.clicked.connect(self.appExit)


    #open files to stored Data
    def fileOpen(self):
        os.startfile(r'E:\Uni Doc\FYP\Applic')

    def appExit(self):
        sys.exit()

#generate a encryption key
    def genKey(self):
        key = Fernet.generate_key()
        with open('encrypt.key','wb') as enckey:
            enckey.write(key)
        print('key generated')

#encryption of attendance.csv
    def encryptF(self):
        # initialize existance of files
        fileKey = os.path.exists('encrypt.key')
        fileDoc = os.path.exists('attendance.csv')
        # error checking before encryption
        if fileDoc and fileKey == True:
            key = open('encrypt.key', 'rb').read()
            filename = 'attendance.csv'
            f= Fernet(key)
            with open(filename, 'rb') as file:
                fileData = file.read()
            encryptedData = f.encrypt(fileData)
            with open(filename, 'wb') as file:
                file.write(encryptedData)
            print('file has been encrypt')
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Please ensure a encryption key and attendance.csv file exist")
            msg.exec_()



#decryption of attendance.csv
    def decryptF(filename, key):
        #initialize existance of files
        fileKey = os.path.exists('encrypt.key')
        fileDoc = os.path.exists('attendance.csv')
        #error checking before decryption
        if fileDoc and fileKey == True:
            key = open('encrypt.key', 'rb').read()
            filename = 'attendance.csv'
            f = Fernet(key)
            with open(filename, 'rb') as file:
                encryptedData = file.read()
            decryptedData = f.decrypt(encryptedData)
            with open(filename, 'wb') as file:
                file.write(decryptedData)
            print('file has been decrypt')
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Please ensure a decryption key and attendance.csv file exist")
            msg.exec_()



    @pyqtSlot()
    def startVideo(self, camera):
        """
        :param camera_name: link of camera or usb camera
        :return:
        """
        if len(camera) == 1:
        	self.capture = cv2.VideoCapture(int(camera))
        else:
        	self.capture = cv2.VideoCapture(camera)
        self.timer = QTimer(self)  # Create Timer
        path = 'images'
        if not os.path.exists(path):
            os.mkdir(path)
        # known face encoding and known face name list
        images = []
        self.class_names = []
        self.encode_list = []
        self.timeList = []
        self.timeList2 = []
        attendance_list = os.listdir(path)
        # print(attendance_list)
        for cl in attendance_list:
            cur_img = cv2.imread(f'{path}/{cl}')
            images.append(cur_img)
            self.class_names.append(os.path.splitext(cl)[0])
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(img)
            encodes_cur_frame = face_recognition.face_encodings(img, boxes)[0]
            # encode = face_recognition.face_encodings(img)[0]
            self.encode_list.append(encodes_cur_frame)
        self.timer.timeout.connect(self.update_frame)  # Connect timeout to the output function
        self.timer.start(40)  # emit the timeout() signal at x=40ms

    def face_rec_(self, frame, encode_list_known, class_names):
        """
        :param frame: frame from camera
        :param encode_list_known: known face encoding
        :param class_names: known face names
        :return:
        """
        # csv
        def mark_attendance(name):
            """
            :param name: detected face known or unknown one
            :return:
            """
            if self.btnTakeAttd.isChecked():
                self.btnTakeAttd.setEnabled(False)
                with open('attendance.csv', 'a') as f:
                    if (name != 'unknown'):
                        buttonReply = QMessageBox.question(self, 'Taking Attendance for' + name, 'Confirm?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        if buttonReply == QMessageBox.Yes:
                            date_time_string = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
                            f.writelines(f'\n{name},{date_time_string},Attendance Taken')
                            self.btnTakeAttd.setChecked(False)

                            self.lblName2.setText(name)
                            self.lblStatus2.setText('Attendance Taken')

                            self.Time1 = datetime.datetime.now()

                            self.btnTakeAttd.setEnabled(True)
                        else:
                            print('Attendance Not Taken')
                            self.btnTakeAttd.setEnabled(True)

        # face recognition
        faces_cur_frame = face_recognition.face_locations(frame)
        encodes_cur_frame = face_recognition.face_encodings(frame, faces_cur_frame)
        # count = 0
        for encodeFace, faceLoc in zip(encodes_cur_frame, faces_cur_frame):
            match = face_recognition.compare_faces(encode_list_known, encodeFace, tolerance=0.50)
            face_dis = face_recognition.face_distance(encode_list_known, encodeFace)
            name = "unknown"
            best_match_index = np.argmin(face_dis)
            # print("s",best_match_index)
            if match[best_match_index]:
                name = class_names[best_match_index].upper()
                y1, x2, y2, x1 = faceLoc
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            mark_attendance(name)
        return frame

    def update_frame(self):
        ret, self.image = self.capture.read()
        self.displayImage(self.image, self.encode_list, self.class_names, 1)

    def displayImage(self, image, encode_list, class_names, window=1):
        """
        :param image: frame from camera
        :param encode_list: known face encoding list
        :param class_names: known face names
        :param window: number of window
        :return:
        """
        image = cv2.resize(image, (640, 480))
        try:
            image = self.face_rec_(image, encode_list, class_names)
        except Exception as e:
            print(e)
        qformat = QImage.Format_Indexed8
        if len(image.shape) == 3:
            if image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(image, image.shape[1], image.shape[0], image.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)
