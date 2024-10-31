import cv2 
import numpy as np
# import pandas as pd 
# import seaborn as sns
from numpy import sin,cos
import matplotlib.pyplot as plt 

# file_path = './data/test.mp4'
# file_path = './data/AB3-1.avi'
# file_path = './data/img/img_69.jpg'
file_path = './data/img/img_127.jpg'
file_path2 = './data/img/img_173.jpg'
# 有 二值化過的圖片結果會比較好, 至少看起來知道是什麼

b_ellipsefit = False
b_drawContour = True
b_canny = False
b_fft = True
# 
def find_contour(img,thres_img):
	contours , hierachy = cv2.findContours(thres_img,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
	cnt_img = cv2.drawContours(img,contours,-1,(0,0,255),3)
	return contours

def from_img(file):
	img = cv2.imread(file)
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	height , width = gray.shape
	df_Matrix = np.zeros((height,width)) 
	ret , thres_img = cv2.threshold(gray,210,255,cv2.THRESH_BINARY)
	
	if b_drawContour and ret:
		cnt = find_contour(thres_img,thres_img)	

	if b_ellipsefit:
		ellipse = cv2.fitEllipse(cnt[0])
		cx,cy = int(ellipse[0][0]), int(ellipse[0][1])
		dx ,dy = cx + int(ellipse[1][1]*0.5*sin(ellipse[2]*np.pi/180)) , cy - int(ellipse[1][1]*0.5*cos(ellipse[2]*np.pi/180))

		cv2.ellipse(img,ellipse,(0,0,255),3)
		cv2.arrowedLine(img,(cx,cy) ,(dx,dy),(0,255,0),1)
		cv2.imshow('contour',img)
		cv2.waitKey(0)

	if b_fft:
		img_fft = cv2.dft(np.float64(gray),flags=cv2.DFT_COMPLEX_OUTPUT)
		img_fft_shift = np.fft.fftshift(img_fft)
		rows, cols,_ = img.shape
		crow, ccol = rows//2 , cols //2
		mask = np.zeros((rows,cols,2),np.uint8)
		for i in range(crow):
			for j in range(ccol):
				if i**2+ j**2 <= min(rows,cols)**2:
					mask[i,j] = 1 
		# mask[crow-100:crow+100,ccol-100:ccol+100] = 1
		dft_shift_mask = img_fft_shift*mask
		img_dft = np.fft.ifftshift(dft_shift_mask)
		img_back = cv2.idft(img_dft)
		
		
		# cv2.imshow('fft image',img_back)
		# cv2.waitKey(0)


	if b_canny:
		img_cc = img.copy()[:,:,0]
		img_cc = cv2.medianBlur(img_cc, 7) 
		edge = cv2.Canny(image=img_cc,threshold1=20,threshold2=80)
		# masked = cv2.bitwise_or(img_cc.copy(),edge)
		# print(img.shape,gray.shape,edge.shape)
		# cnt_img = cv2.drawContours(gray,edge,-1,(0,0,255),3) 
		# draw contour
		# 第一個arg. image 矩陣
		# 第二個arg. contour 矩陣
		# 第三個arg. 要繪製第幾個contour，如果有圈到很多區域，就會有這個問題。 如果需要全部的區域都繪製，就輸入-1
		# 第四個arg. 線的顏色 (g,b,r)
		# 第五個arg. 線的粗細 

		cv2.imshow('edge',edge)
		cv2.waitKey(0)

	# df_Matrix += thres_img
	# return thres_img
	return img_back
	

def from_video(file):
	cap = cv2.VideoCapture(file)
	width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
	height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
	df_Matrix = np.zeros((height,width))
	frame_count = 0
	while cap.isOpened():
		ret , frame = cap.read()
		if not ret :
			break
		gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)	
		_, thres_img = cv2.threshold(gray,130,255,cv2.THRESH_BINARY)
		if b_drawContour:
			# cnt = find_contour(frame,thres_img)
			cnt , _ = cv2.findContours(thres_img,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
			cv2.drawContours(frame,cnt,-1,(0,0,255),2)
			cv2.imshow('img',frame)
			
		if b_ellipsefit:
			# if (cnt[0].size > 5):
			ellipse = cv2.fitEllipse(cnt[0])
			cx,cy = int(ellipse[0][0]), int(ellipse[0][1])
			dx ,dy = cx + int(ellipse[1][1]*0.5*sin(ellipse[2]*np.pi/180)) , cy - int(ellipse[1][1]*0.5*cos(ellipse[2]*np.pi/180))

			cv2.ellipse(thres_img,ellipse,(0,0,255),3)
			cv2.arrowedLine(thres_img,(cx,cy) ,(dx,dy),(0,255,0),1)
			cv2.imshow('contour',thres_img)
		
		df_Matrix += thres_img
		frame_count += 1
	
	cv2.waitKey(0)
	cap.release()	

	IMG_Matrix = df_Matrix / frame_count
	return IMG_Matrix


# test for video 
# df_Matrix = from_video(file_path)
# 
# test for img 
df_Matrix = from_img(file_path)
# print(df_Matrix.shape)

df2 = from_img(file_path2)

while(1):
	# cv2.imshow('thres image',df_Matrix[:,:,0])
	# gray_stack = np.hstack((df_Matrix[:,:,0],df_Matrix[:,:,1]))
	gray_stack = np.hstack((df_Matrix[:,:,0],df2[:,:,0]))
	cv2.imshow('thres image',gray_stack)
	k = cv2.waitKey(1)
	if k == 27:
		break
	elif k==-1:
		continue
	else :
		print(k)

		
# df = pd.DataFrame(df_Matrix)
# sns.heatmap(df,vmin=0, vmax=15 ,square=True)
# plt.savefig('heatmap.png')
# plt.show()
