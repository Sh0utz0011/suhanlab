from flask import Flask, render_template, request, redirect, url_for, g,abort
from PIL import Image
import os
from werkzeug.utils import secure_filename
import numpy as np
from forms import MyForm,FloatForm
import matplotlib.pyplot as plt
import datetime
from flask import url_for

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lcmtj8mAAAAAPhfPRtEI1gGg6oqH0Gw0wmZ6e1N'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Lcmtj8mAAAAABcRIZWb0SMl4C0Fjx6s4Jw7UN46'
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

        # Сохраняем измененное изображение и строим графики
        changed_filename = f"changed_{filename}"
        changed_image_path = image_changed_path+"/resized_"+filename

        orig_graph_name = f"{filename.split('.')[0]}_graph.png"
        plot_color_distribution(image_path, orig_graph_name)
        changed_graph_name = f"{changed_filename.split('.')[0]}_graph.png"
        plot_color_distribution(changed_image_path, changed_graph_name)

        # Вычисляем разницу между гистограммами и строим график разности
        orig_hist = np.histogram(np.array(Image.open(image_path))[:, :, 0:3].ravel(), bins=256, range=(0, 256))[0]
        changed_hist = \
        np.histogram(np.array(Image.open(changed_image_path))[:, :, 0:3].ravel(), bins=256, range=(0, 256))[0]
        hist_diff = orig_hist - changed_hist
        plt.figure(figsize=(10, 6))
        plt.title('Color Distribution Difference')
        plt.xlabel('Color Intensity')
        plt.ylabel('Frequency Difference')
        plt.xlim(0, 255)
        plt.plot(hist_diff, color='black')
        plt.savefig(f"static/graph/diff_{filename}", dpi=300, bbox_inches='tight')
        plt.close()

        # Получаем текущее время
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Возвращаем шаблон с изображениями и временем загрузки
        return render_template("changed_image.html",
                               filename=filename,
                               graph_name=orig_graph_name,
                               changed_filename=changed_filename,
                               changed_graph_name=changed_graph_name,
                               diff_graph_name=f"diff_{filename}",
                               current_time=current_time)
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
def plot_color_diff(image_path, changed_path, name):
    # Загрузка изображений с помощью Pillow
    image = Image.open(image_path)
    changed_image = Image.open(changed_path)

    # Преобразование изображений в массивы NumPy
    image_array = np.array(image)
    changed_image_array = np.array(changed_image)

    # Вычисление гистограмм распределения цветов для исходного и обработанного изображений
    red_hist = np.histogram(image_array[:, :, 0], bins=256, range=(0, 256))
    green_hist = np.histogram(image_array[:, :, 1], bins=256, range=(0, 256))
    blue_hist = np.histogram(image_array[:, :, 2], bins=256, range=(0, 256))
    changed_red_hist = np.histogram(changed_image_array[:, :, 0], bins=256, range=(0, 256))
    changed_green_hist = np.histogram(changed_image_array[:, :, 1], bins=256, range=(0, 256))
    changed_blue_hist = np.histogram(changed_image_array[:, :, 2], bins=256, range=(0, 256))

    # Вычисление разности гистограмм распределения цветов
    red_diff = red_hist[0] - changed_red_hist[0]
    green_diff = green_hist[0] - changed_green_hist[0]
    blue_diff = blue_hist[0] - changed_blue_hist[0]

    # Рисование графика разности распределения цветов
    plt.figure(figsize=(10, 6))
    plt.title('Color Distribution Difference')
    plt.xlabel('Color Intensity')
    plt.ylabel('Frequency Difference')
    plt.xlim(0, 255)
    plt.plot(red_hist[1][:-1], red_diff, color='red', label='Red')
    plt.plot(green_hist[1][:-1], green_diff, color='green', label='Green')
    plt.plot(blue_hist[1][:-1], blue_diff, color='blue', label='Blue')
    plt.legend()

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'upload'
    app.run()
