#!/usr/bin/python
from __future__ import division

from PyQt5.QtWidgets import QWidget, QLabel, QFrame, QPushButton, QHBoxLayout, QVBoxLayout, QScrollArea, QSizePolicy, QGroupBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QPalette, QPixmap

import os
import rospkg

# Size of Primitive Widget
PRIMITIVE_WIDTH = 100
PRIMITIVE_HEIGHT = 120

# Spacings for the Program Widget
H_SPACING = 20
V_SPACING = 30

# Minimum number of visible primitives on screen
MIN_PRIMITIVE = 5

# Color Palettes
gray_palette = QPalette()
gray_palette.setColor(QPalette.Background, QColor("gainsboro"))
white_palette = QPalette()
white_palette.setColor(QPalette.Background, QColor("ghostwhite"))
current_index_palette = QPalette()
current_index_palette.setColor(QPalette.Background, QColor("lightskyblue"))
executed_primitive_palette = QPalette()
executed_primitive_palette.setColor(QPalette.Background, QColor("cornflowerblue"))


class EUPWidget(QWidget):
    def __init__(self):
        super(EUPWidget, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('EUP Widget')

        self.vbox = QVBoxLayout(self)
        self.vbox.setAlignment(Qt.AlignTop)

        self.low_buttons = QWidget()
        self.low_buttons_layout = QHBoxLayout()
        self.low_buttons_layout.setAlignment(Qt.AlignCenter)

        self.panda_program_widget = PandaProgramWidget(self)
        self.adjust_parameters_frame = QGroupBox(self)
        self.adjust_parameters_frame.setTitle('Primitive parameters:')
        self.go_start_button = QExpandingPushButton("Go to start pose")
        self.execute_one_step_button = QExpandingPushButton("Execute one step")
        self.revert_one_step_button = QExpandingPushButton("Revert one step")
        self.execute_rest_button = QExpandingPushButton("Execute rest of program")
        self.revert_to_beginning_button = QExpandingPushButton("Revert to beginning")

        size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.adjust_parameters_frame.setSizePolicy(size_policy)

        self.go_start_button.clicked.connect(self.go_to_starting_state)
        self.execute_one_step_button.clicked.connect(self.execute_one_step)
        self.revert_one_step_button.clicked.connect(self.revert_one_step)

        self.low_buttons_layout.addWidget(self.go_start_button)
        self.low_buttons_layout.addWidget(QVerticalLine())
        self.low_buttons_layout.addWidget(self.execute_one_step_button)
        self.low_buttons_layout.addWidget(self.revert_one_step_button)
        self.low_buttons_layout.addWidget(QVerticalLine())
        self.low_buttons_layout.addWidget(self.execute_rest_button)
        self.low_buttons_layout.addWidget(self.revert_to_beginning_button)
        self.low_buttons.setLayout(self.low_buttons_layout)

        self.vbox.addWidget(self.panda_program_widget)
        self.vbox.addWidget(self.adjust_parameters_frame)
        self.vbox.addWidget(self.low_buttons)

    def go_to_starting_state(self):
        self.panda_program_widget.interpreter.go_to_starting_state()
        self.panda_program_widget.updateWidget()
    def execute_one_step(self):
        self.panda_program_widget.interpreter.execute_one_step()
        self.panda_program_widget.updateWidget()
    def revert_one_step(self):
        self.panda_program_widget.interpreter.revert_one_step()
        self.panda_program_widget.updateWidget()

    def sizeHint(self):
        return QSize(1280, 720)

    def minimumSizeHint(self):
        return QSize(1280, 720)


class PandaProgramWidget(QGroupBox):
    def __init__(self, parent):
        super(PandaProgramWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.program = None
        self.primitive_widget_list = []
        program_size = 0
        self.setTitle('No program loaded yet')

        # Create layout for program widget and add Scroll Area
        self.widget_layout = QHBoxLayout(self)
        self.program_scroll_area = QScrollArea(self)
        self.widget_layout.addWidget(self.program_scroll_area)
        self.program_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.program_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set the policy to expand on horizontal axis
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)

        # Create container and layout for PandaPrimitiveWidgets
        self.program_widget = QWidget(self)
        self.program_widget_layout = QHBoxLayout(self.program_widget)
        self.program_widget_layout.setAlignment(Qt.AlignLeft)
        self.program_widget.setSizePolicy(sizePolicy)

        # Color the Program area
        self.setAutoFillBackground(True)
        self.setPalette(gray_palette)
        self.program_widget.setAutoFillBackground(True)
        self.program_widget.setPalette(gray_palette)

        # Add scrolling area
        self.program_scroll_area.setWidget(self.program_widget)
        self.program_widget.setGeometry(0, 0, (H_SPACING + PRIMITIVE_WIDTH)*program_size, V_SPACING + PRIMITIVE_HEIGHT)
        # self.program_scroll_area.resize(self.sizeHint())

    def addPrimitiveWidget(self, primitive):
        primitive_widget = PandaPrimitiveWidget(self.program_widget, primitive)
        self.primitive_widget_list.append(primitive_widget)
        self.program_widget_layout.addWidget(primitive_widget)

        program_length = self.program.get_program_length()
        if self.program_widget.width() < (H_SPACING + PRIMITIVE_WIDTH)*program_length:
            self.program_widget.setGeometry(0, 0, (H_SPACING + PRIMITIVE_WIDTH)*program_length, V_SPACING + PRIMITIVE_HEIGHT)

    def loadPandaInterpreter(self, interpreter):
        # TODO: self.program is redundant
        self.program = interpreter.loaded_program
        self.interpreter = interpreter
        self.setTitle(self.program.name + ':')
        for primitive in self.program.primitives:
            self.addPrimitiveWidget(primitive)
        self.updateWidget()

    def updateWidget(self):
        for i, primitive_widget in enumerate(self.primitive_widget_list):
            primitive_widget.updateWidget(i, self.interpreter.next_primitive_index)

    def sizeHint(self):
        return QSize((H_SPACING+PRIMITIVE_WIDTH)*MIN_PRIMITIVE, V_SPACING*3 + PRIMITIVE_HEIGHT)

    def minimumSizeHint(self):
        return QSize((H_SPACING+PRIMITIVE_WIDTH)*MIN_PRIMITIVE, V_SPACING*3 + PRIMITIVE_HEIGHT)


class PandaPrimitiveWidget(QFrame):
    def __init__(self, parent, panda_primitive):
        super(PandaPrimitiveWidget, self).__init__(parent)
        self.initUI(panda_primitive)

    def initUI(self, panda_primitive):
        # Create widget subcomponents
        self.primitive = panda_primitive
        self.primitive_label = QLabel()
        self.status_label = QLabel(str(panda_primitive.status.name))

        primitive_icon_path = os.path.join(rospkg.RosPack().get_path('panda_pbd'), 'resources',
                                           panda_primitive.__class__.__name__ + '.png')

        primitive_image = QPixmap(primitive_icon_path)
        self.primitive_label.setPixmap(primitive_image)

        # Add vertical layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.primitive_label)
        layout.addWidget(self.status_label)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)

        # Beautify QFrame and Color
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)

        self.setAutoFillBackground(True)
        self.setPalette(white_palette)

    def sizeHint(self):
        return QSize(PRIMITIVE_WIDTH, PRIMITIVE_HEIGHT)

    def updateWidget(self, own_index, program_current_index):
        self.status_label.setText(str(self.primitive.status.name))
        if  own_index < program_current_index:
            self.setPalette(executed_primitive_palette)
        elif own_index > program_current_index:
            self.setPalette(gray_palette)
        else:
            self.setPalette(current_index_palette)

class QVerticalLine(QFrame):
    def __init__(self, parent=None):
        super(QVerticalLine, self).__init__(parent)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

class QExpandingPushButton(QPushButton):
    def __init__(self, text='', parent=None):
        super(QExpandingPushButton, self).__init__(text, parent)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.setSizePolicy(sizePolicy)