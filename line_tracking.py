import numpy as np
import time
import cv2
import pyfirmata

vs = cv2.VideoCapture(0); #deklarasi video

board = pyfirmata.Arduino('/dev/ttyACM0')
pin9 = board.get_pin('d:9:p') #servo
pin10 = board.get_pin('d:10:p') #esc
pin10.write(0.7)
pin9.write(0.4)
time.sleep(3.5)

while True:
    _,fram = vs.read() #memulai video
    frame = cv2.resize(fram,(350,198)) #resize pake opencv 
    img_size = (frame.shape[1], frame.shape[0]) #ukuran gambar, 1 untuk lebar dan 0 untuk tinggi
    
    src = np.float32([[55, 135], 
                      [340, 135],
                      [0, 200],
                      [400, 200]]) #dikertas (pakai pixel_detec.py)

    dst = np.float32([[0, 0],
                      [400, 0],
                      [20, 225],
                      [380, 225]]) #disesuaikan sama fullfix, diganti dlu

    matrix = cv2.getPerspectiveTransform(src, dst) #ngerubah sudut pandang frame jdi kek diatas
    atas = cv2.warpPerspective(frame, matrix, img_size) #pengaplikasian pada gambar yg diambil
    
    hls = cv2.cvtColor(atas, cv2.COLOR_BGR2HLS)
    lower_white = np.array([0, 152, 0]) ##cek raspi bgr_color
    upper_white = np.array([255, 255, 255]) #batas seperti biasa
    mask = cv2.inRange(hls, lower_white, upper_white) #diambil yg warna putih aja
    hls_result = cv2.bitwise_and(atas, atas, mask = mask) #dri yg warna putih diatas dibandingin sama aslinya, trus bisa dilihat warna yg bener2 diambil, karna putih intensitasnya tidak sama
    gray = cv2.cvtColor(hls_result, cv2.COLOR_BGR2GRAY)
    ret, binary_warped = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    blur = cv2.GaussianBlur(binary_warped,(1, 1), 0)
    canny = cv2.Canny(blur, 20, 180) #garis tepi

    histogram = np.sum(canny[canny.shape[0] // 2:, :], axis = 0) #nilai tinggi 225 dari [0] yg dibagi 2 tingginya [0] yg terbaca tengah ke bawah (lihat dikertas)
    midpoint = np.int(histogram.shape[0] / 2) #400/2 aja, 0 bukan berarti tinggi karna ini hanya 1 bidang, lebar saja
    left_base = np.argmax(histogram[:midpoint]) #melihat nilai terbesar terletak di sebelah mana yang terdekat dari sebelah kiri 0-200 (bisa buat penyempitan jalan)
    right_base = np.argmax(histogram[midpoint:]) + midpoint #sama kayak atas, jdi diurut dri 200-400 dan lihat yg terbesar, tpi rangenya tetep 0-200, karna 400 dibagi 2 kanan dan kiri 
    
    nframing = 9 #pembaginya 9
    tinggi_framing = np.int(canny.shape[0] / nframing) #tinggi setiap framenya 225/9 = 25
    nonzero = canny.nonzero() #cek di coba.py
    nonzeroy = np.array(nonzero[0]) #untuk tinggi
    nonzerox = np.array(nonzero[1]) #untuk lebar
    
    left = left_base
    right = right_base
    
    margin = 20 #kekiri kanannnya dari garis marka
    minpix = 15 #nilai untuk menentukan perbandingan dari panjangnya jumlah data yg didapat dari good_left (lihat di catetan)
    
    left_lane = [] #rumah untuk array
    right_lane = [] #jadi array yang masuk ga langsung ilang
    
    for framing in range(nframing): #perulangan for
        frm_y_high = canny.shape[0] - (framing + 1) * tinggi_framing #kotak bagian atasnya
        frm_y_low = canny.shape[0] - framing * tinggi_framing #bagian bawahnya
        frm_xleft_low = left - margin #kiri untuk kiri
        frm_xleft_high = left + margin #kiri unruk kanan
        frm_xright_low = right - margin #kanan untuk kiri
        frm_xright_high = right + margin #kanan untuk kanan
        
        kotak_kiri = cv2.rectangle(atas, (frm_xleft_low, frm_y_high), (frm_xleft_high, frm_y_low),(0,0,255), 2) #buat kotak dari itungan diats jalur kiri
        kotak_kanan = cv2.rectangle(atas, (frm_xright_low, frm_y_high), (frm_xright_high, frm_y_low),(0,255,0), 2) #jalur kanan, ututan warnanya BGR
        good_left = ((nonzeroy >= frm_y_high) & (nonzeroy < frm_y_low) & (nonzerox >= frm_xleft_low) & (nonzerox < frm_xleft_high)).nonzero()[0] #buat kotakan , jdi intinya nilai2 didalam kotak framenya, untuk kiri
        good_right = ((nonzeroy >= frm_y_high) & (nonzeroy < frm_y_low) & (nonzerox >= frm_xright_low) & (nonzerox < frm_xright_high)).nonzero()[0] #buat kotakan , jdi intinya nilai2 didalam kotak framenya, untuk kanan
        
        left_lane.append(good_left) #menambahkan array good_left ke rumah array diatas untuk bagian gambar kiri
        right_lane.append(good_right) #menambahkan array good_left ke rumah array diatas untuk bagian gambar kanan
        
        cv2.imshow('hasil tracking',kotak_kiri) #menampilkan hasil tracking 
        
        if len(good_left) > minpix: #ngotakinnya turun, jdi klo kondisinya ga terpenuhi makaa letak kotak akan sama seperti diatasnya
            left = np.int(np.mean(nonzerox[good_left]))

        if len(good_right) > minpix:
            right = np.int(np.mean(nonzerox[good_right]))
            
    left_lane = np.concatenate(left_lane) #menyatukan beberapa array
    right_lane = np.concatenate(right_lane)
            
    leftx = nonzerox[left_lane] #mencari yg bukan 0
    lefty = nonzeroy[left_lane]
    rightx = nonzerox[right_lane]
    righty = nonzeroy[right_lane]

    try:
        if rightx[0] - rightx[-1] > 15:
            if rightx[0]<300:
                curve_direction = 'kiri banyak'
                pin10.write(0.63)
                pin9.write(0.69)
            else :
                curve_direction = 'kiri dikit'
                pin10.write(0.65)
                pin9.write(0.5)
        elif rightx[0] - rightx[-1] < -25:
            if rightx[0]>310 :
                curve_direction = 'kanan banyak'
                pin10.write(0.63)
                pin9.write(0.23)
            else :
                curve_direction = 'kanan dikit'
                pin10.write(0.65)
                pin9.write(0.35)
        else:
            if rightx[0]>320:
                curve_direction = 'lurus belok kanan'
                pin10.write(0.65)
                pin9.write(0.35)
            elif rightx[0]<295:
                curve_direction = 'lurus belok kiri'
                pin10.write(0.65)
                pin9.write(0.47)
            else:
                curve_direction = 'lurus'
                pin10.write(0.65)
                pin9.write(0.42)
    except:
        curve_direction = "stop"
        pin10.write(0.7)
        pin9.write(0.4)
    print(curve_direction)
    key = cv2.waitKey(1)
    if key == 27:
        break
vs.release()
cv2.destroyAllWindows()
