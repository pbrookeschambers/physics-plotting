from io import StringIO
from typing import List
import numpy as np
from dataclasses import dataclass
from constants import MarkerStyles, LineStyles
from text import parse_unit, process_fit, process_units


@dataclass
class Color:
    auto_color: bool
    color: str
    opacity: float = 1

    def to_dict(self):
        return {
            "auto_color": self.auto_color,
            "color": self.color,
            "opacity": self.opacity,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            auto_color=d["auto_color"],
            color=d["color"],
            opacity=d["opacity"],
        )

    def __getitem__(self, key):
        return getattr(self, key)

    @classmethod
    def default(cls, white=False):
        return cls(
            auto_color=True,
            color="#ffffff" if white else "#000000",
            opacity=1,
        )


@dataclass
class Marker:
    style: MarkerStyles
    color: Color
    size: float

    def to_dict(self):
        return {
            "style": self.style.name,
            "color": self.color.to_dict(),
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            style=getattr(MarkerStyles, d["style"]),
            color=Color.from_dict(d["color"]),
            size=d["size"],
        )

    # allow marker["style"] etc
    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class Line:
    style: LineStyles
    color: Color
    width: float

    def to_dict(self):
        return {
            "style": self.style.name,
            "color": self.color.to_dict(),
            "width": self.width,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            style=getattr(LineStyles, d["style"]),
            color=Color.from_dict(d["color"]),
            width=d["width"],
        )

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class LegendEntry:
    show: bool
    label: str
    attempt_render: bool = True

    def to_dict(self):
        return {
            "show": self.show,
            "label": self.label,
            "attempt_render": self.attempt_render,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            label=d["label"],
            attempt_render=d["attempt_render"],
        )

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class LineOfBestFit:
    show: bool
    line: Line
    fit_type: str
    fit_params: List[float]
    legend_entry: LegendEntry
    r_squared: float
    attempt_plot: bool = True

    def to_dict(self):
        return {
            "show": self.show,
            "line": self.line.to_dict(),
            "fit_type": self.fit_type,
            "fit_params": self.fit_params.tolist()
            if isinstance(self.fit_params, np.ndarray)
            else self.fit_params,
            "legend_entry": self.legend_entry.to_dict(),
            "r_squared": float(self.r_squared),
            "attempt_plot": self.attempt_plot,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            line=Line.from_dict(d["line"]),
            fit_type=d["fit_type"],
            fit_params=d["fit_params"],
            legend_entry=LegendEntry.from_dict(d["legend_entry"]),
            r_squared=d["r_squared"],
            attempt_plot=d["attempt_plot"],
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def to_plot_code(
        self, x_data_name: str = "x_data", y_data_name: str = "y_data"
    ) -> str:
        # return the code necessary to plot this line of best fit
        data_code = StringIO()
        # assume that the data is already available in the namespace
        match self.fit_type:
            case "Linear":
                fit_func = "a*x + b"
                fit_params = ["a", "b"]
            case "Quadratic":
                fit_func = "a*x**2 + b*x + c"
                fit_params = ["a", "b", "c"]
            case "Cubic":
                fit_func = "a*x**3 + b*x**2 + c*x + d"
                fit_params = ["a", "b", "c", "d"]
            case "Exponential":
                fit_func = "a*np.exp(b*x) + c"
                fit_params = ["a", "b", "c"]
            case "Logarithmic":
                fit_func = "a*np.log(b*x) + c"
                fit_params = ["a", "b", "c"]
            case "Sinusoidal":
                fit_func = "a*np.sin(b*x + c) + d"
                fit_params = ["a", "b", "c", "d"]
            case _:
                raise ValueError(f"Unrecognised fit type: {self.fit_type}")
        fit_func_string = f"""def fit_func(x, {", ".join(fit_params)}):
    return {fit_func}"""
        data_code.write(
            f"""# Define the fitting function
{fit_func_string}
# Fit the data
fit_params, pcov = curve_fit(fit_func, {x_data_name}, {y_data_name})
# Take a sensible number of sample points (100, or the number of data points if that's larger)
num_points = max(100, len({x_data_name}))
# Calculate the fit line
x_fit = np.linspace(min({x_data_name}), max({x_data_name}), num_points)
y_fit = fit_func(x_fit, *fit_params)
"""
        )
        plot_opts = {}
        if self.line.style != LineStyles.NONE:
            plot_opts["linestyle"] = self.line.style.value
            plot_opts["linewidth"] = self.line.width
            if not self.line.color.auto_color:
                plot_opts["color"] = self.line.color.color
        alpha = self.line.color.opacity
        if alpha != 1:
            plot_opts["alpha"] = alpha
        if self.legend_entry.show:
            label = process_fit(
                process_units(self.legend_entry.label),
                self.fit_params,
                return_preprocessed=True,
            )
            data_code.write(
                f"""# Prepare the legend entry
{", ".join([chr(ord("a") + i) for i in range(len(fit_params))])} = fit_params
fit_label = f{repr(label)}
"""
            )
            plot_opts["label"] = "fit_label"
        # if there's no plot options, don't include them
        data_code.write("# Plot the fit line\n")
        if plot_opts:
            plot_opts_string = ", ".join(
                [
                    f"{k} = {v}" if k == "label" else f"{k} = {repr(v)}"
                    for k, v in plot_opts.items()
                ]
            )
            data_code.write(f"plt.plot(x_fit, y_fit, {plot_opts_string})")
        else:
            data_code.write(f"plt.plot(x_fit, y_fit)")
        return data_code.getvalue()

    def to_plot_json(self) -> dict:
        line_of_best_fit = {}
        line_of_best_fit["fit_type"] = self.fit_type
        line_of_best_fit["fit_params"] = (
            self.fit_params.tolist()
            if isinstance(self.fit_params, np.ndarray)
            else self.fit_params,
        )
        plot_opts = {}
        if self.line.style != LineStyles.NONE:
            plot_opts["linestyle"] = self.line.style.value
            plot_opts["linewidth"] = self.line.width
            if not self.line.color.auto_color:
                plot_opts["color"] = self.line.color.color
        else:
            plot_opts["linestyle"] = "none"
        alpha = self.line.color.opacity
        if alpha != 1:
            plot_opts["alpha"] = alpha
        if self.legend_entry.show:
            label = process_fit(
                process_units(self.legend_entry.label),
                self.fit_params,
                return_preprocessed=True,
            )
            plot_opts["label"] = label
        line_of_best_fit["plot_opts"] = plot_opts
        return line_of_best_fit


@dataclass
class DataSeries:
    name: str
    x: np.array
    y: np.array
    marker: Marker
    line: Line
    legend_entry: LegendEntry
    line_of_best_fit: LineOfBestFit
    attempt_plot: bool = True
    x_original: np.array = None
    y_original: np.array = None

    def __post_init__(self):
        if self.x_original is None:
            self.x_original = self.x.copy()
        if self.y_original is None:
            self.y_original = self.y.copy()

    @property
    def data(self):
        return np.array([self.x, self.y]).T

    def to_dict(self):
        return {
            "name": self.name,
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "marker": self.marker.to_dict(),
            "line": self.line.to_dict(),
            "legend_entry": self.legend_entry.to_dict(),
            "line_of_best_fit": self.line_of_best_fit.to_dict(),
            "attempt_plot": self.attempt_plot,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d["name"],
            x=np.array(d["x"]),
            y=np.array(d["y"]),
            marker=Marker.from_dict(d["marker"]),
            line=Line.from_dict(d["line"]),
            legend_entry=LegendEntry.from_dict(d["legend_entry"]),
            line_of_best_fit=LineOfBestFit.from_dict(d["line_of_best_fit"]),
            attempt_plot=d["attempt_plot"],
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def to_plot_code(
        self, x_data_name: str = "x_data", y_data_name: str = "y_data"
    ) -> str:
        # return the code necessary to plot this data series
        data_code = StringIO()
        # assume that the data is already available in the namespace
        plot_opts = {}
        if self.marker.style != MarkerStyles.NONE:
            plot_opts["marker"] = self.marker.style.value
            plot_opts["markersize"] = self.marker.size
            if not self.marker.color.auto_color:
                plot_opts["markerfacecolor"] = self.marker.color.color
                plot_opts["markeredgecolor"] = self.marker.color.color
        if self.line.style != LineStyles.NONE:
            plot_opts["linestyle"] = self.line.style.value
            plot_opts["linewidth"] = self.line.width
            if not self.line.color.auto_color:
                plot_opts["color"] = self.line.color.color
        else:
            plot_opts["linestyle"] = "none"
        alpha = max(self.marker.color.opacity, self.line.color.opacity)
        if alpha != 1:
            plot_opts["alpha"] = alpha
        if self.legend_entry.show:
            plot_opts["label"] = process_units(self.legend_entry.label)
        # if there's no plot options, don't include them
        if plot_opts:
            plot_opts_string = ", ".join(
                [f"{k}={repr(v)}" for k, v in plot_opts.items()]
            )
            data_code.write(
                f"plt.plot({x_data_name}, {y_data_name}, {plot_opts_string})"
            )
        else:
            data_code.write(f"plt.plot({x_data_name}, {y_data_name})")
        data_code.write("\n")
        if self.line_of_best_fit.show:
            data_code.write(
                self.line_of_best_fit.to_plot_code(x_data_name, y_data_name)
            )
        return data_code.getvalue()

    def to_plot_json(self) -> dict:
        # return the dict with properties that would be passed to the appropriate matplotlib functions.
        series = {}
        series["x_data"] = self.x.tolist()
        series["y_data"] = self.y.tolist()
        plot_opts = {}
        if self.marker.style != MarkerStyles.NONE:
            plot_opts["marker"] = self.marker.style.value
            plot_opts["markersize"] = self.marker.size
            if not self.marker.color.auto_color:
                plot_opts["markerfacecolor"] = self.marker.color.color
                plot_opts["markeredgecolor"] = self.marker.color.color
        if self.line.style != LineStyles.NONE:
            plot_opts["linestyle"] = self.line.style.value
            plot_opts["linewidth"] = self.line.width
            if not self.line.color.auto_color:
                plot_opts["color"] = self.line.color.color
        else:
            plot_opts["linestyle"] = "none"
        alpha = max(self.marker.color.opacity, self.line.color.opacity)
        if alpha != 1:
            plot_opts["alpha"] = alpha
        if self.legend_entry.show:
            plot_opts["label"] = process_units(self.legend_entry.label)
        series["plot_opts"] = plot_opts
        if self.line_of_best_fit.show:
            series["line_of_best_fit"] = self.line_of_best_fit.to_plot_json()
        return series

    def to_csv(self) -> str:
        # return the x and y data as a csv string
        csv = StringIO()
        for x, y in zip(self.x, self.y):
            csv.write(f"{x}, {y}\n")
        return csv.getvalue()

    def reset_data(self):
        self.x = self.x_original.copy()
        self.y = self.y_original.copy()


@dataclass
class AxisProperties:
    min: float | None
    max: float | None
    label: str
    font_size: int
    attempt_render: bool = True

    def to_dict(self):
        return {
            "min": self.min,
            "max": self.max,
            "label": self.label,
            "font_size": self.font_size,
            "attempt_render": self.attempt_render,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            min=d["min"],
            max=d["max"],
            label=d["label"],
            font_size=d["font_size"],
            attempt_render=d["attempt_render"],
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def to_plot_code(self, axis: str) -> str:
        axis = axis.lower()
        if not axis in ["x", "y"]:
            raise ValueError(f"Invalid axis: {axis}")

        code = StringIO()
        if self.min is not None or self.max is not None:
            code.write(f"ax.set_{axis}lim({self.min}, {self.max})\n")
        if self.label is not None:
            code.write(
                f"ax.set_{axis}label({repr(process_units(self.label))}, fontsize={int(self.font_size)})\n"
            )
        return code.getvalue()


@dataclass
class TitleProperties:
    text: str
    font_size: int
    attempt_render: bool = True

    def to_dict(self):
        return {
            "text": self.text,
            "font_size": self.font_size,
            "attempt_render": self.attempt_render,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            text=d["text"],
            font_size=d["font_size"],
            attempt_render=d["attempt_render"],
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def to_plot_code(self):
        if len(self.text.strip()) == 0:
            return ""
        return f"ax.set_title({repr(process_units(self.text))}, fontsize={int(self.font_size)})\n"


@dataclass
class LegendProperties:
    show: bool
    position: str
    font_size: float
    background_color: Color

    def to_dict(self):
        return {
            "show": self.show,
            "position": self.position,
            "font_size": self.font_size,
            "background_color": self.background_color.to_dict(),
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            position=d["position"],
            font_size=d["font_size"],
            background_color=Color.from_dict(d["background_color"]),
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def to_plot_code(self) -> str:
        if not self.show:
            return ""
        code = StringIO()
        opts = {}
        opts["fontsize"] = int(self.font_size)
        if not self.background_color.auto_color:
            opts["facecolor"] = self.background_color.color
            opts["framealpha"] = self.background_color.opacity
        if self.position != "Best":
            opts["loc"] = self.position.lower()
        code.write(
            f"ax.legend({', '.join([f'{k} = {repr(v)}' for k, v in opts.items()])})\n"
        )
        return code.getvalue()


@dataclass
class FigureProperties:
    x_axis: AxisProperties
    y_axis: AxisProperties
    title: TitleProperties
    legend: LegendProperties
    filename: str
    file_type: str
    theme: str

    def to_dict(self):
        return {
            "x_axis": self.x_axis.to_dict(),
            "y_axis": self.y_axis.to_dict(),
            "title": self.title.to_dict(),
            "legend": self.legend.to_dict(),
            "filename": self.filename,
            "file_type": self.file_type,
            "theme": self.theme,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            x_axis=AxisProperties.from_dict(d["x_axis"]),
            y_axis=AxisProperties.from_dict(d["y_axis"]),
            title=TitleProperties.from_dict(d["title"]),
            legend=LegendProperties.from_dict(d["legend"]),
            filename=d["filename"],
            file_type=d["file_type"],
            theme=d["theme"],
        )

    @classmethod
    def default(cls):
        x_axis = AxisProperties(None, None, "$x$", 14)
        y_axis = AxisProperties(None, None, "$y$", 14)
        title = TitleProperties("Title", 16)
        legend = LegendProperties(True, "Best", 14, Color.default(white=True))
        filename = "figure"
        file_type = "pdf"
        return cls(
            x_axis=x_axis,
            y_axis=y_axis,
            title=title,
            legend=legend,
            filename=filename,
            file_type=file_type,
            theme="Newcastle",
        )

    def __getitem__(self, key):
        return getattr(self, key)

    def is_default(self) -> bool:
        return self == FigureProperties.default()

    def to_plot_code(self) -> str:
        code = StringIO()
        code.write(f"# Set the axis labels\n")
        code.write(self.x_axis.to_plot_code("x"))
        code.write(self.y_axis.to_plot_code("y"))
        if len(self.title.text.strip()) > 0:
            code.write(f"# Set the title\n")
        code.write(self.title.to_plot_code())
        code.write(f"# Add the legend\n")
        code.write(self.legend.to_plot_code())
        code.write(f"# Save the figure\n")
        if self.file_type.lower() == "png":
            code.write(
                f'plt.savefig("{self.filename}.{self.file_type.lower()}", dpi = 300, bbox_inches = "tight")\n'
            )
        else:
            code.write(
                f'plt.savefig("{self.filename}.{self.file_type.lower()}", bbox_inches = "tight")\n'
            )
        return code.getvalue()


def indent(string: str, indent_by: int, absolute_indent: False, indent_width: int = 4):
    lines = string.split("\n")
    full_indent = " " * indent_width * indent_by
    if not absolute_indent:
        lines = [full_indent + line for line in lines]
        return "\n".join(lines)

    # otherwise, we need to find the minimum indent
    min_indent = 1000
    for line in lines:
        if line.strip():
            min_indent = min(min_indent, len(line) - len(line.lstrip()))
    lines = [full_indent + line[min_indent:] for line in lines]
