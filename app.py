from flask import Flask, render_template, request, redirect, url_for, g,abort
from PIL import Image
import os
from werkzeug.utils import secure_filename
import numpy as np
from forms import MyForm,FloatForm
import matplotlib.pyplot as plt
import tkinter as tk

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'upload'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LdugDwmAAAAADXAM0stMt2dfH0RfU7oF5RQH1Tk'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LdugDwmAAAAAC2IMPVgMu-SwxU9uY_EtW-JNy5r'
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}


@app.route('/protected')
def protected():
    # Проверяем, решена ли reCAPTCHA
    if request.args.get('captcha') == 'solved':
        return redirect(url_for('image', captcha='solved'))
    if request.args.get('captcha') == 'unsolved':
        return "Captcha not succed"
    return abort(403)

@app.route('/', methods=['GET', 'POST'])
def submit():
    form = MyForm()
    if form.validate_on_submit():
        return redirect(url_for('protected', captcha='solved'))

    return render_template('index.html', form=form)

@app.route('/image', methods=['GET'])
def image():
    form = FloatForm()
    return render_template('upload-image.html',form=form)

@app.route('/image/upload', methods=['GET','POST'])
def upload():
    # Получаем загруженный файл из формы
    file = request.files['image']
    form = FloatForm()
    # Проверяем, что файл существует и имеет разрешенное расширение
    if file and allowed_file(file.filename):
        # Сохраняем файл на сервере
        number = form.float_number.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Выполняем необходимые операции с изображением
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        image_changed_path = "static/changed"
        # Обработка изображения
        resize_image(image_path, filename, image_changed_path, scale=number)
        graname = filename.split('.')[0] + "_graph.png"
        plot_color_distribution(image_path, graname)
        return render_template("changed_image.html", filename=filename, graph_name=graname)
    else:
        return 'Недопустимый файл'

def allowed_file(filename):
    # Проверяем разрешенные расширения файлов
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, file_name, image_folder,scale):
    image = Image.open(image_path)

    old_size = image.size
    new_size = (int(old_size[0] * scale), int(old_size[1] * scale))
    resized_image = image.resize(new_size)
    resized_image.save(f"{image_folder}/resized_{file_name}")


def plot_color_distribution(image_path,name):
    # Загрузка изображения с помощью Pillow
    image = Image.open(image_path)

    # Преобразование изображения в массив NumPy
    image_array = np.array(image)

    # Получение гистограммы распределения цветов по каналам
    red_hist = np.histogram(image_array[:, :, 0], bins=256, range=(0, 256))
    green_hist = np.histogram(image_array[:, :, 1], bins=256, range=(0, 256))
    blue_hist = np.histogram(image_array[:, :, 2], bins=256, range=(0, 256))

    # Рисование графика распределения цветов
    plt.figure(figsize=(10, 6))
    plt.title('Color Distribution')
    plt.xlabel('Color Intensity')
    plt.ylabel('Frequency')
    plt.xlim(0, 255)
    plt.plot(red_hist[1][:-1], red_hist[0], color='red', label='Red')
    plt.plot(green_hist[1][:-1], green_hist[0], color='green', label='Green')
    plt.plot(blue_hist[1][:-1], blue_hist[0], color='blue', label='Blue')
    plt.legend()

    plt.savefig(f"static/graph/{name}", dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'upload'
    app.run()