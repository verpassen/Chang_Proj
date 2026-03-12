import sys
from PyQt5.QtWidgets import * 
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class myfun(QWidget):
		def __init__(self):
			super(myfun, self).__init__()
			self.initUi()
			
		def initUi(self):
			path = './'
			# model = QDirModel()
			model = QFileSystemModel()
			model.setRootPath(path)
			mytree = QTreeView(self)
			mytree.setModel(model)
			mytree.setRootIndex(model.index(path))
			self.setWindowTitle('QTreeView')
			mytree.resize(600,400)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = myfun()
	ex.show()
	sys.exit(app.exec_())