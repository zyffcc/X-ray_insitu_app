import sys
import cv2
import os
import numpy as np
import tempfile
from scipy.interpolate import make_interp_spline
import glob
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, \
    QLineEdit, QVBoxLayout, QSizePolicy, QGridLayout, QWidget, QRadioButton, QButtonGroup, \
    QFileSystemModel, QTreeView, QHBoxLayout, QSplitter, QDesktopWidget, QMessageBox, QComboBox, \
    QFrame, QCheckBox, QProgressBar, QMenu, QMenuBar, QAction, QTextEdit, QDialog, QSplashScreen
from PyQt5.QtGui import QImage, QPixmap, QPainter, QTransform, QMovie
from PyQt5.QtCore import QSize, Qt, QRect, QPoint, QDir, QTimer, QCoreApplication, QEventLoop,\
    QSettings, QThread, pyqtSignal, QResource
from matplotlib import cm
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.lines import Line2D

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # self.image_layout = ImageLayout(self)
        self.image_widget = ImageWidget(self)
        self.parameter = Parameter(self, image_widget=self.image_widget)
        # self.parameter = Parameter(self)
        self.image_layout = ImageLayout(self, parameter=self.parameter, image_widget = self.image_widget)
        self.image_widget.set_image_layout(self.image_layout, self.parameter)
        self.parameter.set_image_layout(self.image_layout)
        self.dirtree = FileExplorer(self.image_layout)

        # 创建BatchProcessor实例对象
        self.batch_processor = BatchProcessor(self.image_widget,self.image_layout)
        self.image_widget.set_batch_processor(self.batch_processor)
        self.image_layout.set_batch_processor(self.batch_processor)

        # 设置左侧部件和右侧部件
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.dirtree)
        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.image_layout, 6)
        # 添加第一条水平方向的横线
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(line1)
        right_layout.addWidget(self.parameter, 1)
        # 添加第二条水平方向的横线
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        right_layout.addWidget(line2)
        right_layout.addWidget(self.batch_processor,1)
        right_widget.setLayout(right_layout)

        # 创建QSplitter对象并添加left_widget和right_widget
        splitter = QSplitter()
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # 设置初始大小比例为1:4
        splitter.setSizes([2,4])
        # splitter.setStretchFactor(0, 3)  # 设置左部件的拉伸因子为1
        # splitter.setStretchFactor(1, 4)  # 设置右部件的拉伸因子为4

        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.dirtree.setMinimumWidth(300)
        self.image_layout.setMinimumWidth(400)

        # 设置整体布局
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        self.setCentralWidget(main_widget)

        # 设置主窗口的标题
        self.setWindowTitle('原位数据处理')

        # 创建菜单项
        help_action = QAction('程序说明', self)
        help_action.triggered.connect(self.show_help)
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)

        # 创建菜单
        help_menu = QMenu('Help', self)
        help_menu.addAction(help_action)
        about_menu = QMenu('About', self)
        about_menu.addAction(about_action)

        # 创建菜单栏并添加菜单
        menu_bar = QMenuBar(self)
        menu_bar.addMenu(help_menu)
        menu_bar.addMenu(about_menu)

        # 将菜单栏设置为窗口的菜单栏
        self.setMenuBar(menu_bar)

        self.readme_content = """
        软件功能简介及使用说明

        该软件提供了对二维散射图片的处理、积分、原位数据处理等功能。以下是各个功能模块的详细说明。
        
        1. 二维图片处理
        
        1.1 导入图片
        
        左侧双击 .tif 文件导入
        点击文件名 - 选择文件按钮
        直接拖入右上角框内
        
        1.2 调整 Colorbar
        
        调整 Colorbar_min 和 Colorbar_max 参数
        默认的 colormap 为 jet，当前版本不提供调整色系功能
        
        1.3 改变二维坐标显示
        
        默认坐标系单位为 pixel
        转化为 Qxy 和 Qz 坐标选择“切图”
        
        1.4 导出二维图片
        
        点击选择"导出文件夹"选定文件夹路径，默认为程序所在的当前文件夹
        点击"导出图片-jpg"
        
        1.5 调整切图显示范围
        
        调整“切图Qr_min”，“切图Qr_max”，“切图Qz_min”，“切图Qz_max”
        如果设置为 -121 则为不加限制
        
        1.6 遮盖图片坏点和gap
        
        改变“Mask_min”和"Mask_max"将小于或者大于设定值的像素设置为0
        
        2. 二维图片积分为一维曲线
        
        2.1 导入图片
        
        根据第1步导入图片，原图切图均可
        
        2.2 确定实验条件
        
        修改“入射角”（单位：°），“圆心-X”（单位：pixel），“圆心-Y”(单位：pixel)，“距离”(单位：mm)，“像素-X”（单位：um），“像素-Y”（单位：um），“波长”（单位：埃）
        实验条件的确定可以由 Fit2D 完成
        友情链接 Fit2D: http://ftp.esrf.eu/pub/expg/FIT2D/
        
        2.3 积分区域选择
        
        点击“积分区域选择”按钮，选四个点：初始方位角，最终方位角，起始积分内径，最终积分外径，确定一个顺时针扇形
        也可以通过按钮下方四个文本框手动输入，单位分别为°以及pixel
        
        2.4 选择积分方式
        
        选择“径像积分”和“角向积分”，分别对应沿 q 积分和沿方位角积分
        调整积分步长，默认为 500
        
        2.5 选择坐标轴
        
        默认为 Log 坐标，q 为横坐标，单位埃分之一，降噪平滑
        可选项：pixel 和 2Theta
        2Theta 的为铜靶波长 1.54 埃下的角度
        也可以选择对应的 unsmoothed 的未经过平滑操作的原始数据
        纵坐标也可以转化为线性坐标
        
        2.6 导出一维结果
        
        先“选择导出文件夹”，然后点击积分结果导出-txt，导出格式为 txt
        
        3. 原位数据处理
        
        3.1 选择原位数据文件夹
        
        在最下面一栏选择文件夹选择原位数据所处的文件夹
        
        3.2 文件名匹配模式
        
        输入匹配模式，如原位数据为 Cl0001.tif, Cl0002.tif....，则匹配模式可以设置为 Cl*.tif
        
        3.3 批量处理功能
        
        提供二维图片批量导出、一维曲线批量导出、以及一维曲线的扣背底
        前置操作参考单张图片
        调整 Colorbar_min、Colorbar_max 以及 Mask_min, Mask_max
        点击切图或原图
        
        3.4 设置实验参数和积分区域
        
        参考第 2 步设置实验参数和积分区域
        
        3.5 设置扣背底参数
        
        有三个参数：以第几张图片为基准，积分曲线显示范围的起始和结束
        
        3.6 批量处理导出
        
        点击批量处理后，导出 output 和 output_subbg 文件
        第一列是横坐标，之后每一列代表对应图片的积分坐标
        可以用原位热图预览初步预览本组数据的情况，建议用 origin heatmap 模块进行处理
        
        3.7 导入已处理的原位数据
        
        点击原位文件导入，导入处理过的 output.txt 文件，显示原位热图预览
        使用以上功能，您可以对二维散射图片进行处理、积分以及批量处理原位数据。如有疑问，请参阅相关文档或联系开发者。
        
        ————————————————————————————————
        
        更新日志：

        1.1 增加了关闭软件后对之前输入参数的记忆。

        1.2 增加了原位数据处理的暂停功能。
        
        1.3 增加了翻转按钮，按需可以对二维图进行上下翻转操作。注意，翻转对积分区域选择的图像不适用。
        
        1.4 优化了扣背底参数的实现。
        
        1.5 热图预览使用插值方法，是的对数据量较少的output文件显示更为优化。
        
        1.6 增加了对除tif，jpg外的图片文件的支持。
        
        """

    def show_help(self):
        # 显示帮助信息
        help_dialog = HelpDialog(self.readme_content, self)
        help_dialog.exec_()

    def show_about(self):
        QMessageBox.about(self, 'About', 'Copyright (c) Yufeng Zhai'
                                         '\nVersion v1.0'
                                         '\nDate 2023-05-03')

    def closeEvent(self, event):
        # Save current settings
        settings = QSettings('mycompany', 'myapp')
        settings.setValue('Angle_incidence', self.parameter.Angle_incidence.text())
        settings.setValue('x_Center', self.parameter.x_Center.text())
        settings.setValue('y_Center', self.parameter.y_Center.text())
        settings.setValue('distance', self.parameter.distance.text())
        settings.setValue('pixel_x', self.parameter.pixel_x.text())
        settings.setValue('pixel_y', self.parameter.pixel_y.text())
        settings.setValue('lamda', self.parameter.lamda.text())
        settings.setValue('textbox_min',self.image_layout.textbox_min.text())
        settings.setValue('textbox_max', self.image_layout.textbox_max.text())
        settings.setValue('Qr_min', self.parameter.Qr_min.text())
        settings.setValue('Qr_max', self.parameter.Qr_max.text())
        settings.setValue('Qz_min', self.parameter.Qz_min.text())
        settings.setValue('Qz_max', self.parameter.Qz_max.text())
        settings.setValue('threshold_min', self.parameter.threshold_min.text())
        settings.setValue('threshold_max', self.parameter.threshold_max.text())
        settings.setValue('numbin', self.parameter.numbin.text())

        super().closeEvent(event)

    def close_loading(self):
        self.label.close()
        self.show()

class HelpDialog(QDialog):
    def __init__(self, content, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Help")
        self.resize(600, 400)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(content)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

class ImageWidget(QWidget):
    def __init__(self, parent=None, file_name=None, textbox_min=None, textbox_max=None, Angle_incidence=None, x_Center=None,
                  y_Center=None, distance=None, pixel_x=None, pixel_y=None, lamda=None, threshold_min=None, threshold_max=None):
        super().__init__(parent)

        #导出图像用的
        self.fig = None

        self.setAcceptDrops(True)  # 允许接受拖放事件
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(1, 1)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


        self.size_label = QLabel(self)
        self.size_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.size_label.setMinimumSize(1, 1)
        self.size_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.size_label)
        self.setLayout(self.layout)

        self.file_name = file_name
        self.textbox_min = textbox_min
        self.textbox_max = textbox_max
        self.Angle_incidence = Angle_incidence
        self.x_Center = x_Center
        self.y_Center = y_Center
        self.distance = distance
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.lamda = lamda
        self.threshold_min = threshold_min
        self.threshold_max = threshold_max

        # 窗口大小变化时连接resizeEvent事件
        self.resizeEvent = self.on_resize
        # 设置初始缩放级别
        self.scale_factor = 1.0
        # 在滚轮事件中记录时间和鼠标位置
        self.last_wheel_time = 0
        self.last_wheel_pos = QPoint(0, 0)
        # 记录上一次鼠标位置
        self.last_pos = None
        # 记录图像的偏移量
        self.image_offset = QPoint(0, 0)


        #初始化定时器，提高改变窗口大小时调用Cut的流畅度
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.on_resize_timeout)

        # 类变量，用于存储图像窗口的引用
        self.image_fig = None

        # 初始化区域参数
        self.numbin = 1000

        # 设置当前窗口状态
        self.windowstate = 0

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile() and os.access(url.toLocalFile(), os.R_OK):
                event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        url = event.mimeData().urls()[0]
        file_path = url.toLocalFile()
        self.file_name = file_path
        self.image_layout.file_name = file_path
        self.update_image()

    def update_image(self):
        if self.file_name:
            # 读取图像并规范化
            cb_min = float(self.textbox_min.text())
            cb_max = float(self.textbox_max.text())
            im = cv2.imread(self.file_name, cv2.IMREAD_ANYDEPTH)

            mask = (im >= self.threshold_max) | (im < self.threshold_min)
            img_norm = im.copy()
            img_norm[img_norm > cb_max] = cb_max
            img_norm[img_norm < cb_min] = cb_min
            im_norm = cv2.normalize(img_norm, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            im_norm[mask] = 0
            if self.image_layout.flip.isChecked():
                im_norm = cv2.flip(im_norm, 0)

            # 缩放图像以适应窗口
            height, width = im_norm.shape
            window_height, window_width = self.label.height(), self.label.width()
            if window_height <= 1 or window_width <= 1:
                return
            scale = min(window_height / height, window_width / width)
            resized = cv2.resize(im_norm, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_NEAREST)
            # 使用Jet颜色映射
            color_map = cv2.applyColorMap(resized, cv2.COLORMAP_JET)

            # 显示图像
            pixmap = self.to_qimage(color_map)
            self.label.setPixmap(pixmap)
            # pixmap_offset = self.image_offset - self.label.rect().topLeft()
            # self.label.setPixmap(pixmap)
            # self.label.move(pixmap_offset)
            self.size_label.setText(f'pixels：{im.shape[1]} x {im.shape[0]} file_name: {os.path.basename(self.file_name)}')

            self.windowstate = 1

    def to_qimage(self, img): #转化为Qpixmap
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        elif len(img.shape) == 3 and img.shape[2] == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        height, width, channels = img.shape
        bytes_per_line = channels * width
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimage = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(qimage)

    def Cut(self):
        #初始化参数
        if self.file_name:
            Angle_incidence = float(self.Angle_incidence)
            x_Center = float(self.x_Center)
            y_Center = float(self.y_Center)
            distance = float(self.distance)
            pixel_x = float(self.pixel_x)
            pixel_y = float(self.pixel_y)
            lamda = float(self.lamda)

            # 读取图像并规范化
            cb_min = float(self.textbox_min.text())
            cb_max = float(self.textbox_max.text())

            threshold_min = float(self.threshold_min)
            threshold_max = float(self.threshold_max)

            im = cv2.imread(self.file_name, cv2.IMREAD_ANYDEPTH)
            img_norm = im.copy()
            img_norm = img_norm.astype(float)

            # Create mask for regions above threshold_max and below threshold_min
            mask_max = np.zeros_like(img_norm, dtype=np.uint8)
            mask_max[img_norm > threshold_max] = 255

            mask_min = np.zeros_like(img_norm, dtype=np.uint8)
            mask_min[img_norm < threshold_min] = 255

            mask = cv2.bitwise_or(mask_max, mask_min)
            img_norm[mask == 255] = 0

            img_norm[img_norm > cb_max] = cb_max
            img_norm[img_norm < cb_min] = cb_min

            im_norm = cv2.normalize(img_norm, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            im_norm = cv2.flip(im_norm, 0)

            # 读取文件
            A = im_norm

            # 参数设置
            sz = np.shape(A)
            sz_1 = sz[1]
            sz_2 = sz[0]
            y_Center = sz_2 - y_Center
            Qr, Qz = np.meshgrid(np.arange(1, sz_1 + 1), np.arange(1, sz_2 + 1))

            # pixel
            Qr = Qr - x_Center
            Qz = (sz_2 - y_Center) - Qz
            # distance
            Qr = Qr * pixel_x * 1e-6
            Qz = Qz * pixel_y * 1e-6
            # Theta
            Qxx = Qr
            Qr = np.arctan(Qr / (distance * 1e-3)) / 2
            Qz = np.arctan(Qz / np.sqrt((distance * 1e-3) ** 2 + Qxx ** 2))
            # Theta = np.arctan(np.sqrt(Qr ** 2 * Qz ** 2) / (distance * 1e-3))

            Theta_f = Qr
            Alpha_f = Qz
            Alpha_i = Angle_incidence * np.pi / 180  # 入射角度

            Qx = 2 * np.pi / lamda * (np.cos(2 * Theta_f) * np.cos(Alpha_f) - np.cos(Alpha_i))
            Qy = 2 * np.pi / lamda * (np.sin(2 * Theta_f) * np.cos(Alpha_f))
            Qz = 2 * np.pi / lamda * (np.sin(Alpha_f) + np.sin(Alpha_i))

            # q 单位：Angstrom
            Qr = np.sign(Qy) * np.sqrt(Qx ** 2 + Qy ** 2)
            Qz = Qz
            # Qr[Qy_temp < 0] = np.nan
            diff_Qy = np.diff(np.sign(Qy), axis=1)
            indices = np.where(diff_Qy != 0)

            # 在 diff_Qy 中找到变号的区域，并将对应的 A 数组中的值设置为 NaN
            A = A.astype(float)
            A[indices[0], indices[1]] = np.nan
            A[indices[0], indices[1] + 1] = np.where(Qy[indices[0], indices[1] + 1] > 0, np.nan,
                                                     A[indices[0], indices[1] + 1])
            A[indices[0], indices[1] - 1] = np.where((indices[1] > 0) & (Qy[indices[0], indices[1] - 1] < 0), np.nan,
                                                     A[indices[0], indices[1] - 1])

            # 创建掩码数组
            A_masked = np.ma.masked_where(np.isnan(A), A)

            # 绘制pcolor图像


            self.fig, ax = plt.subplots()
            pcolor = ax.pcolormesh(Qr, Qz, A_masked, cmap='jet', shading='auto')
            self.fig.colorbar(pcolor)
            ax.set_xlabel('Qr')
            ax.set_ylabel('Qz')
            ax.set_aspect('equal')
            if not self.image_layout.flip.isChecked():
                plt.gca().invert_yaxis()
            # 设置横纵坐标显示范围
            if float(self.parameter.Qr_min.text()) == -121:
                Qr_min = None
            else:
                Qr_min = float(self.parameter.Qr_min.text())

            if float(self.parameter.Qr_max.text()) == -121:
                Qr_max = None
            else:
                Qr_max = float(self.parameter.Qr_max.text())

            if float(self.parameter.Qz_min.text()) == -121:
                Qz_min = None
            else:
                Qz_min = float(self.parameter.Qz_min.text())

            if float(self.parameter.Qz_max.text()) == -121:
                Qz_max = None
            else:
                Qz_max = float(self.parameter.Qz_max.text())

            ax.set_xlim(Qr_min, Qr_max)
            ax.set_ylim(Qz_min, Qz_max)

            # 保存图像为临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self.fig.savefig(temp_file.name, dpi=300)
            plt.close(self.fig)  # 关闭绘图窗口

            # 读取临时文件
            color_values = cv2.imread(temp_file.name, cv2.IMREAD_COLOR)

            # 缩放图像以适应窗口
            height, width = color_values.shape[:2]
            window_height, window_width = self.label.height(), self.label.width()
            if window_height <= 1 or window_width <= 1:
                return
            scale = min(window_height / height, window_width / width)
            resized = cv2.resize(color_values, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_NEAREST)

            # 显示图像
            pixmap = self.to_qimage(resized)
            self.label.setPixmap(pixmap)
            self.size_label.setText(f'pixels：{im.shape[1]} x {im.shape[0]} file_name: {os.path.basename(self.file_name)}')

            # 删除临时文件
            temp_file.close()
            os.unlink(temp_file.name)

            self.windowstate = 2

    def update_parameters(self, parameter):

        self.Angle_incidence = parameter.Angle_incidence_value
        self.x_Center = parameter.x_Center_value
        self.y_Center = parameter.y_Center_value
        self.distance = parameter.distance_value
        self.pixel_x = parameter.pixel_x_value
        self.pixel_y = parameter.pixel_y_value
        self.lamda = parameter.lamda_value
        self.threshold_min = parameter.threshold_min_value
        self.threshold_max = parameter.threshold_max_value
        self.numbin = parameter.numbin_value

    def on_resize(self, event):
        if self.image_layout.rb1.isChecked():
            self.update_image()
        if self.image_layout.rb2.isChecked():
            self.resize_timer.start(300)  # 设置等待时间，单位为毫秒
        event.accept()

    def on_resize_timeout(self):
        self.Cut()
    # def wheelEvent(self, event):
    #     # 获取当前的鼠标位置
    #     mouse_pos = event.pos()
    #
    #     # 计算鼠标位置与标签的偏移量
    #     offset = mouse_pos - self.label.pos()
    #
    #     # 计算缩放因子和缩放中心点
    #     zoom_in_factor = 1.25
    #     zoom_out_factor = 1 / zoom_in_factor
    #     zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
    #     center = QPoint(offset.x() * zoom_factor, offset.y() * zoom_factor)
    #
    #     # 改变图像缩放级别
    #     self.scale_factor *= zoom_factor
    #     if self.scale_factor < 0.1:
    #         self.scale_factor = 0.1
    #
    #     # 改变图像缩放级别并设置缩放中心点
    #     transform = QTransform().translate(center.x(), center.y()).scale(zoom_factor, zoom_factor).translate(
    #         -center.x(), -center.y())
    #     # transform = QTransform().scale(zoom_factor, zoom_factor)
    #     self.label.setPixmap(self.label.pixmap().transformed(transform))

    def mousePressEvent(self, event):
        # 记录鼠标按下时的位置
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        # 如果鼠标左键被按下，移动图片
        if event.buttons() == Qt.LeftButton:
            # 计算鼠标移动距离
            delta = event.pos() - self.last_pos
            self.last_pos = event.pos()

            # 更新图像的偏移量
            self.image_offset += delta

            # 更新图像
            # self.update_image()
            pixmap_offset = self.image_offset - self.label.rect().topLeft()
            self.label.move(pixmap_offset)

    def mouseReleaseEvent(self, event):
        # 鼠标释放时清空记录的上一次鼠标位置
        self.last_pos = None

    def set_image_layout(self, image_layout, parameter):
        self.image_layout = image_layout
        self.parameter = parameter

    def set_batch_processor(self, batch_processor):
        self.batch_processor = batch_processor

    def update_batch_processor_filename(self):
        self.file_name = self.batch_processor.filename

    def int_region(self, cb_min, cb_max, x_center, y_center):

        # 读取图像并规范化
        im = cv2.imread(self.file_name, cv2.IMREAD_ANYDEPTH)
        img_norm = im.copy()
        img_norm[img_norm > cb_max] = cb_max
        img_norm[img_norm < cb_min] = cb_min
        im_norm = cv2.normalize(img_norm, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        im_norm = cv2.flip(im_norm, 0)

        # fig, ax = plt.subplots()
        # ax.imshow(im_norm)

        # 创建图像窗口
        if self.image_fig is None or not plt.fignum_exists(self.image_fig.number):
            self.image_fig, axx = plt.subplots()
            axx.imshow(im_norm)

        else:
            self.image_fig.clf()
            axx = self.image_fig.add_subplot(111)
            axx.imshow(im_norm)
            plt.draw()

        # 用于存储鼠标点击位置
        points = []

        for i in range(4):
            # 获取鼠标点击位置
            point = plt.ginput(1)[0]
            x, y = int(point[0]), int(point[1])
            points.append((x, y))

            if i == 0 or i == 1:
                # 绘制直线
                axx.add_line(Line2D([x, x_center], [y, y_center], color='red'))
                plt.draw()  # 强制刷新图像
            else:
                # 计算起始和终止角度
                start_angle = np.arctan2(points[0][1] - y_center, points[0][0] - x_center)
                end_angle = np.arctan2(points[1][1] - y_center, points[1][0] - x_center)
                if i == 2:
                    # 计算内半径和外半径
                    inner_radius = np.sqrt((points[2][0] - x_center) ** 2 + (points[2][1] - y_center) ** 2)
                    # 绘制扇形区域
                    wedge = Wedge((x_center, y_center), inner_radius, math.degrees(start_angle),
                                  math.degrees(end_angle),
                                  width=2)
                    axx.add_patch(wedge)
                    plt.draw()  # 强制刷新图像
                if i == 3:
                    outer_radius = np.sqrt((points[3][0] - x_center) ** 2 + (points[3][1] - y_center) ** 2)
                    # 绘制扇形区域
                    wedge = Wedge((x_center, y_center), outer_radius, math.degrees(start_angle),
                                  math.degrees(end_angle),
                                  width=outer_radius-inner_radius)
                    wedge.set_alpha(0.5)
                    axx.add_patch(wedge)
                    plt.draw()  # 强制刷新图像

        # # 提示用户是否确认选择区域
        # msg_box = QMessageBox()
        # msg_box.setText("是否确认选择区域？")
        # msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        # msg_box.setDefaultButton(QMessageBox.Yes)
        # 关闭图像窗口并返回结果
        # plt.close(fig)
        # ret = msg_box.exec_()
        return im_norm, start_angle, end_angle, inner_radius, outer_radius

    # 将笛卡尔坐标系下的图像转换为极坐标系下的图像
    def cart2pol(self, image, center):
        # 计算图像中每个像素点的极坐标值
        x, y = np.meshgrid(np.arange(image.shape[1]), np.arange(image.shape[0]))
        x = x - center[0]
        y = y - center[1]
        r, theta = cv2.cartToPolar(x, y)

        # 插值得到极坐标系下的图像
        polar_image = cv2.remap(image, theta, r, cv2.INTER_LINEAR)

        return polar_image

    # 点击积分按钮调用此函数
    def radial_integral(self, image, center, start_angle, end_angle, inner_radius, outer_radius, num_bins):
        """
        计算选定的扇形区域的径向积分和角向积分
        :param image: 待处理的图像
        :param center: 中心像素位置，tuple类型，(x, y)
        :param start_angle: 起始方位角，单位为度，0度表示x轴正方向，逆时针旋转为正
        :param end_angle: 结束方位角，单位为度，0度表示x轴正方向，逆时针旋转为正
        :param inner_radius: 扇形区域的内径
        :param outer_radius: 扇形区域的外径
        :param num_bins: 径向积分的点数
        :return: (radial_profile, angular_profile)，径向积分和角向积分
        """

        num_bins = int(num_bins)
        # 将角度转换为弧度
        start_angle = math.radians(start_angle)
        end_angle = math.radians(end_angle)

        # 构造一个极坐标网格
        height, width = image.shape[:2]
        y, x = np.ogrid[:height, :width]
        x = x.astype(np.float64) - float(center[0])
        y = y.astype(np.float64) - float(center[1])
        r = np.hypot(x, y)
        theta = np.arctan2(y, x)


        #
        im = cv2.imread(self.file_name, cv2.IMREAD_ANYDEPTH)
        im = cv2.flip(im, 0)
        # 确定扇形区域的布尔掩码
        mask = (r >= inner_radius) & (r <= outer_radius) & (theta >= start_angle) & (theta <= end_angle)

        if start_angle >= end_angle:
            mask = (r >= inner_radius) & (r <= outer_radius) & ((theta >= start_angle) | (theta <= end_angle))
            end_angle = end_angle + 2 * np.pi
        mask = mask & (im >= self.threshold_min)
        mask = mask & (im <= self.threshold_max)
        # print(im)

        # plt.imshow(mask.astype(np.float64), cmap='gray')
        # plt.show()
        # 计算径向积分
        rbin_edges = np.linspace(inner_radius, outer_radius, num_bins + 1)
        rbin_centers = 0.5 * (rbin_edges[1:] + rbin_edges[:-1])
        radial_profile, _ = np.histogram(r[mask], bins=rbin_edges, weights=image[mask].astype(np.float64))
        radial_profile = radial_profile.astype(np.float64) / np.diff(rbin_edges)

        # 计算角向积分
        thetabin_edges = np.linspace(start_angle, end_angle, num_bins + 1)
        thetabin_centers_radians = 0.5 * (thetabin_edges[1:] + thetabin_edges[:-1])
        thetabin_centers_degrees = np.degrees(thetabin_centers_radians)
        angular_profile, _ = np.histogram(theta[mask], bins=thetabin_edges, weights=image[mask].astype(np.float64))
        angular_profile = angular_profile.astype(np.float64) / np.diff(thetabin_edges)

        # 定义滑动窗口的大小
        window_size = 5
        # 定义滑动窗口的权重
        window = np.ones(window_size) / window_size
        # 对angular_profile进行滑动平均
        smoothed_angular_profile = np.convolve(angular_profile, window, mode='same')
        smoothed_radial_profile = np.convolve(radial_profile, window, mode='same')

        # 绘制图像
        self.fig, ax = plt.subplots()
        index = self.image_layout.comboBox.currentIndex()
        distance = float(self.distance) * 1e-3
        pixel_x = float(self.pixel_x) * 1e-6
        pixel_y = float(self.pixel_y) * 1e-6
        lamda = float(self.lamda)

        pixel = (pixel_x + pixel_y)/2
        theta = np.arctan(rbin_centers * pixel / distance) / 2
        q = 4 * np.pi * np.sin(theta) / lamda
        twoTheta = np.arcsin(q * 1.54 / 4 / np.pi) * 180 / np.pi * 2

        if self.image_layout.comboBox2.currentIndex() == 0:
            if self.image_layout.radioButtonRadial.isChecked():
                if index == 0 :
                    ax.semilogy(q, smoothed_radial_profile)
                    ax.set_xlabel('q')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Radial Profile')
                    # return q, smoothed_radial_profile
                if index == 1:
                    ax.semilogy(twoTheta, smoothed_radial_profile)
                    ax.set_xlabel('2Theta')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Radial Profile')
                    # return twoTheta, smoothed_radial_profile
                if index == 2:
                    ax.semilogy(rbin_centers, smoothed_radial_profile)
                    ax.set_xlabel('Pixel')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Radial Profile')
                    # return rbin_centers, smoothed_radial_profile
                if index == 3:
                    ax.semilogy(q, radial_profile)
                    ax.set_xlabel('q')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Radial Profile')
                    # return q, radial_profile
                if index == 4:
                    ax.semilogy(twoTheta, radial_profile)
                    ax.set_xlabel('2Theta')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Radial Profile')
                    # return twoTheta, radial_profile
                if index == 5:
                    ax.semilogy(rbin_centers, radial_profile)
                    ax.set_xlabel('Pixel')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Radial Profile')
                    # return rbin_centers, radial_profile
            if self.image_layout.radioButtonAngular.isChecked():
                if index == 0:
                    ax.semilogy(thetabin_centers_degrees, smoothed_angular_profile)
                    ax.set_xlabel('Theta')
                    ax.set_ylabel('Intensity (Log Scale)')
                    ax.set_title('Azimuth Profile')
                    # return thetabin_centers_degrees, smoothed_angular_profile
        if self.image_layout.comboBox2.currentIndex() == 1:
            if self.image_layout.radioButtonRadial.isChecked():
                if index == 0 :
                    ax.plot(q, smoothed_radial_profile)
                    ax.set_xlabel('q')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Radial Profile')
                    # return q, smoothed_radial_profile
                if index == 1:
                    ax.plot(twoTheta, smoothed_radial_profile)
                    ax.set_xlabel('2Theta')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Radial Profile')
                    # return twoTheta, smoothed_radial_profile
                if index == 2:
                    ax.plot(rbin_centers, smoothed_radial_profile)
                    ax.set_xlabel('Pixel')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Radial Profile')
                    # return rbin_centers, smoothed_radial_profile
                if index == 3:
                    ax.plot(q, radial_profile)
                    ax.set_xlabel('q')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Radial Profile')
                    # return q, radial_profile
                if index == 4:
                    ax.plot(twoTheta, radial_profile)
                    ax.set_xlabel('2Theta')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Radial Profile')
                    # return twoTheta, radial_profile
                if index == 5:
                    ax.plot(rbin_centers, radial_profile)
                    ax.set_xlabel('Pixel')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Radial Profile')
                    # return rbin_centers, radial_profile
            if self.image_layout.radioButtonAngular.isChecked():
                if index == 0:
                    ax.plot(thetabin_centers_degrees, smoothed_angular_profile)
                    ax.set_xlabel('Theta')
                    ax.set_ylabel('Intensity')
                    ax.set_title('Azimuth Profile')
                    # return thetabin_centers_degrees, smoothed_angular_profile

        # 保存图像为临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        self.fig.savefig(temp_file.name, dpi=300)
        plt.close(self.fig)  # 关闭绘图窗口

        # 读取临时文件
        color_values = cv2.imread(temp_file.name, cv2.IMREAD_COLOR)

        # 缩放图像以适应窗口
        height, width = color_values.shape[:2]
        window_height, window_width = self.label.height(), self.label.width()
        if window_height <= 1 or window_width <= 1:
            return
        scale = min(window_height / height, window_width / width)
        resized = cv2.resize(color_values, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_NEAREST)

        # 显示图像
        pixmap = self.to_qimage(resized)
        self.label.setPixmap(pixmap)
        self.size_label.setText(f'一维图片——file_name: {os.path.basename(self.file_name)}')

        # 删除临时文件
        temp_file.close()
        os.unlink(temp_file.name)

        self.windowstate = 3

        if self.image_layout.comboBox2.currentIndex() == 0:
            if self.image_layout.radioButtonRadial.isChecked():
                if index == 0 :
                    return q, smoothed_radial_profile
                if index == 1:
                    return twoTheta, smoothed_radial_profile
                if index == 2:
                    return rbin_centers, smoothed_radial_profile
                if index == 3:
                    return q, radial_profile
                if index == 4:
                    return twoTheta, radial_profile
                if index == 5:
                    return rbin_centers, radial_profile
            if self.image_layout.radioButtonAngular.isChecked():
                if index == 0:
                    return thetabin_centers_degrees, smoothed_angular_profile
        if self.image_layout.comboBox2.currentIndex() == 1:
            if self.image_layout.radioButtonRadial.isChecked():
                if index == 0 :
                    return q, smoothed_radial_profile
                if index == 1:
                    return twoTheta, smoothed_radial_profile
                if index == 2:
                    return rbin_centers, smoothed_radial_profile
                if index == 3:
                    return q, radial_profile
                if index == 4:
                    return twoTheta, radial_profile
                if index == 5:
                    return rbin_centers, radial_profile
            if self.image_layout.radioButtonAngular.isChecked():
                if index == 0:
                    return thetabin_centers_degrees, smoothed_angular_profile

    # 点击积分按钮调用此函数
    def calculate_integral(self):
        try:
            if self.file_name:
                cb_min = float(self.textbox_min.text())
                cb_max = float(self.textbox_max.text())
                # 获取image
                im = cv2.imread(self.file_name, cv2.IMREAD_ANYDEPTH)
                img_norm = im.copy()
                img_norm[img_norm > cb_max] = cb_max
                img_norm[img_norm < cb_min] = cb_min
                # im_norm = cv2.normalize(img_norm, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                image = cv2.flip(img_norm, 0)

                # 获取所有参数值
                center = [float(self.x_Center), float(self.y_Center)]
                start_angle = float(self.image_layout.textbox_startAngle.text())
                end_angle = float(self.image_layout.textbox_endAngle.text())
                inner_radius = float(self.image_layout.textbox_innerRadius.text())
                outer_radius = float(self.image_layout.textbox_outerRadius.text())
                num_bins = self.numbin
                # 调用 radial_integral() 函数计算径向积分和角向积分
                x, y = self.radial_integral(image, center, start_angle, end_angle, inner_radius,
                                                                  outer_radius, num_bins)
                # mask = (x >= float(self.batch_processor.background_min.text())) & (x <= float(self.batch_processor.background_max.text()))
                # x_selected = x[mask]
                # y_selected = y[mask]

                return x, y
        except:
            return

class ImageLayout(QWidget):
    def __init__(self, parent = None, file_name = None, parameter = None, image_widget = None):
        super().__init__(parent)

        self.file_name = file_name
        settings = QSettings('mycompany', 'myapp')

        # 添加按钮和文本框控件
        self.button = QPushButton('选择文件', self)
        self.button.setFixedWidth(100)
        self.button.setFixedHeight(30)
        # self.button.move(20, 20)
        self.button.clicked.connect(self.select_file)

        try:
            value = float(settings.value('textbox_min', '0'))
        except ValueError:
            value = 0
        self.textbox_min = QLineEdit(str(value))
        self.textbox_min.setFixedWidth(100)
        self.textbox_min.setFixedHeight(20)
        # self.textbox_min.setText('0')

        try:
            value = float(settings.value('textbox_max', '800'))
        except ValueError:
            value = 800
        self.textbox_max = QLineEdit(str(value))
        self.textbox_max.setFixedWidth(100)
        self.textbox_max.setFixedHeight(20)
        # self.textbox_max.setText('800')

        self.button_output = QPushButton('导出图片-jpg', self)
        self.button_output.setFixedWidth(100)
        self.button_output.setFixedHeight(30)

        self.button_outputdir = QPushButton('选择导出文件夹', self)
        self.button_outputdir.setFixedWidth(150)
        self.button_outputdir.setFixedHeight(30)
        self.textbox_outputdir = QLineEdit(self)
        self.textbox_outputdir.setFixedWidth(400)
        self.textbox_outputdir.setFixedHeight(20)
        self.textbox_outputdir.setText(os.getcwd())
        self.update_output_folder()

        self.rb1 = QRadioButton('原图')
        self.rb2 = QRadioButton('切图')
        self.flip = QRadioButton('翻转')

        self.button_intRegion = QPushButton('积分区域选择',self)
        self.button_integer = QPushButton('积分',self)
        self.textbox_startAngle = QLineEdit(self)
        self.textbox_startAngle.setFixedWidth(100)
        self.textbox_startAngle.setFixedHeight(20)
        self.textbox_startAngle.setPlaceholderText('start angle')
        self.textbox_endAngle = QLineEdit(self)
        self.textbox_endAngle.setFixedWidth(100)
        self.textbox_endAngle.setFixedHeight(20)
        self.textbox_endAngle.setPlaceholderText('end angle')
        self.textbox_innerRadius = QLineEdit(self)
        self.textbox_innerRadius.setFixedWidth(100)
        self.textbox_innerRadius.setFixedHeight(20)
        self.textbox_innerRadius.setPlaceholderText('inner radius')
        self.textbox_outerRadius = QLineEdit(self)
        self.textbox_outerRadius.setFixedWidth(100)
        self.textbox_outerRadius.setFixedHeight(20)
        self.textbox_outerRadius.setPlaceholderText('outer radius')
        self.export_1D = QPushButton("积分结果导出-txt", self)

        # 创建下拉菜单和按钮
        self.comboBox = QComboBox()
        self.comboBox.addItems(['q', '2theta', '像素', 'q(unsmoothed)', '2theta(unsmoothed)', '像素(unsmoothed)'])
        self.comboBox2 = QComboBox()
        self.comboBox2.addItems(['Log', 'Linear'])
        self.comboBox2.setCurrentIndex(1) #默认Linear
        self.radioButtonRadial = QRadioButton('径向积分')
        self.radioButtonAngular = QRadioButton('角向积分')
        self.radioButtonRadial.setChecked(True)  # 默认选中径向积分

        self.buttonGroup1 = QButtonGroup()
        self.buttonGroup1.addButton(self.radioButtonRadial)
        self.buttonGroup1.addButton(self.radioButtonAngular)
        self.buttonGroup1.setExclusive(True)

        # 创建一个QButtonGroup，并将2个QRadioButton添加到组中
        self.group = QButtonGroup()
        self.group.addButton(self.rb1)
        self.group.addButton(self.rb2)
        # 设置rb1为默认选中状态
        self.rb1.setChecked(True)
        # 设置自动互斥
        self.rb1.setAutoExclusive(True)
        self.rb2.setAutoExclusive(True)

        # 点击按钮改变显示形式
        self.rb1.toggled.connect(lambda: self.on_radiobutton_toggled(self.rb1, self.image_widget.update_image))
        self.rb2.toggled.connect(lambda: self.on_radiobutton_toggled(self.rb2, self.image_widget.Cut))

        self.image_widget = image_widget
        self.image_widget.textbox_min=self.textbox_min
        self.image_widget.textbox_max = self.textbox_max
        self.image_widget.Angle_incidence=parameter.Angle_incidence_value
        self.image_widget.x_Center=parameter.x_Center_value
        self.image_widget.y_Center = parameter.y_Center_value
        self.image_widget.distance=parameter.distance_value
        self.image_widget.pixel_x=parameter.pixel_x_value
        self.image_widget.pixel_y=parameter.pixel_y_value
        self.image_widget.lamda=parameter.lamda_value
        self.image_widget.threshold_min = parameter.threshold_min_value
        self.image_widget.threshold_max = parameter.threshold_max_value
        self.image_widget.numbin = parameter.numbin_value


        # 连接colorbar
        self.textbox_min.editingFinished.connect(self.update_image_finished)
        self.textbox_max.editingFinished.connect(self.update_image_finished)
        self.button_output.clicked.connect(self.export_image)
        self.button_outputdir.clicked.connect(self.select_outputdir)
        self.textbox_outputdir.editingFinished.connect(self.update_output_folder)
        self.button_intRegion.clicked.connect(self.on_intRegion_button_clicked)
        self.textbox_startAngle.editingFinished.connect(self.update_rigionValues)
        self.textbox_endAngle.editingFinished.connect(self.update_rigionValues)
        self.textbox_innerRadius.editingFinished.connect(self.update_rigionValues)
        self.textbox_outerRadius.editingFinished.connect(self.update_rigionValues)
        self.button_integer.clicked.connect(self.image_widget.calculate_integral)
        self.radioButtonRadial.toggled.connect(self.on_radio_button_toggled)
        self.radioButtonAngular.toggled.connect(self.on_radio_button_toggled)
        self.export_1D.clicked.connect(self.export_integral_data)
        self.flip.toggled.connect(self.update_image_finished)

        self.image_widget.setStyleSheet("border: 2px solid #808080; border-radius: 5px;")
        # 创建布局

        radio_buttons_layout = QHBoxLayout()
        radio_buttons_layout.addWidget(self.rb1)
        radio_buttons_layout.addWidget(self.rb2)

        layout = QGridLayout(self)
        layout.addWidget(QLabel('文件名:'), 0, 0)
        layout.addWidget(self.button, 0, 1)
        layout.addWidget(QLabel('Colorbar_min:'), 1, 0)
        layout.addWidget(self.textbox_min, 1, 1)
        layout.addWidget(QLabel('Colorbar_max:'), 2, 0)
        layout.addWidget(self.textbox_max, 2, 1)
        layout.addWidget(self.button_output, 3, 0)
        layout.addWidget(self.image_widget, 0, 2, 11, 1)
        layout.addLayout(radio_buttons_layout, 4, 0)
        layout.addWidget(self.flip, 4, 1)
        layout.addWidget(self.button_intRegion, 5, 0)
        layout.addWidget(self.button_integer, 5, 1)
        layout.addWidget(self.textbox_startAngle,6, 0)
        layout.addWidget(self.textbox_endAngle,6,1)
        layout.addWidget(self.textbox_innerRadius,7,0)
        layout.addWidget(self.textbox_outerRadius,7,1)
        layout.addWidget(QLabel('横坐标单位:'), 8, 0)
        layout.addWidget(self.comboBox, 8, 1)
        layout.addWidget(QLabel('纵坐标Scale:'), 9, 0)
        layout.addWidget(self.comboBox2, 9, 1)
        layout.addWidget(self.radioButtonRadial, 10, 0)
        layout.addWidget(self.radioButtonAngular, 10, 1)
        layout.addWidget(self.export_1D, 3, 1)
        layout.addWidget(self.button_outputdir, 11, 0)
        layout.addWidget(self.textbox_outputdir, 11, 1, 1, 2)

        # 设置原位数据处理窗台码
        self.insitustate = 0

    def on_radio_button_toggled(self):
        if self.radioButtonRadial.isChecked():
            self.comboBox.clear()
            self.comboBox.addItems(['q', '2theta', '像素', 'q(unsmoothed)', '2theta(unsmoothed)', '像素(unsmoothed)'])
        elif self.radioButtonAngular.isChecked():
            self.comboBox.clear()
            self.comboBox.addItems(['Theta'])

    def update_image_finished(self):
        if self.rb1.isChecked():
            self.image_widget.update_image()
        if self.rb2.isChecked():
            self.image_widget.Cut()

    def on_radiobutton_toggled(self, button, func):
        if button.isChecked():
            func()

    def select_file(self):
        # 打开文件选择器对话框
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, '选择文件', '', 'TIFF Files (*.tif *.tiff);;All Files (*)', options=options)
        if file_name:
            try:
                self.file_name = file_name
                # 更新图像
                self.update_image(self.file_name)
                if not self.textbox_startAngle.text():
                    self.textbox_startAngle.setText('-180')
                if not self.textbox_endAngle.text():
                    self.textbox_endAngle.setText('180')
                if not self.textbox_innerRadius.text():
                    self.textbox_innerRadius.setText('0')
                if not self.textbox_outerRadius.text():
                    self.textbox_outerRadius.setText('1000')
            except:
                QMessageBox.warning(self, "Error",
                                    "The selected file cannot be read. Please select a valid TIFF or JPG file.")

    def update_rigionValues(self):
        try:
            # 读取文本框的值
            start_angle = float(self.textbox_startAngle.text())
            end_angle = float(self.textbox_endAngle.text())
            inner_radius = float(self.textbox_innerRadius.text())
            outer_radius = float(self.textbox_outerRadius.text())
            # 将值更新到image_widget对象中
            self.image_widget.startAngle = start_angle
            self.image_widget.endAngle = end_angle
            self.image_widget.innerRadius = inner_radius
            self.image_widget.outerRadius = outer_radius

        except ValueError:
            return

    def update_image(self, file_name):
        # 更新ImageWidget的file_name属性

        # self.image_widget.file_name = self.file_name
        self.image_widget.file_name = file_name
        if self.rb1.isChecked():
            # 调用ImageWidget的update_image()方法
            self.image_widget.update_image()
        if self.rb2.isChecked():
            # 调用ImageWidget的Cut()方法
            self.image_widget.Cut()

    def select_outputdir(self):
        # 获取用户选择的导出目录路径
        folder_path = QFileDialog.getExistingDirectory(self, '选择导出文件夹')
        if folder_path:
            self.output_folder = folder_path
            # 更新导出文件夹的路径文本框
            self.textbox_outputdir.setText(folder_path)

    def on_intRegion_button_clicked(self):
        if self.image_widget.file_name:
            cb_min = float(self.textbox_min.text())
            cb_max = float(self.textbox_max.text())
            x_center = self.image_widget.x_Center
            y_center = self.image_widget.y_Center
            try:
                im_norm, start_angle, end_angle, inner_radius, outer_radius = self.image_widget.int_region(cb_min, cb_max,
                                                                                                           x_center, y_center)
                if start_angle is not None and end_angle is not None and inner_radius is not None and outer_radius is not None:
                    self.textbox_startAngle.setText(str(round(math.degrees(start_angle), 2)))
                    self.textbox_endAngle.setText(str(round(math.degrees(end_angle), 2)))
                    self.textbox_innerRadius.setText(str(round(inner_radius, 2)))
                    self.textbox_outerRadius.setText(str(round(outer_radius, 2)))
                    self.update_rigionValues()

            except ValueError as ve:
                print("Error:", ve)
                QMessageBox.warning(self, "错误", "输入的值有误，请检查并重新输入。")
            except Exception as e:
                print("Error:", e)
                QMessageBox.warning(self, "错误", "发生未知错误，请重试。")
    # def export_image(self):
    #     if self.output_folder:
    #         # 获取用户选择的文件名并拼接文件路径
    #         file_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(self.file_name))[0] + '.jpg')
    #         # 获取当前图像的QPixmap对象
    #         pixmap = self.image_widget.label.pixmap()
    #         # 将QPixmap对象保存为jpg格式的文件
    #         pixmap.save(file_path, 'jpg')
    #     else:
    #         # 如果导出文件夹路径未设置，弹出提示信息
    #         QMessageBox.warning(self, '提示', '请先选择导出文件夹！')

    def export_image(self):
        # 获取用户选择的文件名
        self.update_output_folder()
        file_name = self.file_name

        if not file_name:
            return

        # 获取用户选择的文件名并拼接文件路径
        if self.insitustate == 0:
            file_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(self.file_name))[0] + '.jpg')
        if self.insitustate == 1:
            # 创建 image 文件夹
            folder_name = os.path.splitext(os.path.basename(file_name))[0]
            image_folder_path = os.path.join(self.output_folder, 'image')
            os.makedirs(image_folder_path, exist_ok=True)
            file_path = os.path.join(image_folder_path, folder_name + '.jpg')
            print(file_path)
        if self.image_widget.windowstate == 3: #判断当前图窗是否为一维图像
            # file_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(self.file_name))[0] + '.jpg')
            self.image_widget.fig.savefig(file_path, dpi=300)
            return
        if self.rb1.isChecked():

            # 读取图像并规范化
            cb_min = float(self.textbox_min.text())
            cb_max = float(self.textbox_max.text())
            im = cv2.imread(file_name, cv2.IMREAD_ANYDEPTH)
            img_norm = im.copy()
            img_norm[img_norm > cb_max] = cb_max
            img_norm[img_norm < cb_min] = cb_min
            im_norm = cv2.normalize(img_norm, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

            if self.flip.isChecked():
                im_norm = cv2.flip(im_norm, 0)

            # 创建 jet colormap 并将规范化后的图像映射到 colormap 上
            cmap = cm.get_cmap('jet')
            rgba_img = cmap(im_norm / 255.0)

            # 将 RGBA 图像转换为 BGR 图像，便于用 OpenCV 保存为 jpg 格式
            bgr_img = np.uint8(rgba_img[:, :, :3] * 255)
            rgb_img = bgr_img[..., ::-1]

            # 获取用户选择的文件名并拼接文件路径
            # file_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(self.file_name))[0] + '.jpg')

            # 保存 BGR 图像为 jpg 格式
            cv2.imwrite(file_path, rgb_img)

        if self.rb2.isChecked():

            # file_path = os.path.join(self.output_folder, os.path.splitext(os.path.basename(self.file_name))[0] + '.jpg')
            self.image_widget.fig.savefig(file_path, dpi=300)

    def export_integral_data(self):
        try:
            x, y = self.image_widget.calculate_integral()
            if x is not None and y is not None:
                file_name = os.path.join(self.output_folder,
                                         os.path.splitext(os.path.basename(self.file_name))[0] + '.txt')
                print(file_name)
                with open(file_name, 'a') as f:
                    for i in range(len(x)):
                        f.write(f"{x[i]}\t{y[i]}\n")
                QMessageBox.information(self, "Export Success", "Integral data has been exported successfully!")
        except:
            QMessageBox.warning(self, "Warning", "未能导出数据", QMessageBox.Ok)

    def update_output_folder(self):
        folder_path = self.textbox_outputdir.text()
        if folder_path:
            self.output_folder = folder_path

    def set_file_name(self, file_name):
        self.file_name = file_name

    def set_batch_processor(self, batch_processor):
        self.batch_processor = batch_processor

    def update_batch_processor_filename(self):
        self.file_name = self.batch_processor.filename

class Parameter(QWidget):
    def __init__(self, parent=None, image_widget = None):
        super().__init__(parent)
        self.init_ui()
        self.image_widget = image_widget

    def init_ui(self):
        # 创建文本框并初始化
        settings = QSettings('mycompany', 'myapp')
        self.Angle_incidence = QLineEdit(settings.value('Angle_incidence', '0.5'))
        self.x_Center = QLineEdit(settings.value('x_Center', '0'))
        self.y_Center = QLineEdit(settings.value('y_Center', '0'))
        self.distance = QLineEdit(settings.value('distance', '300'))
        self.pixel_x = QLineEdit(settings.value('pixel_x', '73.2'))
        self.pixel_y = QLineEdit(settings.value('pixel_y', '73.2'))
        self.lamda = QLineEdit(settings.value('lamda', '1.24'))
        self.Qr_min = QLineEdit(settings.value('Qr_min', '-121'))
        self.Qr_max = QLineEdit(settings.value('Qr_max', '-121'))
        self.Qz_min = QLineEdit(settings.value('Qz_min', '-121'))
        self.Qz_max = QLineEdit(settings.value('Qz_max', '-121'))
        self.threshold_min = QLineEdit(settings.value('threshold_min', '0'))
        self.threshold_max = QLineEdit(settings.value('threshold_max', '1000000'))
        self.numbin = QLineEdit(settings.value('numbin', '500'))

        self.Angle_incidence = QLineEdit(self)
        self.Angle_incidence.setText(self.checkFloatValue(settings.value('Angle_incidence', '0.5')))
        self.x_Center = QLineEdit(self)
        self.x_Center.setText(self.checkFloatValue(settings.value('x_Center', '0')))
        self.y_Center = QLineEdit(self)
        self.y_Center.setText(self.checkFloatValue(settings.value('y_Center', '0')))
        self.distance = QLineEdit(self)
        self.distance.setText(self.checkFloatValue(settings.value('distance', '300')))
        self.pixel_x = QLineEdit(self)
        self.pixel_x.setText(self.checkFloatValue(settings.value('pixel_x', '73.2')))
        self.pixel_y = QLineEdit(self)
        self.pixel_y.setText(self.checkFloatValue(settings.value('pixel_y', '73.2')))
        self.lamda = QLineEdit(self)
        self.lamda.setText(self.checkFloatValue(settings.value('lamda', '1.24')))
        self.Qr_min = QLineEdit(self)
        self.Qr_min.setText(self.checkFloatValue(settings.value('Qr_min', '-121')))
        self.Qr_max = QLineEdit(self)
        self.Qr_max.setText(self.checkFloatValue(settings.value('Qr_max', '-121')))
        self.Qz_min = QLineEdit(self)
        self.Qz_min.setText(self.checkFloatValue(settings.value('Qz_min', '-121')))
        self.Qz_max = QLineEdit(self)
        self.Qz_max.setText(self.checkFloatValue(settings.value('Qz_max', '-121')))
        self.threshold_min = QLineEdit(self)
        self.threshold_min.setText(self.checkFloatValue(settings.value('threshold_min', '0')))
        self.threshold_max = QLineEdit(self)
        self.threshold_max.setText(self.checkFloatValue(settings.value('threshold_max', '1000000')))
        self.numbin = QLineEdit(self)
        self.numbin.setText(self.checkFloatValue(settings.value('numbin', '500')))

        # 将各个参数设为类属性
        self.Angle_incidence_value = float(self.Angle_incidence.text())
        self.x_Center_value = float(self.x_Center.text())
        self.y_Center_value = float(self.y_Center.text())
        self.distance_value = float(self.distance.text())
        self.pixel_x_value = float(self.pixel_x.text())
        self.pixel_y_value = float(self.pixel_y.text())
        self.lamda_value = float(self.lamda.text())
        self.Qr_min_value = float(self.Qr_min.text())
        self.Qr_max_value = float(self.Qr_max.text())
        self.Qz_min_value = float(self.Qz_min.text())
        self.Qz_max_value = float(self.Qz_max.text())
        self.threshold_min_value = float(self.threshold_min.text())
        self.threshold_max_value = float(self.threshold_max.text())
        self.numbin_value = float(self.numbin.text())

        # 绑定文本框的输入与类属性
        self.Angle_incidence.editingFinished.connect(
            lambda: self.update_value('Angle_incidence', self.Angle_incidence.text())
        )
        self.x_Center.editingFinished.connect(
            lambda: self.update_value('x_Center', self.x_Center.text())
        )
        self.y_Center.editingFinished.connect(
            lambda: self.update_value('y_Center', self.y_Center.text())
        )
        self.distance.editingFinished.connect(
            lambda: self.update_value('distance', self.distance.text())
        )
        self.pixel_x.editingFinished.connect(
            lambda: self.update_value('pixel_x', self.pixel_x.text())
        )
        self.pixel_y.editingFinished.connect(
            lambda: self.update_value('pixel_y', self.pixel_y.text())
        )
        self.lamda.editingFinished.connect(
            lambda: self.update_value('lamda', self.lamda.text())
        )
        self.Qr_min.editingFinished.connect(
            lambda: self.update_value('Qr_min', self.Qr_min.text())
        )
        self.Qr_max.editingFinished.connect(
            lambda: self.update_value('Qr_max', self.Qr_max.text())
        )
        self.Qz_min.editingFinished.connect(
            lambda: self.update_value('Qz_min', self.Qz_min.text())
        )
        self.Qz_max.editingFinished.connect(
            lambda: self.update_value('Qz_max', self.Qz_max.text())
        )
        self.threshold_min.editingFinished.connect(
            lambda: self.update_value('threshold_min', self.threshold_min.text())
        )
        self.threshold_max.editingFinished.connect(
            lambda: self.update_value('threshold_max', self.threshold_max.text())
        )
        self.numbin.editingFinished.connect(
            lambda: self.update_value('numbin', self.numbin.text())
        )

        self.Angle_incidence.editingFinished.connect(self.update_image_widget_finished)
        self.x_Center.editingFinished.connect(self.update_image_widget_finished)
        self.y_Center.editingFinished.connect(self.update_image_widget_finished)
        self.distance.editingFinished.connect(self.update_image_widget_finished)
        self.pixel_x.editingFinished.connect(self.update_image_widget_finished)
        self.pixel_y.editingFinished.connect(self.update_image_widget_finished)
        self.lamda.editingFinished.connect(self.update_image_widget_finished)
        self.Qr_min.editingFinished.connect(self.update_image_widget_finished)
        self.Qr_max.editingFinished.connect(self.update_image_widget_finished)
        self.Qz_min.editingFinished.connect(self.update_image_widget_finished)
        self.Qz_max.editingFinished.connect(self.update_image_widget_finished)
        self.threshold_min.editingFinished.connect(self.update_image_widget_finished)
        self.threshold_max.editingFinished.connect(self.update_image_widget_finished)
        # self.numbin.editingFinished.connect(self.update_image_widget)

        # 创建布局
        layout = QGridLayout(self)

        layout.addWidget(QLabel('入射角:'), 0, 0)
        layout.addWidget(self.Angle_incidence, 0, 1)
        layout.addWidget(QLabel('圆心-X：'), 0, 2)
        layout.addWidget(self.x_Center, 0, 3)
        layout.addWidget(QLabel('圆心-Y：'), 0, 4)
        layout.addWidget(self.y_Center, 0, 5)
        layout.addWidget(QLabel('距离：'), 0, 6)
        layout.addWidget(self.distance, 0, 7)
        layout.addWidget(QLabel('像素-X:'), 1, 0)
        layout.addWidget(self.pixel_x, 1, 1)
        layout.addWidget(QLabel('像素-Y:'), 1, 2)
        layout.addWidget(self.pixel_y, 1, 3)
        layout.addWidget(QLabel('波长：'), 1, 4)
        layout.addWidget(self.lamda, 1, 5)
        layout.addWidget(QLabel('切图Qr_min：'), 2, 0)
        layout.addWidget(self.Qr_min, 2, 1)
        layout.addWidget(QLabel('切图Qr_max：'), 2, 2)
        layout.addWidget(self.Qr_max, 2, 3)
        layout.addWidget(QLabel('切图Qz_min：'), 2, 4)
        layout.addWidget(self.Qz_min, 2, 5)
        layout.addWidget(QLabel('切图Qr_max：'), 2, 6)
        layout.addWidget(self.Qz_max, 2, 7)
        layout.addWidget(QLabel('Mask_min'), 3, 0)
        layout.addWidget(self.threshold_min, 3, 1)
        layout.addWidget(QLabel('Mask_max'), 3, 2)
        layout.addWidget(self.threshold_max, 3, 3)
        layout.addWidget(QLabel('一维精度：'), 3, 4)
        layout.addWidget(self.numbin, 3, 5)

    def checkFloatValue(self, value):
        try:
            float_value = float(value)
            return str(float_value)
        except ValueError:
            return '0.0'

    def closeEvent(self, event):
        # Save current settings
        settings = QSettings('mycompany', 'myapp')
        settings.setValue('Angle_incidence', self.Angle_incidence.text())
        settings.setValue('x_Center', self.x_Center.text())
        settings.setValue('y_Center', self.y_Center.text())
        settings.setValue('distance', self.distance.text())
        settings.setValue('pixel_x', self.pixel_x.text())
        settings.setValue('pixel_y', self.pixel_y.text())
        settings.setValue('lamda', self.lamda.text())

        event.accept()

    def update_image_widget_finished(self):
        if self.image_widget.windowstate == 3:
            self.image_widget.calculate_integral()
            return
        if self.image_layout.rb1.isChecked():
            self.image_widget.update_image()
        elif self.image_layout.rb2.isChecked():
            self.image_widget.Cut()

    def update_image_widget(self):
        try:
            self.Angle_incidence_value = float(self.Angle_incidence.text())
            self.x_Center_value = float(self.x_Center.text())
            self.y_Center_value = float(self.y_Center.text())
            self.distance_value = float(self.distance.text())
            self.pixel_x_value = float(self.pixel_x.text())
            self.pixel_y_value = float(self.pixel_y.text())
            self.lamda_value = float(self.lamda.text())
            self.Qr_min_value = float(self.Qr_min.text())
            self.Qr_max_value = float(self.Qr_max.text())
            self.Qz_min_value = float(self.Qz_min.text())
            self.Qz_max_value = float(self.Qz_max.text())
            self.threshold_min_value = float(self.threshold_min.text())
            self.threshold_max_value = float(self.threshold_max.text())
            self.numbin_value = float(self.numbin.text())

            self.image_widget.update_parameters(self)
        except:
            return



    def _get_float_or_default(self, input_str):
        try:
            value = float(input_str)
        except ValueError:
            value = -121
        return value
    def set_image_layout(self, image_layout):
        self.image_layout = image_layout

    def update_value(self, key, text):
        try:
            value = float(text) if text != '' else 0.0
        except ValueError:
            value = getattr(self, key + '_value', 0.0)
        setattr(self, key + '_value', value)
        self.update_image_widget()

class BatchProcessor(QWidget):
    def __init__(self, image_widget, image_layout):
        super().__init__()

        self.image_widget = image_widget
        self.image_layout = image_layout

        # 创建控件
        self.folder_label = QLabel("选择文件夹：")
        self.folder_path_label = QLabel()
        self.folder_select_button = QPushButton("选择")

        self.pattern_label = QLabel("文件名匹配模式：")
        self.pattern_input = QLineEdit()
        self.pattern_input.setText('*.tif')
        self.process_button = QPushButton("批量处理")
        self.hotmap_button = QPushButton("原位热图预览")

        self.export_image_check = QCheckBox("导出图片")
        self.export_curve_check = QCheckBox("导出一维曲线")
        self.background_removal_check = QCheckBox("扣背底")
        self.background_init_img = QLineEdit()
        self.background_init_img.setPlaceholderText('init_img')
        self.background_init_img.setText('1')
        self.background_init_img.setFixedWidth(100)
        self.background_min = QLineEdit()
        self.background_min.setPlaceholderText('1D_min')
        self.background_min.setFixedWidth(100)
        self.background_max = QLineEdit()
        self.background_max.setPlaceholderText('1D_max')
        self.background_max.setFixedWidth(100)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        self.insitu_txt_button = QPushButton('原位文件导入')
        self.insitu_txt_button.setFixedWidth(220)
        self.insitu_txt_label = QLabel()

        self.stop_button = QPushButton('停止')

        # 设置布局
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_path_label)
        folder_layout.addWidget(self.folder_select_button)

        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(self.pattern_label)
        pattern_layout.addWidget(self.pattern_input)

        check_layout = QHBoxLayout()
        check_layout.addWidget(QLabel("请选择导出类型:"))
        check_layout.addWidget(self.export_image_check)
        check_layout.addWidget(self.export_curve_check)
        check_layout.addWidget(self.background_removal_check)
        check_layout.addWidget(QLabel("扣背底参数:"))
        check_layout.addWidget(self.background_init_img)
        check_layout.addWidget(self.background_min)
        check_layout.addWidget(self.background_max)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.hotmap_button)
        button_layout.addWidget(self.progress_bar)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.insitu_txt_button)
        input_layout.addWidget(self.insitu_txt_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(folder_layout)
        main_layout.addLayout(pattern_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(check_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(input_layout)




        self.setLayout(main_layout)
        self.output_matrix = None
        # 连接信号槽
        self.folder_select_button.clicked.connect(self.select_folder)
        self.process_button.clicked.connect(self.batch_process)
        self.hotmap_button.clicked.connect(self.hotmap_plot)
        self.insitu_txt_button.clicked.connect(self.insitu_input)
        self.stop_button.clicked.connect(self.stop_loop)
        self.background_init_img.textChanged.connect(self.update_bg_init_param)

    def update_bg_init_param(self, text):
        try:
            self.background_init_img_value = int(text)
        except ValueError:
            self.background_init_img_value = 1

    def insitu_input(self):
        # 显示文件对话框，以选择输入文件
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                   "Text Files (*.txt);;All Files (*)", options=options)

        # 如果选择了文件，则读取该文件并将其解析为二维数组
        if file_name:
            # 加载文本文件，并将数据存储在一个numpy数组中
            data = np.loadtxt(file_name)
            self.output_matrix = data
            self.insitu_txt_label.setText(file_name)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder_path:
            self.folder_path_label.setText(folder_path)

    def batch_process(self):

        # Reset the stop flag
        self.reset_stop_flag()

        folder_path = self.folder_path_label.text()
        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "警告", "请选择有效的文件夹！")
            return

        pattern_str = self.pattern_input.text()
        if not pattern_str:
            QMessageBox.warning(self, "警告", "请指定文件名匹配模式！")
            return

        # 寻找符合通配符模式的文件
        file_list = sorted(glob.glob(folder_path + "/*" + pattern_str))
        if not file_list:
            QMessageBox.warning(self, "警告", "没有找到符合条件的文件！")
            return

        total_files = len(file_list)
        # 开启原位处理状态码
        self.image_layout.insitustate = 1

        # 扣背景
        if self.background_removal_check.isChecked():
            self.x_bg = None
            # 首先需要绘制一维图片
            index = int(self.background_init_img.text()) - 1
            self.filename = file_list[index]
            x, y = self.export_integral_data()
            try:
                self.xmin = float(self.background_min.text())
            except ValueError:
                self.xmin = None
            try:
                self.xmax = float(self.background_max.text())
            except ValueError:
                self.xmax = None
            remover = BackgroundRemover(x, y, self.xmin, self.xmax)
            # remover.interactive_plot()
            self.x_bg = remover.remove_background()

            # 循环询问是否需要重新计算背景
            while True:
                reply = QMessageBox.question(self, '确认', '是否确定此背景曲线？',
                                                       QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    break
                else:
                    # plt.close('all')
                    # remover = BackgroundRemover(x, y, self.xmin, self.xmax)
                    # self.x_bg = remover.remove_background()
                    return


        output = []
        output_bk = []
        # 遍历符合条件的文件并进行处理
        for i, filepath in enumerate(file_list):

            if self.stop_flag:
                self.progress_bar.setValue(0)
                QMessageBox.warning(self, 'Warning', 'The process was stopped by the user.')
                return

            filename = os.path.basename(filepath)

            # 设置image_widget的filename并调用Cut()、update_image()和export_image()
            self.filename = filepath
            self.image_widget.update_batch_processor_filename()
            self.image_layout.update_batch_processor_filename()

            # 如果一维被勾选上
            if self.export_curve_check.isChecked():
                try:
                    x, y = self.export_integral_data()
                    if i == 0:
                        output.append(x)
                    output.append(y)

                except:
                    QMessageBox.warning(self, "Warning", "积分中止！", QMessageBox.Ok)
                    self.image_layout.insitustate = 0
                    return

            # 如果二维导出被勾选上
            if self.export_image_check.isChecked():
                if self.image_layout.rb2.isChecked():
                    self.image_widget.Cut()
                if self.image_layout.rb1.isChecked():
                    self.image_widget.update_image()
                self.image_layout.export_image()


            # 更新进度条
            progress = (i + 1) / total_files * 100
            self.progress_bar.setValue(int(round(progress)))
            # 强制处理未处理的事件，以便更新界面
            QCoreApplication.processEvents()

            plt.close('all')
            fig, ax = plt.subplots()
            # 扣背底循环
            if self.background_removal_check.isChecked() and self.x_bg is not None:
                x, y = self.export_integral_data()
                # 搜索self.x_bg在x中对应的索引
                idx = [np.abs(x - xi).argmin() for xi in self.x_bg]
                # 获取对应的y值
                y_bg = y[idx]
                # 使用样条插值
                interp_spline = make_interp_spline(self.x_bg, y_bg, k=2)
                y_bg_interp = interp_spline(x)
                # 扣除背景曲线，得到扣除背景后的曲线
                y_corrected = y - y_bg_interp
                # 导出数据
                if i == 0:
                    output_bk.append(x)
                output_bk.append(y_corrected)

                # 清空Axes并绘制新的数据
                ax.clear()
                ax.plot(x, y_corrected)
                ax.set_title('Iteration %d' % (i + 1))
                # 刷新画布
                fig.canvas.draw()
                # 保证窗口能够响应事件
                plt.pause(0.001)


        # 显示窗口
        plt.show()

        # 如果一维被勾选上，导出txt数据
        if self.export_curve_check.isChecked():
            # 定义 1D 文件夹
            image_folder_path = os.path.join(self.image_layout.output_folder, '1D')
            file_path = os.path.join(image_folder_path, 'output.txt')

            # 转换output为numpy矩阵
            output_matrix = np.column_stack(output)
            # 保存矩阵为txt文件
            np.savetxt(file_path, output_matrix, fmt='%.6f', delimiter=' ')
            self.output_matrix = output_matrix
            self.insitu_txt_label.setText(file_path)
        self.image_layout.insitustate = 0
        # QMessageBox.information(None, "完成", "已完成！")
        # 如果一维被勾选上，导出txt数据
        if self.background_removal_check.isChecked():
            # 定义 1D 文件夹
            image_folder_path = os.path.join(self.image_layout.output_folder, '1D')
            file_path = os.path.join(image_folder_path, 'output_subBk.txt')

            # 转换output为numpy矩阵
            output_bk_matrix = np.column_stack(output_bk)
            # 保存矩阵为txt文件
            np.savetxt(file_path, output_bk_matrix, fmt='%.6f', delimiter=' ')
            self.output_matrix_bk = output_bk_matrix
            # self.insitu_txt_label.setText(file_path)

        self.image_layout.insitustate = 0

        plt.close()

    # def on_click(self, event):
    #    The code is dedicated to the beloved Sherry, as a token of affection from Yufeng. 2023-04-29
    #     # 如果鼠标左键被点击
    #     if event.button == 1:
    #         # 获取鼠标点击的x坐标和y坐标
    #         x = event.xdata
    #         y = event.ydata
    #         if x is not None and y is not None:
    #             # 在该位置绘制一个点
    #             self.ax.plot(x, y, 'ro')
    #
    #             # 将鼠标点击的x坐标和y坐标添加到列表中
    #             self.clicks.append((x, y))
    #
    #             # 记录下鼠标点击的x坐标和对应的y值
    #             print('x =', x, 'y =', y)
    #
    #         # 刷新图形
    #         self.fig.canvas.draw_idle()
    #     # 如果鼠标右键被点击
    #     elif event.button == 3:
    #         # 对所有鼠标点击的x和y坐标进行样条插值
    #         xs = [click[0] for click in self.clicks]
    #         ys = [click[1] for click in self.clicks]
    #         spl = make_interp_spline(xs, ys, k=2)
    #         ys_interp = spl(xs)
    #
    #         # 在整个x范围内绘制样条插值曲线
    #         xmin, xmax = self.x.min(), self.x.max()
    #         xs_interp = np.linspace(xmin, xmax, 100)
    #         ys_interp = spl(xs_interp)
    #         self.ax.plot(xs_interp, ys_interp)
    #
    #         # 刷新图形
    #         self.fig.canvas.draw_idle()
    #     # 如果鼠标中键被点击
    #     elif event.button == 2:
    #         # 获取鼠标点击的x坐标和y坐标
    #         x = event.xdata
    #         y = event.ydata
    #         if x is not None and y is not None:
    #             # 在该位置移除一个点
    #             idx = None
    #             for i, click in enumerate(self.clicks):
    #                 if np.abs(click[0] - x) < 0.01 and np.abs(click[1] - y) < 0.01:
    #                     idx = i
    #                     break
    #             if idx is not None:
    #                 del self.clicks[idx]
    #                 self.ax.lines.pop(-1)
    #                 for click in self.clicks:
    #                     self.ax.plot(click[0], click[1], 'ro')
    #                 print('Removed point at x =', x, 'y =', y)
    #
    #             # 刷新图形
    #             self.fig.canvas.draw_idle()

    def hotmap_plot(self):
        try:
            if self.output_matrix.any():
                output_matrix = self.output_matrix
                # 提取x轴和y轴数据
                x = output_matrix[:, 0]
                y = output_matrix[:, 1:]

                # 创建一个新的Figure对象和Axes对象
                fig, ax = plt.subplots()
                # 创建一个新的矩阵，只包含y轴的数据
                y_matrix = y.T
                # 绘制热图
                im = ax.imshow(y_matrix, aspect='auto', cmap='jet', origin='lower',
                               extent=[x.min(), x.max(), 1, len(y_matrix)],
                               interpolation='bilinear')  # 添加双线性插值
                cbar = fig.colorbar(im, ax=ax)

                # 设置x轴和y轴的标签
                ax.set_xlabel('X-axis label')
                ax.set_ylabel('Y-axis label')
                cbar.set_label('Intensity')

                # 显示热图
                plt.show()
            else:
                QMessageBox.warning(self, "Warning", "请先进行一维曲线的批量处理或导入原位数据文件！", QMessageBox.Ok)
        except:
            QMessageBox.warning(self, "Warning", "请先进行一维曲线的批量处理或导入原位数据文件！", QMessageBox.Ok)

    def export_integral_data(self):
        try:
            # 创建 1D 文件夹
            self.image_layout.file_name = self.filename
            self.image_widget.file_name = self.filename
            folder_name = os.path.splitext(os.path.basename(self.image_layout.file_name))[0]
            image_folder_path = os.path.join(self.image_layout.output_folder, '1D')
            os.makedirs(image_folder_path, exist_ok=True)
            file_path = os.path.join(image_folder_path, folder_name + '.jpg')

            x, y = self.image_widget.calculate_integral()
            self.image_widget.fig.savefig(file_path, dpi=300) #导出一维图片的jpg格式

            # mask = (x >= float(self.batch_processor.background_min.text())) & (
            #             x <= float(self.batch_processor.background_max.text()))
            # x_selected = x[mask]
            # y_selected = y[mask]
            return x, y

        except:
            return None, None

    def stop_loop(self):
        self.stop_flag = True

    def reset_stop_flag(self):
        self.stop_flag = False

        # Process events to ensure the UI is updated
        loop = QEventLoop()
        QTimer.singleShot(0, loop.quit)
        loop.exec_()

class FileExplorer(QWidget):
    def __init__(self, image_layout, parent=None):
        super().__init__(parent)

        # 创建QFileSystemModel和QTreeView对象
        self.model = QFileSystemModel()
        self.model.setRootPath('')
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        # self.tree.setRootIndex(self.model.index(QDir.currentPath()))

        # 隐藏不需要的列和标题栏，禁用排序
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)
        self.tree.setHeaderHidden(True)
        self.tree.setSortingEnabled(False)

        # 获取当前目录的QModelIndex对象
        root_index = self.model.index(QDir.currentPath())

        # 设置树视图的根项为当前目录
        # self.tree.setRootIndex(root_index)

        # 遍历从根目录到当前目录的所有路径并展开
        index = root_index
        while index.isValid():
            self.tree.expand(index)
            index = index.parent()

        # 创建一个QLabel对象显示文件路径
        self.file_path = QLabel()

        # 将QTreeView和QLabel添加到QWidget上
        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addWidget(self.file_path)
        self.setLayout(layout)

        # 创建一个 ImageLayout 实例
        self.image_layout = image_layout

        # 连接selectionChanged信号和槽函数
        self.tree.selectionModel().selectionChanged.connect(self.on_selection_changed)
        # 连接QTreeView的双击信号和选择文件的槽函数
        self.tree.doubleClicked.connect(self.on_tree_double_clicked)

    def on_selection_changed(self):
        # 获取当前选中的文件路径并设置到QLabel上
        index = self.tree.currentIndex()
        file_path = self.model.filePath(index)
        self.file_path.setText(file_path)
        # 检查是否选中了一个文件并且文件的扩展名为.tif或.jpg
        # if not self.model.isDir(index) and file_path.lower().endswith(('.tif', '.jpg')):
        #     # 实例化 ImageLayout 类并调用 update_image() 方法
        #     image_layout = ImageLayout(file_name = file_path)
        #     image_layout.update_image()

    def on_tree_double_clicked(self, index):
        # 获取当前双击的文件路径
        file_path = self.model.filePath(index)
        # 检查是否选中了一个文件并且文件的扩展名为.tif或.jpg
        if not self.model.isDir(index) and file_path.lower().endswith(('.tif', '.jpg' ,)):
            self.image_layout.set_file_name(file_path)
            self.image_layout.update_image(file_path)

            if not self.image_layout.textbox_startAngle.text():
                self.image_layout.textbox_startAngle.setText('-180')
            if not self.image_layout.textbox_endAngle.text():
                self.image_layout.textbox_endAngle.setText('180')
            if not self.image_layout.textbox_innerRadius.text():
                self.image_layout.textbox_innerRadius.setText('0')
            if not self.image_layout.textbox_outerRadius.text():
                self.image_layout.textbox_outerRadius.setText('1000')

        else:
            try:
                self.image_layout.set_file_name(file_path)
                self.image_layout.update_image(file_path)

                if not self.image_layout.textbox_startAngle.text():
                    self.image_layout.textbox_startAngle.setText('-180')
                if not self.image_layout.textbox_endAngle.text():
                    self.image_layout.textbox_endAngle.setText('180')
                if not self.image_layout.textbox_innerRadius.text():
                    self.image_layout.textbox_innerRadius.setText('0')
                if not self.image_layout.textbox_outerRadius.text():
                    self.image_layout.textbox_outerRadius.setText('1000')

            except:
                QMessageBox.warning(self, "Error",
                                    "The selected file cannot be read. Please select a valid TIFF or JPG file.")


class BackgroundRemover:
    def __init__(self, x, y, xmin=None, xmax=None):
        self.x = x
        self.y = y
        self.xmin = xmin
        self.xmax = xmax
        self.background_points = []
        self.background_dots = []  # 存储所有的红点
        self.fig, self.ax = plt.subplots()

        # 绑定事件处理器
        # self.cid_button_press = self.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
        # self.cid_button_release = self.fig.canvas.mpl_connect('button_release_event', self.on_button_release)
        # # self.cid_mouse_move = self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        self.background_points = list(set(self.background_points))
        self.dragging_point = None

    def validate_input(self):
        if self.xmin is not None and self.xmax is not None:
            if self.xmin >= self.xmax or self.xmin > np.max(self.x) or self.xmax < np.min(self.x):
                raise ValueError("Invalid input: x must be in the range [xmin, xmax].")
            mask = (self.x >= self.xmin) & (self.x <= self.xmax)
            self.x = self.x[mask]
            self.y = self.y[mask]
        elif self.xmin is not None or self.xmax is not None:
            raise ValueError("Both xmin and xmax must be provided or both must be None.")

    def plot_initial_data(self):
        self.validate_input()
        self.ax.plot(self.x, self.y, label='Original Data')
        self.background_points.append((self.x[0], self.y[0]))
        self.background_points.append((self.x[-1], self.y[-1]))
        # 创建和存储所有的红点
        for point in self.background_points:
            dot, = self.ax.plot(point[0], point[1], 'ro')
            self.background_dots.append(dot)
        self.ax.legend()

    def on_left_click(self, event):
        if event.inaxes != self.ax:
            return
        x = event.xdata
        # Get the nearest y value to the clicked x value
        idx = np.abs(self.x - x).argmin()
        y = self.y[idx]
        self.background_points.append((x, y))
        self.background_dots.append(self.ax.plot(x, y, 'ro')[0])
        self.update_background()

    def on_right_click(self, event):
        if event.inaxes != self.ax:
            return
        if len(self.background_points) <= 2:
            print("Cannot remove initial points.")
            return
        x = event.xdata
        # Get the nearest y value to the clicked x value
        idx = np.abs(self.x - x).argmin()
        nearest_idx = np.argmin([np.abs(p[0] - x) for p in self.background_points])
        nearest_point = self.background_points[nearest_idx]
        min_distance = np.sqrt((x - nearest_point[0]) ** 2 + (self.y[idx] - nearest_point[1]) ** 2)
        distance_threshold = 20  # Custom threshold, you can adjust as needed
        if min_distance > distance_threshold:
            print("No points within the threshold.")
            return
        # Remove the nearest point from the background points list
        del self.background_points[nearest_idx]
        # Remove the corresponding dot from the plot
        self.background_dots[nearest_idx].remove()
        del self.background_dots[nearest_idx]
        # Remove the corresponding line from the plot
        self.ax.lines.pop(nearest_idx)
        # Redraw the remaining background points
        self.ax.legend()
        plt.draw()
        self.update_background()

    # def on_button_press(self, event):
    #     if event.button == 1:  # 左键
    #         self.dragging_point = self.find_nearest_point(event)
    #         if self.dragging_point is not None:
    #             self.dragging_line = self.find_line(self.dragging_point)
    # #
    # def on_button_release(self, event):
    #     if event.button == 1:  # 左键
    #         self.dragging_point = None
    #         self.dragging_line = None
    #
    # def on_mouse_move(self, event):
    #     if not self.dragging_point:
    #         return
    #
    #     if event.inaxes != self.ax:
    #         return
    #
    #     new_x, new_y = event.xdata, self.y[np.abs(self.x - event.xdata).argmin()]
    #     line = self.find_line(self.dragging_point)
    #     if line is not None:
    #         line.set_data([new_x], [new_y])
    #         plt.draw()
    #
    #         # Update the background point and update the background curve
    #         point_idx = self.background_points.index(self.dragging_point)
    #         self.background_points[point_idx] = (new_x, new_y)
    #         self.update_background()
    #
    #         self.dragging_point = (new_x, new_y)

    def find_nearest_point(self, event):
        if event.inaxes != self.ax:
            return None

        x = event.xdata
        # Get the nearest y value to the clicked x value
        idx = np.abs(self.x - x).argmin()
        nearest_point = self.background_points[np.argmin([np.abs(p[0] - x) for p in self.background_points])]
        min_distance = np.sqrt((x - nearest_point[0]) ** 2 + (self.y[idx] - nearest_point[1]) ** 2)

        distance_threshold = 50  # Custom threshold

        if min_distance > distance_threshold:
            return None

        return nearest_point

    def find_line(self, point):
        for line in self.ax.lines:
            if np.isclose(line.get_xdata()[0], point[0]) and np.isclose(line.get_ydata()[0], point[1]):
                return line
        return None

    def update_background_point(self, point_idx, new_x, new_y):
        self.background_points[point_idx] = (new_x, new_y)
        self.update_background()

    def update_background(self):
        self.background_points = list(set(self.background_points))
        self.background_points.sort(key=lambda p: p[0])
        x_bg, y_bg = zip(*self.background_points)
        x_bg = np.array(x_bg)
        y_bg = np.array(y_bg)
        if len(x_bg) < 3:
            print("At least three background points are required.")
            return

        if len(set(x_bg)) != len(x_bg):
            print("Duplicate x coordinates are not allowed.")
            return

        interp_spline = make_interp_spline(x_bg, y_bg, k=2)
        xnew = np.linspace(self.x[0], self.x[-1], len(self.x))
        ynew = interp_spline(xnew)
        if hasattr(self, 'background_line'):
            self.background_line.set_data(xnew, ynew)
        else:
            self.background_line, = self.ax.plot(xnew, ynew, 'r-', label='Background')
        self.ax.legend()
        plt.draw()

    def on_key_press(self, event):
        if event.key == 'enter':
            plt.close(self.fig)

    def interactive_plot(self):
        self.plot_initial_data()
        self.fig.canvas.mpl_connect('button_press_event', lambda event: self.on_left_click(
            event) if event.button == 1 else self.on_right_click(event))
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        plt.show()

    def remove_background(self):
        self.plot_initial_data()
        self.fig.canvas.mpl_connect('button_press_event', lambda event: self.on_left_click(
            event) if event.button == 1 else self.on_right_click(event))
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        while plt.get_fignums():
            plt.pause(0.1)

        if not self.background_points:
            print("No background points selected.")
            return None

        # Call the fit_background() function to perform the background fitting
        try:
            xnew, ynew = self.fit_background()
            ynew = self.y-ynew
            plt.plot(xnew, ynew, label="Result")
            plt.legend()
            plt.show()

            return self.x_bg

        except:
            self.x_bg = None
            return self.x_bg

    def fit_background(self):
        self.background_points.sort(key=lambda p: p[0])
        x_bg, y_bg = zip(*self.background_points)
        x_bg = np.array(x_bg)
        y_bg = np.array(y_bg)
        self.x_bg = x_bg
        interp_spline = make_interp_spline(x_bg, y_bg, k=2)
        xnew = np.linspace(self.x[0], self.x[-1], len(self.x))
        ynew = interp_spline(xnew)
        return xnew, ynew

if __name__ == '__main__':

    app = QApplication(sys.argv)
    # 创建主窗口
    window = MainWindow()
    # 获取当前屏幕的大小
    screen_size = QDesktopWidget().availableGeometry().size()
    # 设置主窗口的大小为屏幕大小的 0.8 倍
    window.resize(int(screen_size.width() * 0.8), int(screen_size.height() * 0.8))
    # 将主窗口居中显示
    window.move(int(screen_size.width() * 0.1), int(screen_size.height() * 0.1))
    window.show()
    sys.exit(app.exec_())

