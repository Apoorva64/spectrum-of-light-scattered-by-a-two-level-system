from typing import Any, Union, Dict
import math
from modules.auto_installer import install
from modules.main_window import Ui_MainWindow
from PyQt5 import QtCore, QtGui
from PyQt5 import QtWidgets
from modules.graph_classes import InelasticIntensity, laser_intensity_from_laser_waist_laser_power, \
    saturation_parameter_from_laser_intensity, ElasticIntensity, Intensity, NumbersGraph, \
    saturation_parameter_from_rabi_frequency, rabi_frequency_from_saturation_parameter, generalised_rabi_frequency, \
    ElasticInelasticTemperatureIntensity, DopplerBroadenedSpectrum
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
from qt_material import apply_stylesheet
import matplotlib as mpl
from bs4 import BeautifulSoup

install()  # empty


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    inputs: Dict[Union[str, Any], Union[Union[str, float, int], Any]]
    resized = QtCore.pyqtSignal()

    def __init__(self, color_dict, *args, **kwargs):
        """

        :param color_dict: Defines the colors that are going to be used to build the interface
        :param args: Main Window args
        :param kwargs: Main Window kwargs
        """
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # main window setup
        self.color_dict = color_dict
        self.setWindowTitle('Spectrum of light scattered by a quantum two-level system')
        self.setWindowIcon(QtGui.QIcon('images/logo.png'))

        # mpl setup
        self.graphs_to_update = []
        self.toolbar = NavigationToolbar(self.MplWidget.canvas, self)
        self.addToolBar(self.toolbar)
        self.scrollArea.setMinimumWidth(500)

        # defining line inputs
        self.inputs = {
            'saturation_parameter': "",
            'rabi_frequency': "",
            'laser_intensity': 1.0,
            'laser_power': 1.0,
            'laser_waist': 1.0,
            'saturation_intensity': 1.669,
            'detuning': 0.0,
            'gamma': 1.0,
            'temperature': 100,
            'angle': 90,
            'laser_intensity_error_mu': 0,
            'laser_intensity_error_sigma': 0,
            'laser_intensity_error_uniform': 0,
            'laser_intensity_error_random_resolution': 30,
        }
        self.inputs_objects = {
            'saturation_parameter': self.saturation_parameter_line_edit,
            'rabi_frequency': self.rabi_frequency_line_edit,
            'laser_intensity': self.laser_intensity_line_edit,
            'laser_power': self.laser_power_line_edit,
            'laser_waist': self.laser_waist_line_edit,
            'saturation_intensity': self.saturation_i_line_edit,
            'detuning': self.detuning_line_edit,
            'temperature': self.temperature_line_edit,
            'angle': self.angle_line_edit,
            'laser_intensity_error_mu': self.laser_intensity_error_mu_line_edit,
            'laser_intensity_error_sigma': self.laser_intensity_error_sigma_line_edit,
            'laser_intensity_error_uniform': self.laser_intensity_error_uniform_line_edit,
            'laser_intensity_error_random_resolution': self.laser_intensity_resolution_random_line_edit
        }

        # connecting events
        for key, item in self.inputs_objects.items():
            item.setText(str(self.inputs[key]))
            item.textChanged.connect(self.handle_inputs_visibility)
        self.update_graph_button.clicked.connect(self.update_graph)
        self.graphic_resolution_slider.valueChanged.connect(self.update_resolution)
        self.graph_span_slider.valueChanged.connect(self.update_graph_span)
        self.show_inelastic_intensity.stateChanged.connect(self.update_graph)
        self.show_elastic_intensity.stateChanged.connect(self.update_graph)
        self.show_elastic_inelastic_intensity.stateChanged.connect(self.update_graph)
        self.show_annotations_input.stateChanged.connect(self.update_graph)
        self.center_on_detuning_input.stateChanged.connect(self.update_graph)
        self.show_elastic_inelastic_temperature_intensity.stateChanged.connect(self.update_graph)
        self.convolution_kernel.stateChanged.connect(self.update_graph)

        self.handle_inputs()
        self.update_graph()

        # graphs
        self.graphs_number_objects = [InelasticIntensity(), ElasticIntensity(), Intensity(),
                                      ElasticInelasticTemperatureIntensity(), DopplerBroadenedSpectrum()]

        # setting the toolbox to the open the first container
        self.toolBox.setCurrentIndex(0)
        self.show_elastic_inelastic_intensity.setChecked(True)

    def keyPressEvent(self, event):
        """
        update graph on enter
        :param event:
        """
        if event.key() == QtCore.Qt.Key_Return:
            self.update_graph()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        """
        emit signal on resize
        :param event:
        :return:
        """
        self.resized.emit()
        # self.resize_graph()
        return super(QtWidgets.QMainWindow, self).resizeEvent(event)

    def update_resolution(self):
        """
        update the resolution of the graphs
        """
        NumbersGraph.resolution = self.graphic_resolution_slider.value()
        self.update_graph()

    def update_graph_span(self):
        """
        update the span of the graphs
        """
        NumbersGraph.span = math.exp(self.graph_span_slider.value() / 10) / 10
        self.update_graph()

    def handle_inputs_visibility(self):
        """
        handle the visibility of the text line inputs so that some inputs acts as a display and others works as
        a line edit
        """
        for key, item in self.inputs_objects.items():
            item.setEnabled(True)
        if self.rabi_frequency_line_edit.text() != "":
            for key, item in self.inputs_objects.items():
                if key not in ['rabi_frequency', 'detuning', 'angle', 'temperature', 'laser_intensity_error_mu',
                               'laser_intensity_error_sigma', 'laser_intensity_error_uniform']:
                    item.setEnabled(False)
        elif self.saturation_parameter_line_edit.text() != "":
            for key, item in self.inputs_objects.items():
                if key not in ['saturation_parameter', 'detuning', 'angle', 'temperature',
                               'laser_intensity_error_mu', 'laser_intensity_error_sigma',
                               'laser_intensity_error_uniform']:
                    item.setEnabled(False)
        elif self.laser_intensity_line_edit.text() != "":
            self.inputs_objects['laser_power'].setEnabled(False)
            self.inputs_objects['laser_waist'].setEnabled(False)

        if not self.show_elastic_inelastic_temperature_intensity.isChecked():
            self.temperature_line_edit.setEnabled(False)
            self.angle_line_edit.setEnabled(False)

    def handle_inputs(self):
        """
        updates the inputs by filling them where needed
        """
        self.handle_inputs_visibility()
        if self.laser_intensity_error_mu_line_edit.text() != "":
            self.inputs['laser_intensity_error_mu'] = float(self.laser_intensity_error_mu_line_edit.text())
        else:
            self.inputs['laser_intensity_error_mu'] = 0
            self.inputs_objects['laser_intensity_error_mu'].setText('0')

        if self.laser_intensity_error_sigma_line_edit.text() != "":
            self.inputs['laser_intensity_error_sigma'] = float(self.laser_intensity_error_sigma_line_edit.text())
        else:
            self.inputs['laser_intensity_error_sigma'] = 0
            self.inputs_objects['laser_intensity_error_sigma'].setText('0')
        if self.laser_intensity_error_uniform_line_edit.text() != "":
            self.inputs['laser_intensity_error_uniform'] = float(self.laser_intensity_error_uniform_line_edit.text())
        else:
            self.inputs['laser_intensity_error_uniform'] = 0
            self.inputs_objects['laser_intensity_error_uniform'].setText('0')

        if self.laser_intensity_resolution_random_line_edit.text() != "":
            self.inputs['laser_intensity_error_random_resolution'] = float(
                self.laser_intensity_resolution_random_line_edit.text())
        else:
            self.inputs['laser_intensity_error_random_resolution'] = 0
            self.inputs_objects['laser_intensity_error_random_resolution'].setText('0')

        if self.rabi_frequency_line_edit.text() != "":
            self.inputs['rabi_frequency'] = float(self.rabi_frequency_line_edit.text())
            self.inputs['saturation_parameter'] = saturation_parameter_from_rabi_frequency(
                self.inputs['rabi_frequency'])
            self.saturation_parameter_line_edit.setPlaceholderText(str(self.inputs['saturation_parameter']))
            self.inputs['laser_intensity'] = self.inputs['saturation_parameter'] * self.inputs['saturation_intensity']
            self.laser_intensity_line_edit.setPlaceholderText(str(self.inputs['laser_intensity']))
            self.laser_intensity_line_edit.setText('')
        else:
            if self.saturation_parameter_line_edit.text() != "":
                self.inputs['saturation_parameter'] = float(self.saturation_parameter_line_edit.text())
                self.inputs['laser_intensity'] = self.inputs['saturation_parameter'] * self.inputs[
                    'saturation_intensity']
                self.laser_intensity_line_edit.setPlaceholderText(str(self.inputs['laser_intensity']))
                self.laser_intensity_line_edit.setText('')
            else:

                if self.laser_intensity_line_edit.text() != "":
                    self.inputs['laser_intensity'] = float(self.laser_intensity_line_edit.text())

                else:
                    self.inputs['saturation_intensity'] = float(self.saturation_i_line_edit.text())
                    if self.laser_power_line_edit.text() != "":
                        self.inputs['laser_power'] = float(self.laser_power_line_edit.text())
                    else:
                        raise ValueError("laser Power must be defined to calculate the laser Intensity")
                    if self.laser_waist_line_edit.text() != "":
                        self.inputs['laser_waist'] = float(self.laser_waist_line_edit.text())
                    else:
                        raise ValueError("laser waist must be defined to calculate the laser Intensity")
                    self.inputs['laser_intensity'] = laser_intensity_from_laser_waist_laser_power(
                        self.inputs["laser_waist"], self.inputs['laser_power'])
                    self.laser_intensity_line_edit.setPlaceholderText(str(self.inputs['laser_intensity']))

                self.inputs['saturation_parameter'] = saturation_parameter_from_laser_intensity(
                    self.inputs['laser_intensity'], self.inputs['saturation_intensity'])
                self.saturation_parameter_line_edit.setPlaceholderText(str(self.inputs['saturation_parameter']))
            self.inputs['rabi_frequency'] = rabi_frequency_from_saturation_parameter(
                self.inputs['saturation_parameter'])
            self.rabi_frequency_line_edit.setPlaceholderText(str(self.inputs['rabi_frequency']))

        if self.detuning_line_edit.text() != "":
            self.inputs['detuning'] = float(self.detuning_line_edit.text())
        else:
            raise ValueError("detuning must be defined to draw the graph")

        if self.show_elastic_inelastic_temperature_intensity.isChecked():
            if self.temperature_line_edit.text() == '':
                raise ValueError("Temperature must be defined to draw the full graph")
            self.inputs['temperature'] = float(self.temperature_line_edit.text())
            if self.angle_line_edit.text() == '':
                raise ValueError("angle must be defined to draw the full graph")
            self.inputs['angle'] = float(self.angle_line_edit.text())

    def update_graph(self):
        """
        updates the graphs
        :return:
        """
        # self.update_graph_span()
        # self.update_resolution()
        try:
            self.handle_inputs()
        except ValueError as e:
            self.error_popup(e)
            return

        if self.center_on_detuning_input.isChecked():
            NumbersGraph.offset = self.inputs['detuning']
        else:
            NumbersGraph.offset = 0
        self.graphs_to_update = []

        if self.show_elastic_inelastic_intensity.isChecked():
            self.graphs_to_update.append(self.graphs_number_objects[2])
        if self.convolution_kernel.isChecked():
            self.graphs_to_update.append(self.graphs_number_objects[4])
        if self.show_inelastic_intensity.isChecked():
            self.graphs_to_update.append(self.graphs_number_objects[0])
        if self.show_elastic_intensity.isChecked():
            self.graphs_to_update.append(self.graphs_number_objects[1])
        if self.show_elastic_inelastic_temperature_intensity.isChecked():
            self.graphs_to_update.append(self.graphs_number_objects[3])
        self.MplWidget.canvas.axes.clear()
        # grath styling
        self.MplWidget.canvas.axes.grid(color='#4f5b62', linestyle='--', linewidth=0.5)
        self.MplWidget.canvas.axes.set_title('Spectrum of light scattered by a quantum two-level system', fontsize=20,
                                             pad=20)
        self.MplWidget.canvas.axes.set_xlabel('$(ω - ω_{at})/Γ$')
        self.MplWidget.canvas.axes.set_ylabel('Spectrum')
        self.MplWidget.canvas.axes.spines['right'].set_color('#232629')
        self.MplWidget.canvas.axes.spines['top'].set_color('#232629')

        # update graphs
        for graph in self.graphs_to_update:
            try:
                if self.inputs['laser_intensity_error_sigma'] != 0 or self.inputs['laser_intensity_error_mu'] != 0 or \
                        self.inputs['laser_intensity_error_uniform'] != 0:
                    graph.update_with_random(self.inputs)
                else:
                    graph.update(self.inputs)
                self.MplWidget.canvas.axes.plot(graph.x_values, graph.y_values, label=graph.name, color=graph.color)
            except IndexError as e:
                print(e)
            # self.MplWidget.canvas.axes.annotate("w_o", xy=(0, 0))

            self.MplWidget.canvas.axes.legend(loc='upper right')
        # offset
        if self.show_annotations_input.isChecked() and NumbersGraph.offset - NumbersGraph.span < self.inputs[
                'detuning'] < NumbersGraph.offset + NumbersGraph.span:
            self.MplWidget.canvas.axes.axvline(self.inputs['detuning'], ls='--',
                                               color=self.color_dict['primaryLightColor'])
            self.MplWidget.canvas.axes.text(self.inputs['detuning'], 0, r"$Δ/Γ$", fontsize=14,
                                            verticalalignment='top', horizontalalignment='center',
                                            bbox=dict(boxstyle='round',
                                                      facecolor=self.color_dict['secondaryLightColor'], alpha=1))
        self.generalised_rabi_frequency_label.setText('Generalised Rabi Frequency(Ω<sub>G</sub>/Γ) = ' + str(
            round(generalised_rabi_frequency(self.inputs['rabi_frequency'],
                                             self.inputs['detuning'],
                                             self.inputs['gamma']), 2)))

        # managing limits
        self.MplWidget.canvas.axes.set_ylim(bottom=0)
        offset = self.inputs['detuning'] if self.center_on_detuning_input.isChecked() else 0
        self.MplWidget.canvas.axes.set_xlim(
            [-NumbersGraph.span + offset, NumbersGraph.span + offset])
        self.MplWidget.canvas.draw()

    @staticmethod
    def error_popup(error):
        """
        is called when an error is raised
        :param error: error
        """
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("ERROR VALUE NOT DEFINED")
        msg.setText(" ".join(error.args))
        msg.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    THEME = 'dark_teal'
    apply_stylesheet(app, theme=f'themes/{THEME}.xml')
    font = app.font()

    # FACTOR on base size of the font
    FACTOR = 1.4
    font.setPointSize(int(8 * FACTOR))
    app.setFont(font)

    # get colors from THEME
    f = open(f'themes/{THEME}.xml', 'r')
    colors = BeautifulSoup(f, 'xml').find_all("color")
    f.close()
    colors_dict = {
        "primaryColor": colors[0].decode_contents(),
        "primaryLightColor": colors[1].decode_contents(),
        "secondaryColor": colors[2].decode_contents(),
        "secondaryLightColor": colors[3].decode_contents(),
        "secondaryDarkColor": colors[4].decode_contents(),
        "primaryTextColor": colors[5].decode_contents(),
        "secondaryTextColor": colors[6].decode_contents()
    }

    # mpl setup
    mpl.rc('axes', edgecolor=colors_dict['primaryLightColor'], facecolor=colors_dict['secondaryColor'], grid=True,
           labelcolor=colors_dict['primaryLightColor'])
    mpl.rc('xtick', color=colors_dict['primaryLightColor'])
    mpl.rc('ytick', color=colors_dict['primaryLightColor'])
    mpl.rc('figure', facecolor=colors_dict['secondaryColor'])
    mpl.rc('legend', facecolor=colors_dict['secondaryLightColor'])
    mpl.rc('text', color=colors_dict['secondaryTextColor'])
    FACTOR = 2
    SMALL_SIZE = 8 * FACTOR
    MEDIUM_SIZE = 10 * FACTOR
    BIGGER_SIZE = 12 * FACTOR

    mpl.rc('font', size=SMALL_SIZE)  # controls default text sizes
    mpl.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
    mpl.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    mpl.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    mpl.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
    mpl.rc('legend', fontsize=SMALL_SIZE / 1.3)  # legend fontsize
    mpl.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
    mpl.rcParams["figure.autolayout"] = True  # always fit to canvas resolution
    main_window = MainWindow(colors_dict)
    main_window.showMaximized()

    app.exec_()
