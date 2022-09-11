"""
main file for formulas
"""
import math
# import random
import numpy as np

# Constants
_lambda = 780 * (10 ** -9)  # laser frequency in nm
k = 2 * math.pi / _lambda  # wave vector
kB = 1.380649 * (10 ** -23)  # Boltzmann constant in J⋅K−1
M = 1.409993199 * (10 ** -25)  # Rubidium mass in  kg


def saturation_parameter_variable(saturation_parameter, detuning, gamma):
    """
    calculates the variable saturation parameter
    :param saturation_parameter: saturation_parameter at laser frequency
    :param detuning: laser detuning
    :param gamma: 1
    :return: saturation_parameter_variable
    """
    numerator = saturation_parameter
    denominator = 1 + 4 * ((detuning / gamma) ** 2)
    return numerator / denominator


def laser_intensity_from_laser_waist_laser_power(laser_waist: float, laser_power: float) -> float:
    """
    calculates the laser intensity from the laser power and the laser waist
    :param laser_waist: diameter of the laser
    :param laser_power: power of the laser
    :return: laser intensity
    """
    try:
        return (2 * laser_power) / (math.pi * laser_waist ** 2)
    except ValueError:
        return 0


def saturation_parameter_from_laser_intensity(laser_intensity: float, saturation_intensity: float) -> float:
    """
    calculates the saturation parameter from the laser intensity and the saturation intensity
    :param laser_intensity: intensity of the laser
    :param saturation_intensity: saturation intensity of the laser
    :return: saturation parameter
    """
    return laser_intensity / saturation_intensity


def saturation_parameter_from_rabi_frequency(rabi_frequency: float) -> float:
    """
    calculates the saturation parameter from the rabi frequency
    :param rabi_frequency: rabi frequency
    :return: saturation parameter
    """
    return (rabi_frequency ** 2) * 2


def rabi_frequency_from_saturation_parameter(saturation_parameter: float) -> float:
    """
    calculates the rabi frequency from the saturation parameter
    :param saturation_parameter: saturation_parameter
    :return: rabi frequency
    """
    return math.sqrt(saturation_parameter / 2)


def generalised_rabi_frequency(rabi_frequency: float, detuning: float, gamma: float) -> float:
    """
    calculates the generalised rabi frequency
    :param rabi_frequency:
    :param detuning:
    :param gamma:
    :return: generalised rabi frequency
    """
    return math.sqrt((rabi_frequency / gamma) ** 2 + detuning ** 2)


def doppler_width(temperature: float, angle_radians: float) -> float:
    """
    Calculates the doppler width
    :param temperature: temperature in kelvin
    :param angle_radians: angle in radians
    :return: doppler width
    """
    x = k * math.sqrt(2 * (1 - math.cos(angle_radians)) * kB * (temperature / M))
    x /= (2 * math.pi * 6.07 * (10 ** 6))
    return x


def doppler_broadened_spectrum(w: float, laser_frequency: float, temperature: float, angle_radians: float) -> float:
    """

    :param w: frequency of the atom(variable)
    :param laser_frequency: frequency of the laser
    :param temperature: temperature in kelvin
    :param angle_radians: angle in radians
    :return: doppler broadened spectrum for a certain w
    """
    try:
        return np.exp((-1 * (laser_frequency - w) ** 2) / (
                2 * doppler_width(temperature, angle_radians) ** 2))
    except ZeroDivisionError:
        return 0


def elastic_intensity(saturation_parameter, detuning, gamma, saturation_intensity, intensity_error):
    """
    Calculates the elastic_intensity
    :param saturation_intensity: saturation intensity of the laser
    :param intensity_error: intensity_error
    :param saturation_parameter: saturation_parameter
    :param detuning: detuning
    :param gamma: is at 1
    :return: elastic_intensity
    """
    # applying random distribution on the laser intensity
    laser_intensity = saturation_parameter * saturation_intensity
    laser_intensity += intensity_error
    saturation_parameter = saturation_parameter_from_laser_intensity(laser_intensity, saturation_intensity)

    s = saturation_parameter_variable(saturation_parameter, detuning, gamma)
    value = s / (2 * ((1 + s) ** 2))
    return value


def inelastic_intensity(w, saturation_parameter, detuning, gamma, saturation_intensity, intensity_error):
    """
    Calculates the inelastic intensity for a certain w
    :param w: frequency of the atom(variable)
    :param saturation_parameter: saturation parameter
    :param detuning: detuning
    :param gamma: default at 1
    :param saturation_intensity: saturation intensity
    :param intensity_error: intensity error
    :return: inelastic intensity for a certain w
    """
    # applying random normal distribution on the laser intensity
    laser_intensity = saturation_parameter * saturation_intensity
    laser_intensity += intensity_error
    saturation_parameter = saturation_parameter_from_laser_intensity(laser_intensity, saturation_intensity)

    # calculating using thesis formula
    w_l = detuning
    d = w - w_l  # δ = ω − ωL.
    d_l = w_l
    g_b = gamma
    s = saturation_parameter
    n = 1
    d_l_g_b = (d_l / g_b) ** 2
    d_g_b = (d / g_b) ** 2
    first_part = n ** 2 * (1 / g_b)
    second_part = (s ** 2) / (8 * math.pi * (1 + s + 4 * d_l_g_b))

    numerator_big_part = d_g_b + (s / 4) + 1

    denominator_big_part1 = (1 / 4) + s / 4 + d_l_g_b - 2 * d_g_b

    denominator_big_part2 = (5 / 4) + (s / 2) + d_l_g_b - d_g_b

    big_part = numerator_big_part / (denominator_big_part1 ** 2 + d_g_b * denominator_big_part2 ** 2)
    result = first_part * second_part * big_part
    return result
