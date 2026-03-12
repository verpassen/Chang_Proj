from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys, json, os
import cv2, time
import pandas as pd 
import pyqtgraph as pg 
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('Load_video.ui', self)
        self.init_ui()

    def init_ui(self):
        # Initialize parameters
        self.b_exportImg = True
        self._imgratio = 214 # 214 pixel/mm 
        self._ThresVal = 120
        self.current_frame = None
        self.threshold_frame = None
        self.Meltpool = {'timestamp': [],'radius': [], 'Cent_x': [], 'Cent_y': [], 'Area': [], 
                         'Hu1':[],'Hu2':[],'Hu3':[],'Hu4':[],'Hu5':[],'Hu6': [],'Hu7':[]
                         }
        # self.processing_queue = []
        
        # Connect buttons
        self.LoadBtn.clicked.connect(self.LoadVideo)
        self.SaveBtn.clicked.connect(self.DataExport)
        self.ImgExport_checkBox.stateChanged.connect(self.Exp_Img)
        self.ImgRatioSlider.valueChanged.connect(self.updateRatio)
        self.ThresSlider.valueChanged.connect(self.updateThres)
        self.PlayPauseBtn.clicked.connect(self.toggle_play_pause)
        self.FrameRateSpinBox.valueChanged.connect(self.update_playback_speed)
        if hasattr(self, 'CloseBtn'):
            self.CloseBtn.clicked.connect(self.close)
        
        # Initialize worker thread
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)  # Limit thread count
        
        # Video playback control
        self.is_playing = False
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        # Initialize the GraphicsView for plotting
        self.setup_graph()
        
        # Setup progress reporting
        self.progressBar.setValue(0)


    def setup_graph(self):
        # Initialize the graph for visualizing melt pool radius over time
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        self.graph = pg.PlotWidget()
        self.graph.setYRange(0, 5)
        plot = self.graph.getPlotItem()
        plot.setLabel('left', 'Melt Pool width', units='mm')
        plot.setLabel('bottom', 'Time', units='sec')
        self.plot = self.graph.plot(pen=pg.mkPen(color=(0, 150, 255), width=2))
        self.graph.resize(780, 210)
        self.graph.showGrid(x=True, y=True)
        self.graphicsView.fitInView(scene.sceneRect())
        scene.addWidget(self.graph)

    def Exp_Img(self):
        foldername = '\\data\\img'
        cur_path = os.path.dirname(__file__)
        full_path = cur_path + foldername   
        if self.ImgExport_checkBox.isChecked():
            try: 
                self.b_exportImg = True
                print('image box is checked')
                os.makedirs(full_path)
                os.makedirs( cur_path + '\\data\\thresImg')
                print(f'creat a new folder "{full_path}"')
            except FileExistsError:
                print('the folders already exists!')
        else:
            self.b_exportImg = False
            print('image box is unchecked')

    def init_Meltpooldata(self):
        self.Meltpool = {'timestamp': [],'radius': [], 'Cent_x': [], 'Cent_y': [], 'Area': [], 
                         'Hu1':[],'Hu2':[],'Hu3':[],'Hu4':[],'Hu5':[],'Hu6': [],'Hu7':[]
                         }
        
    def LoadVideo(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', './Video/', 'Video Files (*.mp4 *.avi *.mov *.wmv)')
        if not filename:
            return
        
        # Reset data
        for key in self.Meltpool:
            self.Meltpool[key] = []
        
        self.cap = cv2.VideoCapture(filename)
        if not self.cap.isOpened():
            QMessageBox.critical(self, 'Error', 'Could not open video file')
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.FrameRateSpinBox.setValue(int(self.fps))
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.progressBar.setMaximum(self.total_frames)
        self.start_playback()
        self.ImgExport_checkBox.setEnabled(False)

    def start_playback(self):
        self.is_playing = True
        self.PlayPauseBtn.setText("Pause")
        playback_rate = self.FrameRateSpinBox.value()
        self.timer.start(1000 // playback_rate)

    def update_playback_speed(self):
        if self.is_playing:
            playback_rate = self.FrameRateSpinBox.value()
            self.timer.start(1000 // playback_rate)

    def toggle_play_pause(self):
        # 如果影片還沒撥放，什麼都沒事
        if self.cap is None:
            return
        # 如果影片已經撥放，暫停
        # 如果影片已經播完了，重播    
        if self.is_playing:
            self.timer.stop()
            self.PlayPauseBtn.setText("Play")
        else:
            if self.cap.get(cv2.CAP_PROP_POS_FRAMES) == self.total_frames:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.init_Meltpooldata()
            playback_rate = self.FrameRateSpinBox.value()
            self.timer.start(1000 // playback_rate)
            self.PlayPauseBtn.setText("Pause")
        self.is_playing = not self.is_playing
        self.setup_graph()

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, self.threshold_frame = cv2.threshold(self.current_frame, self._ThresVal, 255, cv2.THRESH_BINARY)
            self.idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.updateImage()
            
            # Update progress bar
            selfidx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.progressBar.setValue(self.idx)
            
            # Process frame using worker thread
            current_time = self.idx / self.fps
            self.process_frame_async(self.threshold_frame, current_time)
            
            # Update live plot if we have data
            # if len(self.Meltpool['radius']) > 0 and len(self.Meltpool['timestamp']) > 0:
            #     self.update_plot()

            self.update_plot()    
        else:
            self.timer.stop()
            self.is_playing = False
            self.PlayPauseBtn.setText("Replay")
            QMessageBox.information(self, 'Info', 'Video playback completed')
            self.ImgExport_checkBox.setEnabled(True)


    def updateRatio(self):
        self._imgratio = self.ImgRatioSlider.value()
        if self.current_frame is not None:
            self.updateImage()

    def updateThres(self):
        self._ThresVal = self.ThresSlider.value()
        if self.current_frame is not None:
            _, self.threshold_frame = cv2.threshold(self.current_frame, self._ThresVal, 255, cv2.THRESH_BINARY)
            self.updateImage()

    def updateImage(self):
        if self.current_frame is None:
            return
        ratio = self.ImgRatioSlider.value() / 100
        
        # Update original image
        cropped = self.cropedimage(self.current_frame, ratio)
        resized = cv2.resize(cropped, (self.OrgImg.width(), self.OrgImg.height()))
        q_img = QImage(resized.data, resized.shape[1], resized.shape[0], resized.strides[0], QImage.Format_Grayscale8)
        self.OrgImg.setPixmap(QPixmap.fromImage(q_img))
        
        # Update threshold image
        cropped_thres = self.cropedimage(self.threshold_frame, ratio)
        resized_thres = cv2.resize(cropped_thres, (self.GrayImg.width(), self.GrayImg.height()))
        ThresQtFormat = QImage(resized_thres.data, resized_thres.shape[1], resized_thres.shape[0], 
                              resized_thres.strides[0], QImage.Format_Grayscale8)
        self.GrayImg.setPixmap(QPixmap.fromImage(ThresQtFormat))
        
        
        if self.b_exportImg:
            cv2.imwrite(f'.\\data\\img\\{self.idx}.jpg',cropped)
            cv2.imwrite(f'.\\data\\thresImg\\{self.idx}.jpg',cropped_thres)
 
    def process_frame_async(self, threshold_image, timestamp):
        # Create a worker and run it in a separate thread
        worker = MeltPoolWorker(threshold_image.copy(), self._imgratio)
        worker.signals.result.connect(lambda result: self.process_worker_result(result, timestamp))
        self.thread_pool.start(worker)

    def process_worker_result(self, result, timestamp):
        if result:
            # Update UI
            self.MeltWidthLbl.setText(f"{result['radius']:.2f}")
            self.CentXLbl.setText(f"{result['Cent_x']:.2f}")
            self.CentYLbl.setText(f"{result['Cent_y']:.2f}")
            
            # Update data
            self.Meltpool['radius'].append(result['radius'])
            self.Meltpool['Cent_x'].append(result['Cent_x'])
            self.Meltpool['Cent_y'].append(result['Cent_y'])
            self.Meltpool['Area'].append(result['Area'])
            self.Meltpool['timestamp'].append(timestamp)
            
            # Update Hu moments
            for i in range(7):
                self.Meltpool[f'Hu{i+1}'].append(result['Hu'][i])
            
            # Update plot
            self.update_plot()

    def update_plot(self):
        if len(self.Meltpool['radius']) > 0 and len(self.Meltpool['timestamp']) > 0:
            # Plot radius vs time
            self.plot.setData(
                x=self.Meltpool['timestamp'], 
                y=self.Meltpool['radius']
            )
 
    def DataExport(self):
        if not self.Meltpool['radius']:
            QMessageBox.warning(self, 'Warning', 'No data to export')
            return
        
        # Create a preview of the data
        preview_data = {}
        for key in self.Meltpool:
            if len(self.Meltpool[key]) > 0:
                preview_data[key] = self.Meltpool[key][:10]  # Show first 10 entries
        
        preview = json.dumps(preview_data, indent=2)
        
        # Show preview dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Data Preview")
        preview_dialog.resize(500, 400)
        layout = QVBoxLayout()
        
        # Add status label
        status_label = QLabel(f"Total frames processed: {len(self.Meltpool['radius'])}")
        layout.addWidget(status_label)
        
        # Add preview text
        text_edit = QTextEdit()
        text_edit.setPlainText(preview)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        # Add export buttons
        button_layout = QHBoxLayout()
        export_json_button = QPushButton("Export JSON")
        export_json_button.clicked.connect(lambda: self.export_json(preview_dialog))
        export_csv_button = QPushButton("Export CSV")
        export_csv_button.clicked.connect(lambda: self.export_csv(preview_dialog))
   
        button_layout.addWidget(export_json_button)
        button_layout.addWidget(export_csv_button)
        layout.addLayout(button_layout)
        
        preview_dialog.setLayout(layout)
        preview_dialog.exec_()

    def export_json(self, dialog):
        saveName, _ = QFileDialog.getSaveFileName(self, 'Save JSON file', 'meltpool_data.json', 'JSON Files(*.json)')
        if saveName:
            with open(saveName, 'w') as f:
                json.dump(self.Meltpool, f, indent=2)
            QMessageBox.information(self, 'Info', f'File saved successfully to {saveName}')
            dialog.accept()

    def export_csv(self, dialog): 
        saveName, _ = QFileDialog.getSaveFileName(self, 'Save csv file', 'meltpool_data.csv', 'CSV Files(*.csv)')
        if saveName:
            pd.DataFrame(self.Meltpool).to_csv(saveName,index=False)
            QMessageBox.information(self, 'Info', f'File saved successfully to {saveName}')
            dialog.accept()
    
    def cropedimage(self, image, ratio):
        h, w = image.shape[:2]
        n_h, n_w = int(ratio * h), int(ratio * w)
        self.img_height.setText(str(n_h))
        self.img_width.setText(str(n_w))
        start_x, start_y = (w - n_w) // 2, (h - n_h) // 2
        end_x, end_y = start_x + n_w, start_y + n_h
        return image[start_y:end_y, start_x:end_x]

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        self.thread_pool.clear()
        super().closeEvent(event)

# Worker signals class
class WorkerSignals(QObject):
    result = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)

# MeltPool worker for threaded processing
class MeltPoolWorker(QRunnable):
    def __init__(self, image, imageratio):
        super().__init__()
        self.image = image
        self._imgratio = imageratio
        self.signals = WorkerSignals()
        
    def run(self):
        try:
            result = self.area_calc(self.image)
            if result:
                self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()
    
    def area_calc(self, image):
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # default values 
        cent_x , cent_y = 0, 0 
        area = 0 
        cal_rad = 0 
        result_Hu = np.zeros(7)
        if contours and len(contours) > 0 :
            max_c = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(max_c)
            M = cv2.moments(max_c)
            if M['m00'] > 100:
                cent_x = M['m10'] / M['m00']
                cent_y = M['m01'] / M['m00']
                cal_rad = round(np.sqrt(4 * M['m00'] / np.pi), 3) / self._imgratio
                Hu = cv2.HuMoments(M).flatten()
                result_Hu = -np.log10(abs(Hu) + 1e-10) * np.copysign(1, Hu)
            
        return {'radius': cal_rad, 'Cent_x': cent_x, 'Cent_y': cent_y, 'Area': area,'Hu': result_Hu }        
         

if __name__ == '__main__':
    App = QApplication(sys.argv)
    Root = MainWindow()
    Root.show()
    sys.exit(App.exec_())