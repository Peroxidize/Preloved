from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt5.QtGui import QPixmap
from PIL import Image
import io
import sys
from models.migrations.image_transformer import download_image, VGGFeatureExtractor
from models.services import query_database
def display_image_in_ui(image_binary):
    # Convert binary data to a PIL image
    image = Image.open(io.BytesIO(image_binary))

    # Convert the PIL image to a format Qt can use (save to a temporary file)
    image_path = "temp_image.png"
    image.save(image_path)

    # Create a Qt Application
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Image Viewer")

    # Create a label to display the image
    label = QLabel(window)
    pixmap = QPixmap(image_path)
    label.setPixmap(pixmap)
    window.setCentralWidget(label)

    # Show the window
    window.resize(800, 600)  # Set the window size
    window.show()
    sys.exit(app.exec_())

# Example usage:
img =download_image('users/seller@gmail.com/usercontent/item_images/Blouse_Floral_Printed.webp')
img2=download_image("users/seller@gmail.com/usercontent/item_images/12K_90s_Nike_Swoosh_Nylon_blokecore_Style_Track_Light_Jacket.jpg")
#display_image_in_ui(img)
extractor = VGGFeatureExtractor()
print('logging')
print(extractor.extract_features(img).shape)
print(extractor.extract_features(img2).shape)

from models.services import add_vector_to_database


add_vector_to_database(1, extractor.extract_features(img))
add_vector_to_database(2, extractor.extract_features(img2))

rep = {
    2:img2,
    1:img
}

result = download_image("users/seller4@gmail.com/usercontent/item_images/Lilly_Pulitzer.png")
result = query_database(extractor.extract_features(result), 1)[0]

display_image_in_ui(rep[int(result)])


