import matplotlib.pylab as plt
import cv2
import numpy as np

vs = cv2.VideoCapture(0); #deklarasi video

while True:
    _,image = vs.read()
    image = cv2.resize(image,(350,198))
    img_size = (image.shape[1], image.shape[0])

    plt1 = np.float32([[80, 60],
                      [250, 60],
                      [0, 198],
                      [350, 198]])

    plt2 = np.float32([[0, 0],
                      [350, 0],
                      [0, 198],
                      [350, 198]])

    matrix = cv2.getPerspectiveTransform(plt1,plt2)
    new_image = cv2.warpPerspective(image,matrix,img_size)

    plt.subplot(121), plt.imshow(image), plt.title('imput')
    plt.subplot(122), plt.imshow(new_image), plt.title('output')
    plt.show()
    
vs.release()
cv2.destroyAllWindows()
