from typing import List
from scipy.optimize import curve_fit
import numpy as np

def _linear(x, a, b):
    return a*x + b

def _quadratic(x, a, b, c):
    return a*x**2 + b*x + c

def _cubic(x, a, b, c, d):
    return a*x**3 + b*x**2 + c*x + d

def _exponential(x, a, b, c):
    return a*np.exp(b*x) + c

def _logarithmic(x, a, b, c):
    return a*np.log(b*x) + c

def _sinusoidal(x, a, b, c, d):
    return a*np.sin(b*x + c) + d

def fit(fit_type: str, x_data: np.array, y_data: np.array) -> List[float]:
    fit_func = None
    match fit_type:
        case "Linear":
            fit_func = _linear
        case "Quadratic":
            fit_func = _quadratic
        case "Cubic":
            fit_func = _cubic
        case "Exponential":
            fit_func = _exponential
        case "Logarithmic":
            fit_func = _logarithmic
        case "Sinusoidal":
            fit_func = _sinusoidal
        case _:
            raise ValueError(f"Unrecognised fit type: {fit_type}")
    
    popt, pcov = curve_fit(fit_func, x_data, y_data)
    return popt

def get_fitted_data(x: np.array, fit_type: str, fit_params: List[float]) -> np.array:
    match fit_type:
        case "Linear":
            return _linear(x, *fit_params)
        case "Quadratic":
            return _quadratic(x, *fit_params)
        case "Cubic":
            return _cubic(x, *fit_params)
        case "Exponential":
            return _exponential(x, *fit_params)
        case "Logarithmic":
            return _logarithmic(x, *fit_params)
        case "Sinusoidal":
            return _sinusoidal(x, *fit_params)
        case _:
            raise ValueError(f"Unrecognised fit type: {fit_type}")
        