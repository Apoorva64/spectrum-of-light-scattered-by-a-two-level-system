from typing import Dict, Any, Union, List
from scipy import signal
from scipy import integrate
import random
from modules.functions import *


class NumbersGraph:
    """base class for all graphs_to_update."""
    # Resolution of the graph
    resolution: int = 2000
    # offset of the graph mainly used to center on detuning or to center on 0
    offset: float = 0.0
    # span of the graph
    span: float = 10.0
    # on-resonance saturation parameter
    saturation_parameter: float = 1.0
    # laser frequency-atom frequency
    detuning: float = 0.0
    gamma: float = 1.0  # scalar
    angle: float = 90.0  #
    temperature: float = 100.0
    saturation_intensity: float = 1.669
    laser_intensity_error_mu: float = 0.0
    laser_intensity_error_sigma: float = 0.0
    laser_intensity_error_uniform: float = 0.0

    graph_end: float
    graph_start: float
    graph_step: float
    y_values: List[float] or np.ndarray  # list of float
    x_values: List[float] or np.ndarray  # list of float

    def __init__(self):
        """
        init method

        :attr x_values: list of values for the x axis
        :attr y_values: list of values for the y axis
        :attr graph_step: step of the graph(space between 2 numbers on the x axis)
        :attr graph_start: start of the graph
        :attr graph_end: end of the graph
        """
        self.x_values = []
        self.y_values = []
        # define how the graph is created
        self.graph_step = (self.span * 2) / self.resolution
        self.graph_start = self.offset - self.span
        self.graph_end = self.offset + self.span
        self.color = 'white'

    def update_inputs(self, inputs: Dict[Union[str, Any], Union[Union[str, float, int], Any]]) -> None:
        """
        this method updates the attributes of the current instance
        :param inputs: update dictionary for the attributes of the current instance
        """
        self.__dict__.update(inputs)

    def update(self, inputs, intensity_error=0.0):
        """
        base update for the graph
        :param intensity_error:
        :param inputs: update dictionary for the attributes of the current instance
        """
        self.update_inputs(inputs)

        # calculate the graph size and step
        self.graph_step = (self.span * 2) / self.resolution
        self.graph_start = self.offset - self.span
        self.graph_end = self.offset + self.span

        # clearing lists
        self.x_values = []
        self.y_values = []

        # fill the x values of the graph
        # noinspection PyTypeChecker
        self.x_values = np.arange(self.graph_start, self.graph_end, self.graph_step).tolist()

        # adding values for 0 and detuning
        self.add_point_x(0)
        self.add_point_x(self.detuning)

    def add_point_x(self, point_x):
        """adds a point to the x axis"""
        try:
            self.x_values.index(point_x)
        except ValueError:
            self.x_values.append(point_x)
            self.x_values.sort()

    def update_with_random(self, inputs):
        n = inputs['laser_intensity_error_random_resolution']
        self.update_inputs(inputs)

        y_values_with_random = []
        for loop in range(int(n)):
            intensity_error = random.normalvariate(self.laser_intensity_error_mu,
                                                   self.laser_intensity_error_sigma) + random.uniform(
                -self.laser_intensity_error_uniform, self.laser_intensity_error_uniform)
            self.update(inputs,
                        intensity_error=intensity_error)
            # print(intensity_error)
            y_values_with_random.append(self.y_values.copy())
        arr = np.array(y_values_with_random)

        self.y_values = np.sum(arr, axis=0) / n
        self.y_values = np.abs(self.y_values)


class InelasticIntensity(NumbersGraph):
    def __init__(self):
        super().__init__()
        self.name = "Inelastic Intensity"
        self.color = 'pink'

    def update(self, inputs, intensity_error=0.0):
        """
        Calculates the y values of the graph
        :param intensity_error:
        :param intensity_error:
        :param inputs: update dictionary for the attributes of the current instance
        """
        NumbersGraph.update(self, inputs)

        self.y_values = [
            inelastic_intensity(x, self.saturation_parameter, self.detuning, self.gamma, self.saturation_intensity,
                                intensity_error)
            for x in self.x_values]

    def find_border(self, inputs):
        """
        finds the span for the function
        :param inputs: update dictionary for the attributes of the current instance
        :return: span
        """
        running = True
        custom_input = inputs.copy()
        custom_input['span'] = 0
        custom_input['resolution'] = 200
        while running:
            custom_input['span'] += 1
            self.update(custom_input)
            max_y = max(self.y_values)
            exponent = int("{:e}".format(max_y).split("e-")[1])
            abs_tolerance = float(f'0.{"0" * exponent}01')
            for y in self.y_values:
                if math.isclose(y, 0, abs_tol=abs_tolerance):
                    running = False
        return custom_input['span']


class ElasticIntensity(NumbersGraph):
    def __init__(self):
        super().__init__()
        self.name = "Elastic Intensity"
        self.value = 0
        self.color = 'red'

    def update(self, inputs, intensity_error=0.0):
        """
        Calculates the y values of the graph
        :param intensity_error:
        :param inputs: update dictionary for the attributes of the current instance
        """
        NumbersGraph.update(self, inputs)
        self.y_values = [0] * len(self.x_values)
        self.value = elastic_intensity(self.saturation_parameter, self.detuning, self.gamma, self.saturation_intensity,
                                       intensity_error)
        try:
            self.y_values[self.x_values.index(self.detuning)] = self.value

        except ValueError:
            for i, x in enumerate(self.x_values):
                if self.detuning - self.graph_step < x < self.detuning + self.graph_step:
                    self.y_values[i] = self.value
                    break


class Intensity(NumbersGraph):
    """Class for the intensity spectrum: intensity=elastic_intensity+inelastic_intensity"""

    def __init__(self):
        super().__init__()
        self.name = "Inelastic Intensity + Elastic Intensity"
        self.elastic_graph = ElasticIntensity()
        self.inelastic_graph = InelasticIntensity()
        self.color = "yellow"

    def update(self, inputs, intensity_error=0.0):
        """
        Calculates the y values of the graph
        :param intensity_error:
        :param inputs: update dictionary for the attributes of the current instance
        """
        NumbersGraph.update(self, inputs)

        self.elastic_graph.update(inputs, intensity_error=intensity_error)
        self.inelastic_graph.update(inputs, intensity_error=intensity_error)
        self.y_values = np.array(self.elastic_graph.y_values) + np.array(self.inelastic_graph.y_values)


class DopplerBroadenedSpectrum(NumbersGraph):
    def __init__(self):
        super().__init__()
        self.name = 'Doppler Broadened Spectrum'

    def update(self, inputs, intensity_error=0.0):
        """
        Calculates the y values of the graph
        :param intensity_error:
        :param inputs: update dictionary for the attributes of the current instance
        """
        NumbersGraph.update(self, inputs)
        for x in self.x_values:
            y = doppler_broadened_spectrum(x, self.detuning, self.temperature * (10 ** -6), math.radians(self.angle))
            # if y != 0:
            self.y_values.append(y)

    def find_resolution(self, inputs):
        """
        finds the resolution of the graph (deprecated)
        :param inputs: update dictionary for the attributes of the current instance
        """
        span = 0
        running = True
        while running:
            span += 2
            self.update(inputs)
            for y in self.y_values:
                if math.isclose(y, 0, abs_tol=0.00001):
                    running = False
        resolution = 4000
        # self.resolution=10
        # print(span)
        self.y_values = []

        while len(self.y_values) - sum(math.isclose(0, y, abs_tol=0.0001) for y in self.y_values) < 2700:
            # print(len(self.y_values))
            resolution *= 2
            self.update(inputs)
            # print(resolution)

        # print(resolution, len(self.y_values) - self.y_values.count(0))
        return resolution


class ElasticInelasticTemperatureIntensity(NumbersGraph):
    def __init__(self):
        super().__init__()
        self.name = 'Inelastic Intensity + Elastic Intensity + Temperature'
        self.doppler_broadened_spectrum = DopplerBroadenedSpectrum()
        self.elastic_inelastic_intensity = InelasticIntensity()
        self.elastic_graph = ElasticIntensity()
        self.color = 'green'

    def update(self, inputs, intensity_error=0.0):
        """
        Calculates the y values of the graph
        :param intensity_error:
        :param inputs: update dictionary for the attributes of the current instance
        """
        new_inputs = inputs.copy()
        new_inputs['offset'] = inputs['detuning']

        # new_inputs['resolution'] = self.doppler_broadened_spectrum.find_resolution(inputs, offset=inputs['detuning'])
        new_inputs['resolution'] = 20000
        new_inputs['span'] = self.elastic_inelastic_intensity.find_border(new_inputs) * 1.4

        NumbersGraph.update(self, new_inputs)

        self.elastic_graph.update(new_inputs)
        self.elastic_inelastic_intensity.update(new_inputs)
        self.doppler_broadened_spectrum.update(new_inputs)
        # Inelastic Intensity Convolution
        self.y_values = signal.convolve(
            np.array(self.elastic_inelastic_intensity.y_values),
            self.doppler_broadened_spectrum.y_values,
            mode='same', method='fft')
        # normalization
        self.y_values /= integrate.simpson(self.y_values, self.x_values)
        self.y_values *= sum(self.elastic_inelastic_intensity.y_values) / sum(self.y_values)

        # adding the convolution of the dirac as the convolution is bilinear
        convolution_dirac = np.array(self.doppler_broadened_spectrum.y_values) * (
                self.elastic_graph.value * self.graph_step / integrate.simpson(self.doppler_broadened_spectrum.y_values,
                                                                               self.x_values))

        self.y_values += convolution_dirac

    def update_with_random(self, inputs):
        """
        Calculates the y values of the graph
        :param inputs: update dictionary for the attributes of the current instance
        """
        new_inputs = inputs.copy()
        new_inputs['offset'] = inputs['detuning']

        # new_inputs['resolution'] = self.doppler_broadened_spectrum.find_resolution(inputs, offset=inputs['detuning'])
        new_inputs['resolution'] = 20000
        new_inputs['span'] = self.elastic_inelastic_intensity.find_border(new_inputs) * 1

        NumbersGraph.update(self, new_inputs)

        self.elastic_graph.update_with_random(new_inputs)
        self.elastic_inelastic_intensity.update_with_random(new_inputs)
        self.doppler_broadened_spectrum.update(new_inputs)
        # Inelastic Intensity Convolution
        self.y_values = signal.convolve(
            np.array(self.elastic_inelastic_intensity.y_values),
            self.doppler_broadened_spectrum.y_values,
            mode='same', method='fft')
        # normalization
        self.y_values /= integrate.simpson(self.y_values, self.x_values)
        self.y_values *= sum(self.elastic_inelastic_intensity.y_values) / sum(self.y_values)

        # adding the convolution of the dirac as the convolution is bilinear
        convolution_dirac = np.array(self.doppler_broadened_spectrum.y_values) * (
                self.elastic_graph.value * self.graph_step / integrate.simpson(self.doppler_broadened_spectrum.y_values,
                                                                               self.x_values))

        self.y_values += convolution_dirac
