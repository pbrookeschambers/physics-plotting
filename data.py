from typing import List
import numpy as np
from dataclasses import dataclass
from constants import MarkerStyles, LineStyles

@dataclass
class Marker:
    style: MarkerStyles
    color: str
    size: float
    auto_color: bool = True

    def to_dict(self):
        return {
            "style": self.style.name,
            "color": self.color,
            "size": self.size,
            "auto_color": self.auto_color,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            style=getattr(MarkerStyles, d["style"]),
            color=d["color"],
            size=d["size"],
            auto_color=d["auto_color"],
        )

@dataclass
class Line:
    style: LineStyles
    color: str
    width: float
    auto_color: bool = True

    def to_dict(self):
        return {
            "style": self.style.name,
            "color": self.color,
            "width": self.width,
            "auto_color": self.auto_color,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            style=getattr(LineStyles, d["style"]),
            color=d["color"],
            width=d["width"],
            auto_color=d["auto_color"],
        )
    
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

@dataclass
class LineOfBestFit:
    show: bool
    line: Line
    fit_type: str
    fit_params: List[float]
    legend_entry: LegendEntry
    auto_color: bool = True
    attempt_plot: bool = True

    def to_dict(self):
        return {
            "show": self.show,
            "line": self.line.to_dict(),
            "fit_type": self.fit_type,
            "fit_params": self.fit_params.tolist() if isinstance(self.fit_params, np.ndarray) else self.fit_params,
            "auto_color": self.auto_color,
            "legend_entry": self.legend_entry.to_dict(),
            "attempt_plot": self.attempt_plot,
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            line=Line.from_dict(d["line"]),
            fit_type=d["fit_type"],
            fit_params=d["fit_params"],
            auto_color=d["auto_color"],
            legend_entry=LegendEntry.from_dict(d["legend_entry"]),
            attempt_plot=d["attempt_plot"],
        )

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

@dataclass
class LegendProperties:
    show: bool
    position: str
    font_size: float
    background_color: str
    opacity: float
    auto_color: bool = True

    def to_dict(self):
        return {
            "show": self.show,
            "position": self.position,
            "font_size": self.font_size,
            "background_color": self.background_color,
            "opacity": self.opacity,
            "auto_color": self.auto_color,
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            position=d["position"],
            font_size=d["font_size"],
            background_color=d["background_color"],
            opacity=d["opacity"],
            auto_color=d["auto_color"],
        )


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
        x_axis = AxisProperties(
            None,
            None,
            "$x$",
            14
        )
        y_axis = AxisProperties(
            None,
            None,
            "$y$",
            14
        )
        title = TitleProperties(
            "Title",
            16
        )
        legend = LegendProperties(
            True,
            "Best",
            14,
            "#ffffff",
            1.0,
        )
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
